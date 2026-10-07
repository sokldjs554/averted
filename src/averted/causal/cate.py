"""설비·주별 효과(CATE) 추정기 — 직접 구현.

  T-learner   μ1(x) − μ0(x)                                (가장 단순, 잡음이 크다)
  DR-learner  교차적합 AIPW 점수 Γ 를 X 로 회귀             (Kennedy 2023; 이중 강건 의사결과)
  shrunk      CATE 를 평균 효과 쪽으로 축소                  (추정기들이 "효과 0" 보다 못한 경우가 흔하다 — Yu 외 2025)

반환 값은 모두 `averted` 부호(막은 고장 확률 = −효과)다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from . import estimators as est
from . import nuisance as nu_mod


@dataclass
class CateModel:
    name: str
    models: object  # (m_e, m0, m1)
    reg: HistGradientBoostingRegressor | None
    ate: float  # 학습 구간 평균 (축소 중심)
    shrink: float = 1.0

    def predict(self, X: np.ndarray) -> np.ndarray:
        """막은 고장 확률의 예측 (클수록 점검 효과가 크다)."""
        if self.name == "t_learner":
            p = nu_mod.predict_models(self.models, X)
            raw = p.mu0 - p.mu1
        else:
            raw = -self.reg.predict(X)
        return self.shrink * raw + (1 - self.shrink) * (-self.ate)


def fit_t_learner(X, T, Y, seed: int = 0) -> CateModel:
    models = nu_mod.fit_models(X, T, Y, seed=seed)
    return CateModel("t_learner", models, None, ate=float(Y[T == 1].mean() - Y[T == 0].mean()))


def fit_dr_learner(
    X, T, Y, groups, n_folds: int = 5, seed: int = 0, depth: int = 3
) -> tuple[CateModel, np.ndarray]:
    """교차적합 점수로 CATE 회귀를 학습. 반환: (모형, 학습행의 교차적합 점수 Γ)."""
    nuis = nu_mod.crossfit(X, T, Y, groups, n_folds=n_folds, seed=seed)
    gamma = est.dr_scores(T, Y, nuis)
    reg = HistGradientBoostingRegressor(
        max_depth=depth,
        learning_rate=0.05,
        max_iter=140,
        min_samples_leaf=300,
        l2_regularization=5.0,
        random_state=seed,
    ).fit(X, gamma)
    models = nu_mod.fit_models(X, T, Y, seed=seed + 100)
    return CateModel("dr_learner", models, reg, ate=float(gamma.mean())), gamma


def with_shrink(model: CateModel, shrink: float) -> CateModel:
    return CateModel(model.name, model.models, model.reg, model.ate, shrink)


def select_shrink(model: CateModel, X_val, gamma_val, grid=(0.0, 0.25, 0.5, 0.75, 1.0)) -> float:
    """검증 구간의 DR 점수만으로 축소 정도를 고른다 (정답 없이 쓸 수 있는 R-loss 근사).

    점수 Γ 는 효과의 잡음 섞인 불편 추정치이므로, 예측 −Γ̂ 와의 제곱오차가 가장 작은 축소 정도를 택한다.
    """
    raw = -model.predict(X_val)  # 효과(음수=개선) 부호로 환산
    best, best_loss = 1.0, np.inf
    for s in grid:
        pred = s * raw + (1 - s) * model.ate
        loss = float(np.mean((gamma_val - pred) ** 2))
        if loss < best_loss:
            best, best_loss = s, loss
    return best
