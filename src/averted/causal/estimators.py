"""평균 효과(ATE) 추정기 — 직접 구현.

모든 값은 "막은 고장"의 부호 규약을 따른다:  효과 = E[Y(1) − Y(0)] (음수면 점검이 고장을 줄인다).
표기 규약: 보고할 때는 `averted = −effect` (점검 1회가 막은 고장 확률) 로 바꿔 쓴다.

구현한 것
  naive        처치군 평균 − 대조군 평균                         (교란을 무시)
  regression   표준화(g-computation): mean(μ1(X) − μ0(X))         (결과 모형만 믿는다)
  ipw          안정화 역확률가중(처치 확률 모형만 믿는다)
  aipw         증대 역확률가중(이중 강건): 둘 중 하나만 맞아도 일치
신뢰구간: AIPW 영향함수를 **설비별로 묶어서** 분산을 구한다 (같은 설비의 여러 주는 독립이 아니다).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from .nuisance import Nuisance


@dataclass
class Estimate:
    name: str
    effect: float  # E[Y(1) − Y(0)]
    se: float
    lo: float
    hi: float

    @property
    def averted(self) -> float:
        return -self.effect

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "effect": self.effect,
            "se": self.se,
            "lo": self.lo,
            "hi": self.hi,
            "averted": -self.effect,
            "averted_lo": -self.hi,
            "averted_hi": -self.lo,
        }


def cluster_se(psi: np.ndarray, groups: np.ndarray) -> float:
    """영향함수 값 ψ_i 의 평균에 대한 군집(설비) 강건 표준오차."""
    n = len(psi)
    centered = psi - psi.mean()
    _, inv = np.unique(groups, return_inverse=True)
    sums = np.bincount(inv, weights=centered)
    g = len(sums)
    var = (g / max(g - 1, 1)) * np.sum(sums**2) / n**2
    return float(np.sqrt(var))


def _make(name: str, psi: np.ndarray, est: float, groups: np.ndarray, level: float = 0.95) -> Estimate:
    se = cluster_se(psi, groups)
    z = stats.norm.ppf(0.5 + level / 2)
    return Estimate(name, float(est), se, float(est - z * se), float(est + z * se))


def naive(T, Y, groups) -> Estimate:
    est = Y[T == 1].mean() - Y[T == 0].mean()
    p = T.mean()
    psi = T * (Y - Y[T == 1].mean()) / p - (1 - T) * (Y - Y[T == 0].mean()) / (1 - p)
    return _make("naive", psi + est, est, groups)


def dr_scores(T, Y, nu: Nuisance) -> np.ndarray:
    """AIPW 점수 Γ_i = μ1 − μ0 + T(Y − μ1)/e − (1−T)(Y − μ0)/(1−e). 평균이 ATE, 개별 값은 CATE 의 잡음 섞인 불편 추정치."""
    return nu.mu1 - nu.mu0 + T * (Y - nu.mu1) / nu.e - (1 - T) * (Y - nu.mu0) / (1 - nu.e)


def aipw(T, Y, groups, nu: Nuisance) -> Estimate:
    g = dr_scores(T, Y, nu)
    return _make("aipw", g, g.mean(), groups)


def regression(T, Y, groups, nu: Nuisance) -> Estimate:
    psi = nu.mu1 - nu.mu0
    return _make("regression", psi, psi.mean(), groups)


def ipw(T, Y, groups, nu: Nuisance) -> Estimate:
    w1 = T / nu.e
    w0 = (1 - T) / (1 - nu.e)
    m1 = (w1 * Y).sum() / w1.sum()
    m0 = (w0 * Y).sum() / w0.sum()
    est = m1 - m0
    psi = w1 * (Y - m1) / w1.mean() - w0 * (Y - m0) / w0.mean() + est
    return _make("ipw", psi, est, groups)


def effective_sample_size(w: np.ndarray) -> float:
    return float(w.sum() ** 2 / np.sum(w**2))
