"""학습곡선 — 고객사(사이트) 몇 곳의 로그로 학습하면, 처음 보는 고객사에서 효과순이 위험순을 이기는가.

큰 세계(예: 60개 사이트) 하나를 만들고, 일부 사이트는 끝까지 떼어 둔다(신규 고객사). 나머지에서 k 개를 무작위로 골라 학습하고
떼어 둔 사이트의 모든 주에서 정책 가치(점검 100번당 막는 고장)를 정답과 로그 기반 추정(OPE)으로 잰다. k 마다 여러 번 반복한다.
이 곡선이 "고객사를 풀링하는 이유"의 근거다.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from ..causal import estimators as est
from ..causal import nuisance as nu_mod
from ..causal import policy as pol
from ..causal.data import prepare
from ..causal.dragonnet import fit_dragonnet
from ..causal.responsiveness import ResponsivenessModel
from ..sim.generate import simulate
from ..sim.world import WorldConfig


def learning_curve(
    n_sites: int = 60,
    n_test_sites: int = 12,
    ks=(4, 8, 16, 32, 48),
    repeats=(5, 4, 3, 2, 2),
    k_budget: int = 8,
    seed: int = 7,
    truth_m: int = 24,
    deep_from: int = 16,
    verbose: bool = True,
    world=None,
) -> dict:
    t0 = time.time()
    cfg = WorldConfig(seed=seed, n_sites=n_sites, weeks=156, burn_in=78)
    w = world or simulate(cfg, truth_m=truth_m)
    fr = prepare(w.log)
    tau_all = w.truth["tau"].to_numpy()[fr.idx]
    rng = np.random.default_rng(seed)
    sites = np.arange(n_sites)
    test_sites = rng.choice(sites, n_test_sites, replace=False)
    pool = np.setdiff1d(sites, test_sites)
    te = np.isin(fr.site, test_sites)
    fte, tau_te = fr.subset(te), tau_all[te]
    df = pd.DataFrame({"site": fte.site, "week": fte.week})
    if verbose:
        print(
            f"[curve] world ready rows={len(fr):,} test rows={len(fte):,} ({time.time() - t0:.0f}s)",
            flush=True,
        )
    # 고정 기준선: 무작위·오라클
    fixed = pol.policy_values(df, {"random": rng.random(len(fte)), "oracle": tau_te}, k_budget, tau_te, None)
    rows = []
    for k, rep in zip(ks, repeats, strict=True):
        for r in range(rep):
            sub = rng.choice(pool, size=min(k, len(pool)), replace=False)
            tr = np.isin(fr.site, sub)
            ftr = fr.subset(tr)
            nu = nu_mod.crossfit(ftr.X, ftr.T, ftr.Y, ftr.asset, n_folds=3, seed=r)
            gamma = est.dr_scores(ftr.T, ftr.Y, nu)
            resp = ResponsivenessModel.fit(ftr, nu.mu0, gamma, n_boot=0)
            models = nu_mod.fit_models(ftr.X, ftr.T, ftr.Y, seed=r)
            nu_te = nu_mod.predict_models(models, fte.X)
            gamma_te = est.dr_scores(fte.T, fte.Y, nu_te)
            risk = pol.fit_risk_model(ftr.X, ftr.Y, seed=r)
            p_risk = risk.predict_proba(fte.X)[:, 1]
            scores = {
                "risk": p_risk,
                "risk_rule": np.where(fte.col("open_wo") == 1, -1.0, p_risk),
                "responsiveness": resp.averted(fte.X, nu_te.mu0),
                "t_learner": nu_te.mu0 - nu_te.mu1,
            }
            scores["responsiveness_rule"] = np.where(fte.col("open_wo") == 1, -1.0, scores["responsiveness"])
            if k >= deep_from:
                dn = fit_dragonnet(ftr.X, ftr.T, ftr.Y, ftr.asset, seed=r)
                scores["dragonnet"] = dn.averted(fte.X)
            vals = pol.policy_values(df, scores, k_budget, tau_te, gamma_te)
            for name, v in vals.items():
                rows.append(
                    {
                        "k_sites": k,
                        "rep": r,
                        "policy": name,
                        "true_per100": v["true_per100"],
                        "ope_per100": v["ope_per100"],
                        "train_rows": len(ftr),
                    }
                )
            if verbose:
                print(
                    f"[curve] k={k} rep={r} train_rows={len(ftr):,} resp={vals['responsiveness']['true_per100']:.2f} risk={vals['risk']['true_per100']:.2f} ({time.time() - t0:.0f}s)",
                    flush=True,
                )
    return {
        "n_sites": n_sites,
        "n_test_sites": n_test_sites,
        "budget_k": k_budget,
        "test_rows": int(len(fte)),
        "fixed": {k: v["true_per100"] for k, v in fixed.items()},
        "rows": rows,
    }


def summarize(res: dict) -> list[dict]:
    df = pd.DataFrame(res["rows"])
    g = (
        df.groupby(["k_sites", "policy"])
        .agg(
            true_mean=("true_per100", "mean"),
            true_sd=("true_per100", "std"),
            ope_mean=("ope_per100", "mean"),
            ope_abs_err=("true_per100", lambda s: 0.0),
            n=("rep", "size"),
            train_rows=("train_rows", "mean"),
        )
        .reset_index()
    )
    err = (
        df.assign(err=(df["ope_per100"] - df["true_per100"]).abs())
        .groupby(["k_sites", "policy"])["err"]
        .mean()
        .reset_index()
    )
    g = g.drop(columns="ope_abs_err").merge(
        err.rename(columns={"err": "ope_abs_err"}), on=["k_sites", "policy"]
    )
    return g.round(4).to_dict("records")
