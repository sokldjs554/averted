"""로그 감사 — 점검 로그 한 장을 받아 "점검 효과를 말해도 되는가"를 판정한다. (제품의 진입점)

실행 순서: 검증 → 처치 확률 모형(겹침·균형) → 효과 추정기들(순진 비교·회귀·IPW·AIPW) → 음성 대조 → 민감도 → 부분집단 → 판정.
시뮬레이터 로그와 실제 로그가 같은 코드를 지나간다.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .causal import diagnostics as diag
from .causal import estimators as est
from .causal import nuisance as nu_mod
from .causal import pilot, sensitivity, subgroups
from .causal.data import DEFAULT_SPEC, LogSpec, prepare


def verdict(report: dict) -> dict:
    """데이터로 확인 가능한 문제만으로 신호등을 정한다 (기준은 docs/design.md 의 관례값).

    민감도(숨은 교란에 대한 취약성)는 데이터로 검증할 수 없는 가정에 대한 정보라서 신호등에 섞지 않고 `assumption_dependence` 로 따로 낸다.
    """
    warns = []
    ov = report["overlap"]
    if ov["share_extreme"] > 0.05:
        warns.append(
            f"점검 여부가 사실상 정해져 있는 행이 {100 * ov['share_extreme']:.1f}%. 이 행들은 비교할 상대가 로그에 거의 없다."
        )
    if min(ov["ess_ratio_treated"], ov["ess_ratio_control"]) < 0.15:
        warns.append("일부 행에 가중치가 지나치게 쏠린다. 실제로 쓰이는 표본이 전체의 15%도 안 된다.")
    worst = max((abs(b["smd_weighted"]) for b in report["balance"]), default=0.0)
    if worst > 0.10:
        warns.append(
            f"가중치를 줘도 점검한 쪽과 안 한 쪽의 차이가 남는다 (가장 큰 차이 {worst:.2f}, 기준 0.10)."
        )
    nc = report.get("negative_control")
    severe = False
    if nc and nc["flag"]:
        warns.append(
            f"점검 이전의 고장에서도 '효과'가 보인다 (z={nc['z']:.1f}). 보정되지 않은 이유가 남아 있다는 신호다."
        )
        severe = True
    if ov["share_extreme"] > 0.20:
        severe = True
    a = report["estimates"]["aipw"]
    if a["averted_lo"] <= 0 <= a["averted_hi"]:
        warns.append("95% 구간이 0을 포함한다. 효과가 있다고도 없다고도 말할 수 없다.")
    level = "green" if not warns else ("red" if severe else "yellow")
    tip = report.get("tipping")
    dep = None
    if tip:
        r = tip["ratio"]
        dep = "높음" if r > 2 else ("보통" if r > 0.5 else "낮음")
    return {"level": level, "warnings": warns, "assumption_dependence": dep}


def run_audit(
    log: pd.DataFrame,
    spec: LogSpec = DEFAULT_SPEC,
    n_folds: int = 5,
    with_sensitivity: bool = True,
    seed: int = 0,
    truth_ate: float | None = None,
) -> dict:
    t0 = time.time()
    fr = prepare(log, spec)
    n_all = int(log[spec.outcome].notna().sum())
    nu = nu_mod.crossfit(fr.X, fr.T, fr.Y, fr.asset, n_folds=n_folds, seed=seed)
    estimates = {
        "naive": est.naive(fr.T, fr.Y, fr.asset),
        "regression": est.regression(fr.T, fr.Y, fr.asset, nu),
        "ipw": est.ipw(fr.T, fr.Y, fr.asset, nu),
        "aipw": est.aipw(fr.T, fr.Y, fr.asset, nu),
    }
    gamma = est.dr_scores(fr.T, fr.Y, nu)
    report: dict = {
        "data": {
            "rows_with_outcome": n_all,
            "rows_analyzed": len(fr),
            "rows_excluded_due": n_all - len(fr),
            "assets": int(len(np.unique(fr.asset))),
            "weeks": int(len(np.unique(fr.week))),
            "treated_share": float(fr.T.mean()),
            "outcome_rate": float(fr.Y.mean()),
            "outcome_rate_treated": float(fr.Y[fr.T == 1].mean()),
            "outcome_rate_control": float(fr.Y[fr.T == 0].mean()),
        },
        "estimates": {k: v.to_dict() for k, v in estimates.items()},
        "overlap": diag.overlap(nu, fr.T),
        "balance": diag.balance(fr, nu),
    }
    if truth_ate is not None:
        report["truth_averted"] = -truth_ate
    nc = diag.negative_control(fr, n_folds=min(n_folds, 3), seed=seed)
    if nc:
        report["negative_control"] = nc
    if with_sensitivity:
        bench = sensitivity.benchmark_drop(fr, estimates["aipw"], seed=seed)
        report["benchmarks"] = bench
        report["tipping"] = sensitivity.tipping(estimates["aipw"], bench)
    # 부분집단: 종류별 (범주 열이 있으면)
    for c in spec.categorical:
        cols = [i for i, n in enumerate(fr.names) if n.startswith(c + "_")]
        if cols:
            labels = np.array([fr.names[cols[j]][len(c) + 1 :] for j in np.argmax(fr.X[:, cols], axis=1)])
            report.setdefault("subgroups", {})[c] = subgroups.subgroup_effects(labels, fr.T, gamma, fr.asset)
    # 파일럿 제안: 관측된 기저 위험과 AIPW 효과 크기를 그대로 쓴 필요 규모
    base = float(fr.Y[fr.T == 0].mean())
    a = estimates["aipw"]
    averted_pp = max(abs(a.averted) * 100, 0.25)
    n_assets = report["data"]["assets"]
    report["pilot"] = {
        "assumed_averted_pp": averted_pp,
        "weeks_needed_half_of_assets": pilot.required_weeks(
            base, averted_pp, max(n_assets // 2, 1), treat_share=0.5
        ),
        "weeks_needed_all_assets": pilot.required_weeks(base, averted_pp, n_assets, treat_share=0.5),
        "base_rate": base,
    }
    report["verdict"] = verdict(report)
    report["seconds"] = round(time.time() - t0, 1)
    return report
