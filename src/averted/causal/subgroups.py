"""부분집단 효과 — DR 점수의 집단 평균과 군집 신뢰구간. 구간이 넓으면 "이 데이터로는 알 수 없음"으로 표시한다."""

from __future__ import annotations

import numpy as np

from . import estimators as est


def subgroup_effects(
    labels: np.ndarray, T, gamma: np.ndarray, groups: np.ndarray, min_treated: int = 150
) -> list[dict]:
    rows = []
    overall = est._make("all", gamma, gamma.mean(), groups)
    for lv in sorted(set(labels.tolist())):
        m = labels == lv
        e = est._make(str(lv), gamma[m], gamma[m].mean(), groups[m])
        n_t = int(T[m].sum())
        width = e.hi - e.lo
        informative = n_t >= min_treated and (e.hi < 0 or e.lo > 0 or width < 0.8 * abs(overall.effect) * 2)
        rows.append(
            {
                "label": str(lv),
                "n": int(m.sum()),
                "n_treated": n_t,
                "averted": -e.effect,
                "averted_lo": -e.hi,
                "averted_hi": -e.lo,
                "informative": bool(informative),
            }
        )
    return rows
