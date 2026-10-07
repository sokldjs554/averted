"""무작위 점검 파일럿 — 관측 로그로 답할 수 없을 때 답을 얻는 유일한 길.

일부 설비·주에 점검을 **동전 던지기로** 배정하면 어떤 숨은 교란도 처치와 무관해진다.
여기서는 (1) 필요한 규모를 계산하고 (2) 파일럿 데이터에서 효과를 추정한다. 실증(PoC) 계획서에 넣을 숫자를 만드는 도구다.

겹치지 않는 창: 결과는 "그 주부터 H주 안의 고장"이라 매주 판정하면 창이 겹쳐 같은 사건을 중복해 센다.
파일럿에서는 H주마다 한 번만 판정(설비당 floor(주 수/H) 개 독립 창)으로 센다.
설계 효과: 같은 설비의 창들은 설비 고유 위험 때문에 닮으므로 표본 크기를 1 + (m − 1)·ICC 배로 부풀려야 한다.
시뮬레이터에서 4주 창의 ICC 를 재 보니 0.02 안팎이었다(`docs/evaluation.md`) — 실제 로그에서는 직접 추정해 넣어야 한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

from . import estimators as est


@dataclass
class PilotPlan:
    base_rate: float
    averted_pp: float
    treat_share: float
    n_assets: int
    weeks: int
    icc: float
    design_effect: float
    n_rows: int
    se: float
    power: float
    min_detectable_pp: float

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _se_two_prop(p0: float, p1: float, n_treat: float, n_ctrl: float, de: float) -> float:
    v = p1 * (1 - p1) / max(n_treat, 1) + p0 * (1 - p0) / max(n_ctrl, 1)
    return math.sqrt(v * de)


def plan(
    base_rate: float,
    averted_pp: float,
    n_assets: int,
    weeks: int,
    treat_share: float = 0.5,
    icc: float = 0.02,
    alpha: float = 0.05,
    horizon: int = 4,
) -> PilotPlan:
    """파일럿 규모(설비 수 × 주)에서 평균 효과 `averted_pp`(%p)를 검출할 검정력과, 80% 검정력으로 검출 가능한 최소 효과."""
    windows = max(weeks // horizon, 1)
    n_rows = n_assets * windows
    de = 1 + (windows - 1) * icc
    n_t, n_c = n_rows * treat_share, n_rows * (1 - treat_share)
    p0 = base_rate
    p1 = max(base_rate - averted_pp / 100.0, 1e-6)
    se = _se_two_prop(p0, p1, n_t, n_c, de)
    z = stats.norm.ppf(1 - alpha / 2)
    power = float(stats.norm.cdf(abs(p0 - p1) / se - z)) if se > 0 else 0.0
    # 최소 검출 효과 (검정력 80%): 근사적으로 (z_a + z_b) · se
    mde = (z + stats.norm.ppf(0.8)) * _se_two_prop(p0, p0, n_t, n_c, de)
    return PilotPlan(
        base_rate, averted_pp, treat_share, n_assets, weeks, icc, de, int(n_rows), se, power, mde * 100.0
    )


def required_weeks(
    base_rate: float,
    averted_pp: float,
    n_assets: int,
    treat_share: float = 0.5,
    icc: float = 0.02,
    target_power: float = 0.8,
    max_weeks: int = 520,
) -> int | None:
    """주어진 설비 수에서 목표 검정력에 도달하는 데 필요한 주 수. 설계 효과 때문에 검정력이 포화되면 None (설비 수를 늘려야 한다)."""
    for w in range(4, max_weeks + 1, 4):
        if plan(base_rate, averted_pp, n_assets, w, treat_share, icc).power >= target_power:
            return w
    return None


def required_assets(
    base_rate: float,
    averted_pp: float,
    weeks: int,
    treat_share: float = 0.5,
    icc: float = 0.02,
    target_power: float = 0.8,
    max_assets: int = 200_000,
) -> int | None:
    """주어진 기간에서 목표 검정력에 필요한 설비 수 (이분 탐색)."""
    if plan(base_rate, averted_pp, max_assets, weeks, treat_share, icc).power < target_power:
        return None
    lo, hi = 1, max_assets
    while lo < hi:
        mid = (lo + hi) // 2
        if plan(base_rate, averted_pp, mid, weeks, treat_share, icc).power >= target_power:
            hi = mid
        else:
            lo = mid + 1
    return lo


def analyze(T: np.ndarray, Y: np.ndarray, groups: np.ndarray) -> est.Estimate:
    """무작위 파일럿 분석: 처치군 − 대조군 평균 차이(군집 강건 구간). 보정이 필요 없다."""
    return est.naive(T, Y, groups)
