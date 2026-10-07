"""한 시나리오(세계)의 전체 평가 — 시뮬레이터 로그와 정답을 모두 써서 각 방법을 채점한다.

  1. 착시: 순진한 비교 / 회귀 / IPW / AIPW 가 정답 평균 효과를 얼마나 맞히는가 (+ 로그 감사 판정)
  2. 정책: 사이트·주마다 K 개 점검을 어떤 기준으로 고르면 "점검 100번당 막는 고장"이 얼마인가
     (정답 값과, 정답 없이 로그만으로 추정한 값 OPE 를 둘 다)
  3. 효과 추정 정확도(PEHE, 순위 상관), 위험 구간·종류별 정답 대 추정 프로필
  4. 데모용 점검표 예시

학습은 앞 구간(주 < train_weeks), 평가는 뒤 구간. 효과 모형은 평가 구간의 어떤 정보도 보지 못한다.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor

from ..audit import run_audit
from ..causal import estimators as est
from ..causal import nuisance as nu_mod
from ..causal import policy as pol
from ..causal.data import prepare
from ..causal.dragonnet import fit_dragonnet
from ..causal.responsiveness import ResponsivenessModel
from ..sim.generate import World, simulate
from ..sim.world import CATEGORIES, WorldConfig

CAT_KO = {c.key: c.ko for c in CATEGORIES}
POLICY_LABELS = {
    "random": "무작위",
    "round_robin": "라운드로빈 (가장 오래 안 본 순)",
    "risk": "위험순 (고장 예측 모형)",
    "risk_rule": "위험순 + 수리 접수 제외 규칙",
    "responsiveness": "효과순 (반응도 모형)",
    "responsiveness_rule": "효과순 + 수리 접수 제외 규칙",
    "dr_gbm": "효과순 (DR-learner, 트리)",
    "t_learner": "효과순 (T-learner)",
    "dragonnet": "효과순 (DragonNet, 신경망)",
    "ceiling": "상한: 관측 변수로 도달 가능한 효과순 (정답 라벨로 학습)",
    "oracle": "오라클: 숨은 손상까지 아는 효과순",
}


def _fit_effect_models(ftr, nuis_tr, gamma_tr, seed: int):
    """학습 구간만으로 모든 효과 점수 모형을 적합한다. 반환: 점수 함수 dict (입력: Frame 의 X, 그 행의 μ0)."""
    resp = ResponsivenessModel.fit(ftr, nuis_tr.mu0, gamma_tr, n_boot=60, seed=seed)
    models = nu_mod.fit_models(ftr.X, ftr.T, ftr.Y, seed=seed + 100)
    # 위험 점수(μ0 가 아닌, 처치를 무시한 고장 예측) — 기준선이자 DR-learner 입력
    risk = pol.fit_risk_model(ftr.X, ftr.Y, seed=seed)
    # 트리 DR-learner: 위험 점수를 입력에 더해 (깊이 2, 큰 잎) 강하게 규제
    from sklearn.model_selection import GroupKFold

    r_cf = np.zeros(len(ftr))
    for a, b in GroupKFold(5).split(ftr.X, ftr.T, ftr.asset):
        r_cf[b] = pol.fit_risk_model(ftr.X[a], ftr.Y[a], seed=seed).predict_proba(ftr.X[b])[:, 1]
    dr_reg = HistGradientBoostingRegressor(
        max_depth=2,
        learning_rate=0.05,
        max_iter=80,
        min_samples_leaf=800,
        l2_regularization=5.0,
        random_state=seed,
    ).fit(np.column_stack([ftr.X, r_cf]), gamma_tr)
    dn = fit_dragonnet(ftr.X, ftr.T, ftr.Y, ftr.asset, seed=seed)
    return {"resp": resp, "models": models, "risk": risk, "dr_reg": dr_reg, "dragon": dn}


def score_rows(fit: dict, X: np.ndarray, mu0_hint: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """점수 사전(클수록 우선). 모두 '막은 고장 확률' 부호 또는 위험 확률."""
    nu = nu_mod.predict_models(fit["models"], X)
    mu0 = nu.mu0 if mu0_hint is None else mu0_hint
    r = fit["risk"].predict_proba(X)[:, 1]
    out = {
        "risk": r,
        "responsiveness": fit["resp"].averted(X, mu0),
        "dr_gbm": -fit["dr_reg"].predict(np.column_stack([X, r])),
        "t_learner": nu.mu0 - nu.mu1,
        "dragonnet": fit["dragon"].averted(X),
    }
    return out, nu


def run_scenario(
    cfg: WorldConfig,
    name: str,
    title: str,
    out_dir: Path | None = None,
    truth_m: int = 64,
    k: int = 8,
    ks: tuple[int, ...] = (2, 4, 6, 8, 12, 16),
    train_weeks: int | None = None,
    seed: int = 0,
    world: World | None = None,
    verbose: bool = True,
) -> dict:
    t_all = time.time()

    def log(msg):
        if verbose:
            print(f"[{name}] {msg} ({time.time() - t_all:.0f}s)", flush=True)

    world = world or simulate(cfg, truth_m=truth_m)
    L, T = world.log, world.truth
    log(f"simulated rows={len(L):,}")
    fr = prepare(L)
    tau_all = T["tau"].to_numpy()[fr.idx]  # 정답: 막은 고장 확률
    p0_all = T["p0"].to_numpy()[fr.idx]
    truth_ate_effect = float(-tau_all.mean())
    att = float(tau_all[fr.T == 1].mean())

    # ------------------------------------------------------------ 1. 착시와 로그 감사
    audit = run_audit(L, truth_ate=truth_ate_effect, seed=seed)
    audit["truth"] = {
        "ate_averted": float(tau_all.mean()),
        "att_averted": att,
        "atc_averted": float(tau_all[fr.T == 0].mean()),
        "base_rate_p0": float(p0_all.mean()),
    }
    log(f"audit done: verdict={audit['verdict']['level']}")

    # ------------------------------------------------------------ 2. 학습/평가 분할
    tw = train_weeks or int(cfg.weeks * 2 / 3)
    tr, te = fr.week < tw, fr.week >= tw
    ftr, fte = fr.subset(tr), fr.subset(te)
    tau_te = tau_all[te]
    nuis_tr = nu_mod.crossfit(ftr.X, ftr.T, ftr.Y, ftr.asset, seed=seed)
    gamma_tr = est.dr_scores(ftr.T, ftr.Y, nuis_tr)
    fit = _fit_effect_models(ftr, nuis_tr, gamma_tr, seed)
    scores, nu_te = score_rows(fit, fte.X)
    gamma_te = est.dr_scores(fte.T, fte.Y, nu_te)  # 평가 구간 DR 점수(학습 구간 모형으로 계산 → 표본 밖)
    log("effect models fit")

    # 상한: 정답 라벨(τ)로 학습한 회귀 — 관측 변수만으로 효과 순위를 얼마나 맞힐 수 있나
    tau_tr = tau_all[tr]
    ceil = HistGradientBoostingRegressor(
        max_depth=5, learning_rate=0.06, max_iter=300, min_samples_leaf=60, random_state=seed
    ).fit(ftr.X, tau_tr)
    scores["ceiling"] = ceil.predict(fte.X)
    scores["oracle"] = tau_te
    rng = np.random.default_rng(seed)
    scores["random"] = rng.random(len(fte))
    scores["round_robin"] = fte.col("wsv") + 1e-6 * rng.random(len(fte))
    scores["risk_rule"] = np.where(fte.col("open_wo") == 1, -1.0, scores["risk"])
    scores["responsiveness_rule"] = np.where(fte.col("open_wo") == 1, -1.0, scores["responsiveness"])

    df = pd.DataFrame({"site": fte.site, "week": fte.week})
    values = {}
    for kk in ks:
        pv = pol.policy_values(df, scores, kk, tau_te, gamma_te)
        values[str(kk)] = pv
    # 기본 K 의 신뢰구간 (사이트·주 묶음 부트스트랩)
    cis = {}
    for nm, sc in scores.items():
        lo, hi = pol.bootstrap_policy_ci(df, sc, k, tau_te, n_boot=200, seed=seed)
        olo, ohi = pol.bootstrap_policy_ci(df, sc, k, -gamma_te, n_boot=200, seed=seed)
        cis[nm] = {"true_lo": lo, "true_hi": hi, "ope_lo": olo, "ope_hi": ohi}
    policy_block = {
        "k": k,
        "ks": list(ks),
        "test_weeks": [int(fte.week.min()), int(fte.week.max())],
        "n_groups": values[str(k)]["random"]["n_groups"],
        "labels": POLICY_LABELS,
        "by_k": values,
        "ci": cis,
    }
    log("policy values done")

    # ------------------------------------------------------------ 3. 효과 추정 정확도·프로필
    cate = {}
    for nm in ("responsiveness", "dr_gbm", "t_learner", "dragonnet", "ceiling", "risk"):
        s = scores[nm]
        entry = {"spearman": float(spearmanr(s, tau_te)[0])}
        if nm != "risk":
            entry["pehe"] = float(np.sqrt(np.mean((s - tau_te) ** 2)))
        cate[nm] = entry
    cate["constant_pehe"] = float(np.sqrt(np.mean((tau_te.mean() - tau_te) ** 2)))
    cate["dragonnet_meta"] = {
        "params": fit["dragon"].n_params,
        "epochs": fit["dragon"].epochs_run,
        "seconds": round(fit["dragon"].train_seconds, 1),
    }
    mu0_te = nu_te.mu0
    prof = pd.DataFrame(
        {
            "risk": scores["risk"],
            "mu0": mu0_te,
            "tau": tau_te,
            "est": scores["responsiveness"],
            "cat": [fte.names[int(np.argmax(r[:8]))][4:] for r in fte.X],
            "open_wo": fte.col("open_wo"),
            "T": fte.T.astype(float),
            "Y": fte.Y,
        }
    )
    prof["decile"] = pd.qcut(prof["risk"].rank(method="first"), 10, labels=False)
    agg = {
        "risk": ("risk", "mean"),
        "tau": ("tau", "mean"),
        "est": ("est", "mean"),
        "n": ("tau", "size"),
        "visit": ("T", "mean"),
        "y": ("Y", "mean"),
    }
    by_dec = prof.groupby("decile").agg(**agg).reset_index()
    by_cat = prof.groupby("cat").agg(**agg).reset_index()
    by_cat["ko"] = by_cat["cat"].map(CAT_KO)
    by_open = prof.groupby("open_wo").agg(**agg).reset_index()
    profile = {
        "by_risk_decile": by_dec.round(5).to_dict("records"),
        "by_category": by_cat.round(5).to_dict("records"),
        "by_open_wo": by_open.round(5).to_dict("records"),
        "multipliers": fit["resp"].multipliers(),
    }

    # 산점도: 평가 구간의 한 주(마지막 평가 주)에서 사이트 전체 설비 + 정책별 선택 여부
    last_wk = int(fte.week.max())
    m_last = fte.week == last_wk
    sc_df = pd.DataFrame(
        {
            "site": fte.site[m_last],
            "risk": scores["risk"][m_last],
            "est": scores["responsiveness"][m_last],
            "truth": tau_te[m_last],
            "open_wo": fte.col("open_wo")[m_last],
            "cat": [fte.names[int(np.argmax(r[:8]))][4:] for r in fte.X[m_last]],
        }
    )
    sc_df["sel_risk"] = False
    sc_df["sel_effect"] = False
    for _, grp in sc_df.groupby("site"):
        sc_df.loc[grp.nlargest(k, "risk").index, "sel_risk"] = True
        sc_df.loc[grp.nlargest(k, "est").index, "sel_effect"] = True
    scatter = {
        "week": last_wk,
        "k": k,
        "n": int(len(sc_df)),
        "points": sc_df.sample(min(900, len(sc_df)), random_state=seed)
        .round({"risk": 4, "est": 4, "truth": 4})
        .to_dict("records"),
    }

    # ------------------------------------------------------------ 4. 데모용 점검표 예시
    plans = _plans(fte, scores, nu_te, tau_te, fit, world, weeks=sorted(set(fte.week.tolist()))[-9::3])

    result = {
        "id": name,
        "title": title,
        "config": {
            k_: v
            for k_, v in cfg.describe().items()
            if k_
            in (
                "seed",
                "n_sites",
                "weeks",
                "hunch",
                "flat",
                "cliff",
                "th_cmp",
                "hazard_scale",
                "repair_eff",
                "horizon",
            )
        },
        "world": {
            "n_sites": int(cfg.n_sites),
            "n_assets": int(L["asset"].nunique()),
            "weeks": int(cfg.weeks),
            "rows": int(len(L)),
            "visit_rate": float(L["treated"].mean()),
            "train_weeks": tw,
        },
        "audit": audit,
        "policy": policy_block,
        "cate": cate,
        "profile": profile,
        "scatter": scatter,
        "plans": plans,
        "seconds": round(time.time() - t_all, 1),
    }
    if out_dir is not None:
        import json

        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{name}.json").write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"), default=float)
        )
    log("done")
    return result


def _plans(fte, scores, nu_te, tau_te, fit, world: World, weeks, top: int = 12) -> list[dict]:
    """사이트·주마다 상위 후보 표 — 효과순과 위험순을 나란히 보이기 위한 자료."""
    interval_lo, interval_hi = fit["resp"].averted_interval(fte.X, nu_te.mu0)
    L = world.log
    d = pd.DataFrame(
        {
            "site": fte.site,
            "week": fte.week,
            "asset": fte.asset,
            "risk": scores["risk"],
            "est": scores["responsiveness"],
            "lo": interval_lo,
            "hi": interval_hi,
            "truth": tau_te,
            "e": nu_te.e_raw,
            "mu0": nu_te.mu0,
        }
    )
    ext = L.loc[fte.idx, ["cat", "age", "grade_last", "cmp", "open_wo", "wsv", "bd"]].reset_index(drop=True)
    d = pd.concat([d, ext], axis=1)
    out = []
    for wk in weeks:
        for s, g in d[d["week"] == wk].groupby("site"):
            by_eff = g.nlargest(top, "est")
            by_risk = g.nlargest(top, "risk")
            out.append(
                {
                    "site": int(s),
                    "week": int(wk),
                    "n_eligible": int(len(g)),
                    "by_effect": _rows(by_eff, g),
                    "by_risk": _rows(by_risk, g),
                }
            )
    return out


def _rows(sel: pd.DataFrame, g: pd.DataFrame) -> list[dict]:
    rank_risk = g["risk"].rank(ascending=False, method="first")
    rank_eff = g["est"].rank(ascending=False, method="first")
    rows = []
    for idx, r in sel.iterrows():
        rows.append(
            {
                "asset": int(r["asset"]),
                "cat": r["cat"],
                "cat_ko": CAT_KO[r["cat"]],
                "age": round(float(r["age"]), 1),
                "grade_last": int(r["grade_last"]),
                "cmp": round(float(r["cmp"]), 2),
                "open_wo": int(r["open_wo"]),
                "wsv": int(r["wsv"]),
                "risk": round(float(r["risk"]), 4),
                "averted": round(float(r["est"]), 4),
                "averted_lo": round(float(r["lo"]), 4),
                "averted_hi": round(float(r["hi"]), 4),
                "truth": round(float(r["truth"]), 4),
                "propensity": round(float(r["e"]), 3),
                "low_support": bool(r["e"] < 0.02),
                "rank_risk": int(rank_risk.loc[idx]),
                "rank_effect": int(rank_eff.loc[idx]),
            }
        )
    return rows


__all__ = ["run_scenario", "POLICY_LABELS", "asdict"]
