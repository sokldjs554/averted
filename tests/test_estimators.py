"""추정기 검증 — 정답을 아는 데이터에서 복원되는가, 그리고 econml 과 일치하는가."""

from __future__ import annotations

import numpy as np
import pytest

from averted.causal import estimators as est
from averted.causal import nuisance as nu_mod
from averted.causal.data import prepare


def _confounded(n=20000, seed=0, ate=-0.10):
    """교란이 있는 인공 자료: 위험한(x 큰) 설비를 더 점검하고, 점검은 고장 확률을 ate 만큼 (로짓 척도 근사) 낮춘다."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    e = 1 / (1 + np.exp(-(1.6 * x[:, 0] - 1.0)))
    t = (rng.random(n) < e).astype(np.int8)
    base = 1 / (1 + np.exp(-(-1.2 + 1.3 * x[:, 0] + 0.5 * x[:, 1])))
    p1 = np.clip(base + ate, 0.001, 0.999)
    p = np.where(t == 1, p1, base)
    y = (rng.random(n) < p).astype(float)
    true_ate = float(np.mean(np.clip(base + ate, 0.001, 0.999) - base))
    groups = np.arange(n)
    return x, t, y, groups, true_ate


def test_aipw_recovers_effect_where_naive_fails():
    x, t, y, g, true_ate = _confounded()
    nu = nu_mod.crossfit(x, t, y, g, n_folds=4, seed=1)
    a = est.aipw(t, y, g, nu)
    n = est.naive(t, y, g)
    assert abs(a.effect - true_ate) < 3 * a.se + 0.01
    assert a.lo <= true_ate <= a.hi
    assert (
        n.effect > true_ate + 0.05
    )  # 순진한 비교는 교란 때문에 크게 틀린다 (점검한 쪽이 더 위험하므로 효과가 덜 음수로 보인다)


def test_all_adjusted_estimators_agree_roughly():
    x, t, y, g, true_ate = _confounded(seed=3)
    nu = nu_mod.crossfit(x, t, y, g, n_folds=4, seed=2)
    vals = [est.regression(t, y, g, nu).effect, est.ipw(t, y, g, nu).effect, est.aipw(t, y, g, nu).effect]
    assert max(vals) - min(vals) < 0.05
    assert all(abs(v - true_ate) < 0.06 for v in vals)


def test_cluster_se_is_larger_when_rows_within_cluster_are_correlated():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(200), 20)
    shared = rng.normal(size=200)[g]
    psi = shared + 0.2 * rng.normal(size=len(g))
    iid = psi.std(ddof=1) / np.sqrt(len(psi))
    assert est.cluster_se(psi, g) > 2.5 * iid


def test_randomized_data_needs_no_adjustment(tiny_cfg):
    from averted.sim.generate import simulate
    from averted.sim.world import WorldConfig

    cfg = WorldConfig(
        seed=8, n_sites=4, assets_min=60, assets_max=80, weeks=80, burn_in=40, random_visit=0.25, hunch=1.5
    )
    w = simulate(cfg, truth_m=24)
    fr = prepare(w.log)
    tau = w.truth["tau"].to_numpy()[fr.idx]
    n = est.naive(fr.T, fr.Y, fr.asset)
    assert n.lo - 0.01 <= -tau.mean() <= n.hi + 0.01  # 무작위 배정이면 숨은 교란이 있어도 단순 차이가 맞는다


@pytest.mark.skipif(pytest.importorskip("econml", reason="econml 없음") is None, reason="econml 없음")
def test_matches_econml_doubly_robust_ate():
    """같은 교차적합 교란 모형을 넣었을 때 우리 AIPW 평균이 econml 의 DR 평균 효과와 같아야 한다."""
    from econml.dr import LinearDRLearner

    x, t, y, g, _ = _confounded(n=12000, seed=5)
    nu = nu_mod.crossfit(x, t, y, g, n_folds=4, seed=7)
    ours = est.aipw(t, y, g, nu).effect
    m = LinearDRLearner(
        model_propensity=nu_mod._gbm(0),
        model_regression=nu_mod._gbm(1),
        discrete_outcome=True,
        cv=4,
        random_state=0,
    ).fit(y, t, X=None, W=x)
    theirs = float(m.ate_inference().mean_point)
    assert abs(ours - theirs) < 0.02
