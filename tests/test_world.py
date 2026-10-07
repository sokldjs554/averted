"""시뮬레이터 불변식 — 정답(두 세계 포크)이 직접 시뮬레이션과 일치하고, 분석가에게 보이는 표에 정답이 새지 않는다."""

from __future__ import annotations

import numpy as np

from averted.sim.generate import LOG_COLUMNS, fork_truth, simulate
from averted.sim.world import Draws, WorldConfig, calibrate_alpha, init_dyn, make_static, step


def test_deterministic_given_seed():
    cfg = WorldConfig(seed=9, n_sites=2, assets_min=30, assets_max=40, weeks=20, burn_in=20)
    a, b = simulate(cfg, truth_m=8), simulate(cfg, truth_m=8)
    assert a.log.equals(b.log)
    assert np.allclose(a.truth["tau"], b.truth["tau"])


def test_log_has_no_truth_columns(tiny):
    banned = {"p0", "p1", "tau", "D", "e_true"}
    assert banned.isdisjoint(tiny.log.columns)
    assert list(tiny.log.columns) == LOG_COLUMNS
    assert len(tiny.truth) == len(tiny.log)


def test_outcome_window_is_missing_at_the_tail(tiny_cfg, tiny):
    last = tiny.log["week"].max()
    tail = tiny.log[tiny.log["week"] > last - tiny_cfg.horizon + 1]
    assert tail["y"].isna().all()
    head = tiny.log[tiny.log["week"] <= last - tiny_cfg.horizon + 1]
    assert head["y"].notna().all()


def test_legal_due_rows_are_always_visited(tiny):
    due = tiny.log[tiny.log["due"]]
    assert len(due) > 0
    assert (due["treated"] == 1).all()


def test_flat_world_switches_off_pending_repairs():
    cfg = WorldConfig(seed=2, n_sites=2, assets_min=30, assets_max=40, weeks=30, burn_in=30, flat=True)
    w = simulate(cfg, truth_m=0)
    assert w.log["open_wo"].sum() == 0


def test_fork_matches_direct_simulation():
    """Rao-Blackwell 로 구한 4주 내 고장 확률이, 같은 상태에서 고장 난수를 직접 굴린 빈도와 일치한다."""
    cfg = WorldConfig(seed=3, n_sites=1, assets_min=40, assets_max=40, weeks=10, burn_in=30)
    rng = np.random.default_rng(0)
    st = make_static(cfg, rng)
    dyn = calibrate_alpha(cfg, st, init_dyn(st, rng), np.random.default_rng(1), weeks=20)
    for _ in range(30):
        dyn, _ = step(cfg, st, dyn, Draws.draw(rng, dyn.D.shape))
    p0, p1, tau = fork_truth(cfg, st, dyn, np.random.default_rng(11), m=600)
    # 직접 시뮬레이션: 같은 상태를 복제해 고장 난수를 실제로 쓰고 4주 안의 고장 여부를 센다
    n, m = len(st), 6000
    stc = st.col()
    freq = []
    for arm in (False, True):
        d = dyn.fork(m)
        any_fail = np.zeros((n, m), dtype=bool)
        r = np.random.default_rng(99 + int(arm))
        for k in range(cfg.horizon):
            d, ev = step(cfg, stc, d, Draws.draw(r, (n, m)), force_visit=arm if k == 0 else None)
            any_fail |= ev["fail"]
        freq.append(any_fail.mean(axis=1))
    assert np.abs(freq[0] - p0).mean() < 0.01
    assert np.abs(freq[1] - p1).mean() < 0.01
    assert np.allclose(tau, p0 - p1, atol=1e-9)


def test_visiting_cannot_help_an_asset_with_an_open_work_order():
    """수리 접수된 설비를 점검해도 새로 발견할 것이 없다 → 효과는 (거의) 0 이거나 약간 해롭다."""
    cfg = WorldConfig(seed=4, n_sites=3, assets_min=60, assets_max=80, weeks=60, burn_in=40)
    w = simulate(cfg, truth_m=24)
    tau = w.truth["tau"].to_numpy()
    open_wo = w.log["open_wo"].to_numpy() == 1
    due = w.log["due"].to_numpy()
    sel = open_wo & ~due
    assert sel.sum() > 50
    assert tau[sel].mean() < 0.003
    assert tau[~open_wo & ~due].mean() > tau[sel].mean()
