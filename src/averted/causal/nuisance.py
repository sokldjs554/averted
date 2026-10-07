"""교란 모형(nuisance) — 처치 확률 e(x) 와 두 결과 모형 μ0(x), μ1(x) 를 교차적합으로 추정한다.

같은 설비의 여러 주가 학습과 예측에 동시에 들어가면 과적합된 예측이 추정량에 새어 들어가므로,
**설비 단위로** 접어서(GroupKFold) 접힘 밖 예측만 쓴다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

CLIP = (0.01, 0.99)


@dataclass
class Nuisance:
    e: np.ndarray  # 처치 확률 (잘린 값)
    e_raw: np.ndarray
    mu0: np.ndarray  # P(Y=1 | X, T=0)
    mu1: np.ndarray  # P(Y=1 | X, T=1)


def _gbm(seed: int, **kw) -> HistGradientBoostingClassifier:
    params = dict(
        max_depth=4,
        learning_rate=0.09,
        max_iter=140,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=seed,
    )
    params.update(kw)
    return HistGradientBoostingClassifier(**params)


def fit_models(X, T, Y, seed: int = 0):
    """전체 데이터로 (e, μ0, μ1) 모형을 적합해 돌려준다 (예측은 predict_models)."""
    m_e = _gbm(seed).fit(X, T)
    m0 = _gbm(seed + 1).fit(X[T == 0], Y[T == 0].astype(int))
    m1 = _gbm(seed + 2, min_samples_leaf=25, max_iter=110).fit(X[T == 1], Y[T == 1].astype(int))
    return m_e, m0, m1


def predict_models(models, X) -> Nuisance:
    m_e, m0, m1 = models
    e_raw = m_e.predict_proba(X)[:, 1]
    return Nuisance(
        e=np.clip(e_raw, *CLIP),
        e_raw=e_raw,
        mu0=m0.predict_proba(X)[:, 1],
        mu1=m1.predict_proba(X)[:, 1],
    )


def crossfit(X, T, Y, groups, n_folds: int = 5, seed: int = 0) -> Nuisance:
    """설비 단위 K-fold 교차적합 — 모든 행이 자신을 학습하지 않은 모형의 예측을 받는다."""
    n = len(T)
    e_raw = np.zeros(n)
    mu0 = np.zeros(n)
    mu1 = np.zeros(n)
    gkf = GroupKFold(n_splits=n_folds)
    for k, (tr, te) in enumerate(gkf.split(X, T, groups)):
        models = fit_models(X[tr], T[tr], Y[tr], seed=seed + 10 * k)
        pred = predict_models(models, X[te])
        e_raw[te], mu0[te], mu1[te] = pred.e_raw, pred.mu0, pred.mu1
    return Nuisance(e=np.clip(e_raw, *CLIP), e_raw=e_raw, mu0=mu0, mu1=mu1)
