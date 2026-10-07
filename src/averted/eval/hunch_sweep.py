"""숨은 교란 강도(γ) 스윕 — 감사 도구가 "틀린 추정"을 얼마나 잡아내는가.

γ 를 올리면(분석가가 못 보는 신호로 점검을 결정) 모든 보정 추정기가 점점 틀린다. 그때 감사의 경고(음성 대조, 민감도)가
실제 편향을 따라 올라오는지를 같은 세계에서 정답과 함께 잰다. 못 잡으면 못 잡는다고 보고한다.
"""

from __future__ import annotations

import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..audit import run_audit
from ..sim.generate import simulate
from ..sim.world import WorldConfig


def _one(args):
    gamma, seed, n_sites, weeks, flat = args
    cfg = WorldConfig(seed=seed, n_sites=n_sites, weeks=weeks, burn_in=78, hunch=gamma, flat=flat)
    w = simulate(cfg, truth_m=24)
    ok = w.log["y"].notna() & ~w.log["due"]
    tau = w.truth["tau"].to_numpy()[ok.to_numpy()]
    rep = run_audit(w.log, truth_ate=float(-tau.mean()), n_folds=3, seed=seed)
    a = rep["estimates"]["aipw"]
    nc = rep.get("negative_control") or {}
    tip = rep.get("tipping") or {}
    return {
        "gamma": gamma,
        "seed": seed,
        "truth_averted": float(tau.mean()),
        "naive": rep["estimates"]["naive"]["averted"],
        "aipw": a["averted"],
        "aipw_lo": a["averted_lo"],
        "aipw_hi": a["averted_hi"],
        "bias": a["averted"] - float(tau.mean()),
        "covers": bool(a["averted_lo"] <= tau.mean() <= a["averted_hi"]),
        "nc_z": nc.get("z"),
        "nc_flag": nc.get("flag"),
        "tip_ratio": tip.get("ratio"),
        "level": rep["verdict"]["level"],
    }


def hunch_sweep(
    gammas=(0.0, 0.3, 0.6, 1.0, 1.5), seeds=(1, 2, 3), n_sites=8, weeks=120, flat=False, workers: int = 4
) -> list[dict]:
    jobs = [(g, s, n_sites, weeks, flat) for g in gammas for s in seeds]
    # 워커마다 스레드 1개 (트리 학습의 OpenMP 가 코어를 서로 빼앗는 것을 막는다), 새 인터프리터(spawn)로 환경변수가 적용되게 한다
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = "1"
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        return list(ex.map(_one, jobs))


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    for g in sorted({r["gamma"] for r in rows}):
        rs = [r for r in rows if r["gamma"] == g]
        out.append(
            {
                "gamma": g,
                "n": len(rs),
                "truth_averted": float(np.mean([r["truth_averted"] for r in rs])),
                "naive": float(np.mean([r["naive"] for r in rs])),
                "aipw": float(np.mean([r["aipw"] for r in rs])),
                "bias": float(np.mean([r["bias"] for r in rs])),
                "coverage": float(np.mean([r["covers"] for r in rs])),
                "nc_flag_rate": float(np.mean([bool(r["nc_flag"]) for r in rs])),
                "nc_z_mean": float(np.mean([abs(r["nc_z"]) for r in rs if r["nc_z"] is not None] or [0])),
            }
        )
    return out
