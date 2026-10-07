"""점검 배분 정책 — 사이트·주마다 예산 K 개를 어떤 기준으로 고르는가, 그리고 그 가치를 어떻게 재는가.

가치 = "점검 100번당 막는 고장 수".
  · 정답 가치: 시뮬레이터가 아는 개별 효과 τ 의 합 (채점용)
  · 로그만으로 추정한 가치(OPE): 선택된 행들의 이중 강건 점수 Γ 의 합 — 정답 없이도 계산할 수 있다.
위험순 기준선은 "처치를 무시하고 고장 확률만 예측하는" 보통의 예지보전 모형이다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier


def fit_risk_model(X, Y, seed: int = 0) -> HistGradientBoostingClassifier:
    """처치 여부를 무시하고 4주 내 고장 확률만 예측 — 일반적인 예지보전 위험 모형."""
    return HistGradientBoostingClassifier(
        max_depth=4,
        learning_rate=0.09,
        max_iter=140,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=seed,
    ).fit(X, Y.astype(int))


def select_top_k(df: pd.DataFrame, score: str, k: int, group=("site", "week")) -> np.ndarray:
    """그룹(사이트·주)마다 score 상위 k 행의 위치(0..n-1)를 돌려준다. score 가 같으면 무작위 순서에 맡기지 않고 안정 정렬."""
    order = df.sort_values([*group, score], ascending=[True] * len(group) + [False], kind="mergesort")
    top = order.groupby(list(group), sort=False).head(k)
    return df.index.get_indexer(top.index)


def policy_values(
    df: pd.DataFrame,
    scores: dict[str, np.ndarray | pd.Series],
    k: int,
    tau: np.ndarray | None,
    gamma: np.ndarray | None,
) -> dict:
    """각 정책의 값을 계산한다. df 는 평가 행들(사이트·주·점수 열 포함), tau/gamma 는 같은 순서의 정답·DR 점수."""
    work = df[["site", "week"]].copy()
    n_groups = work.groupby(["site", "week"]).ngroups
    out = {}
    for name, s in scores.items():
        work["_s"] = np.asarray(s)
        pos = select_top_k(work.reset_index(drop=True), "_s", k)
        visits = len(pos)
        entry = {"visits": int(visits)}
        if tau is not None:
            entry["true_per100"] = float(100.0 * tau[pos].sum() / visits)
        if gamma is not None:
            entry["ope_per100"] = float(-100.0 * gamma[pos].sum() / visits)  # Γ 는 효과(음수=개선) 부호
        entry["n_groups"] = int(n_groups)
        out[name] = entry
    return out


def bootstrap_policy_ci(
    df: pd.DataFrame, score: np.ndarray, k: int, value: np.ndarray, n_boot: int = 300, seed: int = 0
) -> tuple[float, float]:
    """사이트·주 묶음 단위 부트스트랩으로 "점검 100번당" 값의 95% 구간."""
    work = df[["site", "week"]].reset_index(drop=True).copy()
    work["_s"] = np.asarray(score)
    work["_v"] = np.asarray(value)
    pos = select_top_k(work, "_s", k)
    sel = work.iloc[pos]
    groups = sel.groupby(["site", "week"])["_v"].agg(["sum", "count"]).to_numpy()
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), size=len(groups))
        vals.append(100.0 * groups[pick, 0].sum() / groups[pick, 1].sum())
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))
