from __future__ import annotations

import numpy as np
import pandas as pd

from averted.causal import pilot, policy


def test_power_increases_with_size_and_effect():
    small = pilot.plan(0.08, 1.0, n_assets=100, weeks=8)
    big = pilot.plan(0.08, 1.0, n_assets=400, weeks=26)
    assert big.power > small.power
    bigger_effect = pilot.plan(0.08, 2.0, n_assets=100, weeks=8)
    assert bigger_effect.power > small.power
    assert big.min_detectable_pp < small.min_detectable_pp


def test_required_weeks_reaches_target_power():
    w = pilot.required_weeks(0.14, 3.0, n_assets=300)
    assert w is not None
    assert pilot.plan(0.14, 3.0, 300, w).power >= 0.8
    assert pilot.plan(0.14, 3.0, 300, w - 4).power < 0.8


def test_small_effects_cannot_be_detected_by_a_single_small_customer():
    """설계 효과 때문에 기간을 늘려도 검정력이 포화된다 → 설비 수를 늘려야만 한다는 것을 계산기가 말해야 한다."""
    assert pilot.required_weeks(0.07, 0.8, n_assets=150) is None
    n = pilot.required_assets(0.07, 0.8, weeks=52)
    assert n is not None and n > 1500
    assert pilot.plan(0.07, 0.8, n, 52).power >= 0.8


def test_top_k_selection_is_exact_per_group():
    df = pd.DataFrame(
        {"site": [0, 0, 0, 0, 1, 1, 1], "week": [1] * 7, "s": [0.1, 0.9, 0.5, 0.7, 0.2, 0.3, 0.1]}
    )
    pos = policy.select_top_k(df, "s", 2)
    assert sorted(df.loc[pos, "s"].tolist()) == sorted([0.9, 0.7, 0.3, 0.2])


def test_oracle_policy_beats_random_in_expectation():
    rng = np.random.default_rng(0)
    n = 4000
    df = pd.DataFrame({"site": rng.integers(0, 5, n), "week": rng.integers(0, 20, n)})
    tau = rng.gamma(1.0, 0.01, n)
    vals = policy.policy_values(df, {"oracle": tau, "random": rng.random(n)}, 3, tau, None)
    assert vals["oracle"]["true_per100"] > 2 * vals["random"]["true_per100"]
