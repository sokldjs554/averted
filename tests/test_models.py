from __future__ import annotations

import numpy as np

from averted.causal import estimators as est
from averted.causal import nuisance as nu_mod
from averted.causal.data import prepare
from averted.causal.dragonnet import fit_dragonnet
from averted.causal.responsiveness import ResponsivenessModel


def test_responsiveness_model_interval_and_shapes(tiny):
    fr = prepare(tiny.log)
    nu = nu_mod.crossfit(fr.X, fr.T, fr.Y, fr.asset, n_folds=3)
    gamma = est.dr_scores(fr.T, fr.Y, nu)
    m = ResponsivenessModel.fit(fr, nu.mu0, gamma, n_boot=20)
    a = m.averted(fr.X, nu.mu0)
    lo, hi = m.averted_interval(fr.X, nu.mu0)
    assert a.shape == (len(fr),)
    assert (lo <= hi + 1e-12).all()
    assert m.boot.shape[0] == 20
    assert {r["name"] for r in m.multipliers()} >= {"open_wo", "cat_pump"}


def test_dragonnet_trains_and_predicts(tiny):
    fr = prepare(tiny.log)
    m = fit_dragonnet(fr.X, fr.T, fr.Y, fr.asset, epochs=4, seed=0)
    pe, p0, p1 = m.predict_parts(fr.X)
    assert pe.shape == p0.shape == p1.shape == (len(fr),)
    assert ((0 <= p0) & (p0 <= 1) & (0 <= p1) & (p1 <= 1)).all()
    assert np.isfinite(m.averted(fr.X)).all()
