"""시뮬레이션 실행 — 점검 기록(로그)과 정답 효과(truth)를 함께 만든다.

로그: 분석가가 실제로 볼 수 있는 표. 설비·주마다 한 행. (처치 T = 그 주에 점검했는가, 결과 y = 그 주부터 4주 안의 비계획 고장)
정답: 같은 설비·주에서 "점검하지 않았다면 / 했다면"의 4주 내 고장 확률 p0, p1 과 그 차이 tau = p0 − p1 (막은 고장의 기댓값).
      두 세계를 같은 난수(공통 난수)로 M 번씩 굴려 구한다. 추정기는 이 표를 절대 보지 않는다 — 채점에만 쓴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .world import (
    CATEGORIES,
    WSV_CAP,
    Draws,
    Dyn,
    Static,
    WorldConfig,
    calibrate_alpha,
    init_dyn,
    legal_due,
    make_static,
    step,
)

LOG_COLUMNS = [
    "site",
    "asset",
    "week",
    "cat",
    "age",
    "crit",
    "grade_last",
    "wsv",
    "bd",
    "cmp",
    "open_wo",
    "due",
    "pilot",
    "treated",
    "y",
    "y_prev",
]


@dataclass
class World:
    cfg: WorldConfig
    log: pd.DataFrame
    truth: pd.DataFrame  # 같은 행 순서: p0, p1, tau, D, e_true
    assets: pd.DataFrame

    def save(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.log.to_parquet(root / "log.parquet", index=False)
        self.truth.to_parquet(root / "truth.parquet", index=False)
        self.assets.to_parquet(root / "assets.parquet", index=False)

    @staticmethod
    def load(root: Path, cfg: WorldConfig) -> World:
        return World(
            cfg,
            pd.read_parquet(root / "log.parquet"),
            pd.read_parquet(root / "truth.parquet"),
            pd.read_parquet(root / "assets.parquet"),
        )


def _window_any(fail: np.ndarray, start_offset: int, length: int) -> np.ndarray:
    """fail: (weeks, n) bool. 각 주 t 에 대해 weeks t+start_offset .. t+start_offset+length-1 안에 고장이 있었는가. 창이 데이터 밖이면 NaN."""
    weeks, n = fail.shape
    out = np.full((weeks, n), np.nan)
    c = np.cumsum(np.vstack([np.zeros((1, n)), fail.astype(np.float64)]), axis=0)
    for t in range(weeks):
        a, b = t + start_offset, t + start_offset + length
        if a < 0 or b > weeks:
            continue
        out[t] = (c[b] - c[a]) > 0
    return out


def fork_truth(
    cfg: WorldConfig, st: Static, dyn: Dyn, rng: np.random.Generator, m: int
) -> tuple[np.ndarray, np.ndarray]:
    """현재 상태에서 두 세계(이번 주 점검함/안 함)를 M 번씩 굴려 4주 내 고장 확률 (p0, p1) 을 구한다.

    첫 주만 점검 여부를 강제하고, 이후 주들은 평소 현장 규칙(로그 생성 규칙)을 따른다.
    두 세계는 같은 난수를 쓰므로 차이(tau)의 분산이 작다.
    """
    n = len(st)
    stc = st.col()
    base = dyn.fork(m)
    arms = [base.copy(), base.copy()]
    surv = [np.ones((n, m)), np.ones((n, m))]
    for k in range(cfg.horizon):
        draws = Draws.draw(rng, (n, m))
        for a in (0, 1):
            force = (a == 1) if k == 0 else None
            arms[a], ev = step(cfg, stc, arms[a], draws, force_visit=force, no_fail=True)
            surv[a] = surv[a] * ev["surv"]
    # 4주 안에 한 번이라도 고장 = 1 − (주별 생존 확률의 곱). 고장 없는 경로에서 계산하므로 난수 잡음이 훨씬 작다.
    p0 = 1.0 - surv[0].mean(axis=1)
    p1 = 1.0 - surv[1].mean(axis=1)
    tau = (surv[1] - surv[0]).mean(axis=1)
    return p0, p1, tau


def simulate(cfg: WorldConfig, truth_m: int = 128, verbose: bool = False) -> World:
    rng = np.random.default_rng(cfg.seed)
    st = make_static(cfg, rng)
    dyn = init_dyn(st, rng)
    dyn = calibrate_alpha(cfg, st, dyn, np.random.default_rng(cfg.seed + 1))
    for _ in range(cfg.burn_in):  # 번인: 기록하지 않는다
        dyn, _ev = step(cfg, st, dyn, Draws.draw(rng, dyn.D.shape))
    n, W = len(st), cfg.weeks
    rng_truth = np.random.default_rng(cfg.seed + 2)

    keys = ["grade_last", "wsv", "bd", "cmp", "open_wo", "due", "visit", "fail", "e", "D", "p0", "p1", "tau"]
    rec = {k: np.zeros((W, n)) for k in keys}
    for t in range(W):
        rec["grade_last"][t] = dyn.grade_last
        rec["wsv"][t] = np.minimum(dyn.wsv, WSV_CAP)
        rec["bd"][t] = dyn.bd
        rec["cmp"][t] = dyn.cmp
        rec["open_wo"][t] = dyn.pend > 0
        rec["due"][t] = legal_due(st, dyn)
        rec["D"][t] = dyn.D
        if truth_m > 0:
            p0, p1, tau = fork_truth(cfg, st, dyn, rng_truth, truth_m)
            rec["p0"][t], rec["p1"][t], rec["tau"][t] = p0, p1, tau
        draws = Draws.draw(rng, dyn.D.shape)
        dyn, ev = step(cfg, st, dyn, draws)
        rec["visit"][t] = ev["visit"]
        rec["fail"][t] = ev["fail"]
        rec["e"][t] = ev["e"]
        if verbose and t % 26 == 0:
            print(f"[sim] week {t}/{W}", flush=True)

    fail = rec["fail"].astype(bool)
    y = _window_any(fail, 0, cfg.horizon)
    y_prev = _window_any(fail, -cfg.horizon, cfg.horizon)
    asset_ids = np.arange(n)
    rows = []
    for t in range(W):
        rows.append(
            pd.DataFrame(
                {
                    "site": st.site,
                    "asset": asset_ids,
                    "week": t,
                    "cat": [CATEGORIES[c].key for c in st.cat],
                    "age": st.age,
                    "crit": st.crit,
                    "grade_last": rec["grade_last"][t].astype(np.int8),
                    "wsv": rec["wsv"][t],
                    "bd": rec["bd"][t],
                    "cmp": rec["cmp"][t],
                    "open_wo": rec["open_wo"][t].astype(np.int8),
                    "due": rec["due"][t].astype(bool),
                    "pilot": st.pilot,
                    "treated": rec["visit"][t].astype(np.int8),
                    "y": y[t],
                    "y_prev": y_prev[t],
                    "p0": rec["p0"][t],
                    "p1": rec["p1"][t],
                    "tau": rec["tau"][t],
                    "D": rec["D"][t],
                    "e_true": rec["e"][t],
                }
            )
        )
    full = pd.concat(rows, ignore_index=True)
    log = full[LOG_COLUMNS].copy()
    truth = full[["p0", "p1", "tau", "D", "e_true"]].copy()
    assets = pd.DataFrame(
        {
            "asset": asset_ids,
            "site": st.site,
            "cat": [CATEGORIES[c].key for c in st.cat],
            "rho": st.rho,
            "skill": st.skill,
            "culture": st.culture,
        }
    )
    return World(cfg, log, truth, assets)
