"""몬테카를로 검증 — 같은 설정의 세계를 여러 번 새로 만들어 추정기가 정답을 얼마나 맞히고 95% 구간이 실제로 95% 를 덮는가를 잰다.

신뢰구간이 숫자를 장식하는지 보증하는지는 여기서 갈린다. 설비 단위 군집 표준오차를 쓴 구간은 덮어야 하고,
같은 행을 독립으로 가정한 단순 구간은 못 덮는다. 숨은 교란(γ>0)에서는 어떤 구간도 못 덮는다 — 그것도 보고한다.
"""

from __future__ import annotations

import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..causal import estimators as est
from ..causal import nuisance as nu_mod
from ..causal.data import prepare
from ..sim.generate import simulate
from ..sim.world import WorldConfig


def _one(args):
    kind, seed, n_sites, weeks = args
    kw = {"base": {}, "flat": {"flat": True}, "hunch": {"hunch": 0.6}}[kind]
    cfg = WorldConfig(seed=seed, n_sites=n_sites, weeks=weeks, burn_in=78, **kw)
    w = simulate(cfg, truth_m=24)
    fr = prepare(w.log)
    tau = w.truth["tau"].to_numpy()[fr.idx]
    truth = float(-tau.mean())
    nu = nu_mod.crossfit(fr.X, fr.T, fr.Y, fr.asset, n_folds=3, seed=seed)
    out = {"kind": kind, "seed": seed, "truth": truth}
    for e in (
        est.naive(fr.T, fr.Y, fr.asset),
        est.regression(fr.T, fr.Y, fr.asset, nu),
        est.ipw(fr.T, fr.Y, fr.asset, nu),
        est.aipw(fr.T, fr.Y, fr.asset, nu),
    ):
        out[e.name] = {"effect": e.effect, "se": e.se, "lo": e.lo, "hi": e.hi}
    # 같은 AIPW 를 설비 군집을 무시한 표준오차(행 독립 가정)로 만든 구간 — 군집 보정이 왜 필요한지 보이기 위한 비교
    g = est.dr_scores(fr.T, fr.Y, nu)
    se_iid = float(g.std(ddof=1) / np.sqrt(len(g)))
    out["aipw_iid"] = {
        "effect": float(g.mean()),
        "se": se_iid,
        "lo": float(g.mean() - 1.96 * se_iid),
        "hi": float(g.mean() + 1.96 * se_iid),
    }
    return out


def coverage(
    kinds=("base", "flat", "hunch"), reps: int = 40, n_sites: int = 4, weeks: int = 100, workers: int = 4
) -> list[dict]:
    jobs = [(k, 1000 + r, n_sites, weeks) for k in kinds for r in range(reps)]
    # 워커마다 스레드 1개 (트리 학습의 OpenMP 가 코어를 서로 빼앗는 것을 막는다), 새 인터프리터(spawn)로 환경변수가 적용되게 한다
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = "1"
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        return list(ex.map(_one, jobs))


def summarize(rows: list[dict]) -> dict:
    out = {}
    for kind in sorted({r["kind"] for r in rows}):
        rs = [r for r in rows if r["kind"] == kind]
        entry = {"reps": len(rs), "truth_mean": float(np.mean([r["truth"] for r in rs]))}
        for name in ("naive", "regression", "ipw", "aipw", "aipw_iid"):
            eff = np.array([r[name]["effect"] for r in rs])
            tru = np.array([r["truth"] for r in rs])
            cover = np.mean([r[name]["lo"] <= r["truth"] <= r[name]["hi"] for r in rs])
            entry[name] = {
                "bias": float(np.mean(-eff + tru)),  # averted 부호 (= −effect) 기준 평균 오차
                "rmse": float(np.sqrt(np.mean((eff - (-tru)) ** 2))),
                "coverage": float(cover),
                "mean_ci_width": float(np.mean([r[name]["hi"] - r[name]["lo"] for r in rs])),
            }
        out[kind] = entry
    return out
