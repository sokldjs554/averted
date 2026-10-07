"""반응도 모형 — "점검 효과 = 위험 × 반응도" 구조로 효과를 적은 수의 모수로 추정한다.

설비·주별 효과를 아무 구조 없이 배우려면(DR-learner, 신경망) 로그가 매우 많아야 한다: 처치율이 낮고 결과가 드물어서
개별 점수의 잡음이 효과 크기보다 훨씬 크기 때문이다. 현장 직관은 단순하다 — 점검의 효과는 (그 설비가 점검 없이 고장날 확률) ×
(점검이 그 위험을 얼마나 줄이는가) 이고, 뒤의 "반응도"는 설비 종류와 수리 접수 여부 같은 몇 가지에 따라 달라진다.

    τ(x) = Σ_g 1[x ∈ g] · β_g · μ0(x) + β_o · open_wo · μ0(x) + β_0 + β_1 · μ0(x)

μ0(x) 는 점검하지 않았을 때의 고장 확률(결과 모형)이고, 계수는 교차적합 DR 점수 Γ 에 대한 최소제곱으로 구한다 (E[Γ|x] = τ(x) 이므로 불편).
모수가 20개 안팎이라 신뢰구간이 설비 단위 군집 부트스트랩으로 싸게 나온다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import Ridge

from .data import Frame


def modifier_columns(names: list[str], categorical_prefixes=("cat_",), binary=("open_wo",)) -> list[int]:
    return [i for i, n in enumerate(names) if n.startswith(categorical_prefixes) or n in binary]


def basis(X: np.ndarray, mu0: np.ndarray, mod_cols: list[int]) -> np.ndarray:
    M = X[:, mod_cols] * mu0[:, None]
    return np.hstack([M, np.ones((len(X), 1)), mu0[:, None]])


@dataclass
class ResponsivenessModel:
    mod_cols: list[int]
    coef: np.ndarray
    boot: np.ndarray | None  # (B, p) 군집 부트스트랩 계수
    names: list[str]

    @staticmethod
    def fit(
        fr: Frame, mu0: np.ndarray, gamma: np.ndarray, n_boot: int = 60, seed: int = 0, ridge: float = 1e-3
    ) -> ResponsivenessModel:
        mod_cols = modifier_columns(fr.names)
        B = basis(fr.X, mu0, mod_cols)
        coef = Ridge(alpha=ridge, fit_intercept=False).fit(B, gamma).coef_
        boot = None
        if n_boot:
            rng = np.random.default_rng(seed)
            uniq, inv = np.unique(fr.asset, return_inverse=True)
            # 군집 합산 통계량으로 부트스트랩을 싸게: 정규방정식 (BᵀB, Bᵀγ) 를 설비별로 미리 합산
            p = B.shape[1]
            G = len(uniq)
            BtB = np.zeros((G, p, p))
            Btg = np.zeros((G, p))
            order = np.argsort(inv, kind="stable")
            Bs, gs, invs = B[order], gamma[order], inv[order]
            bounds = np.flatnonzero(np.diff(invs)) + 1
            for k, (Bk, gk) in enumerate(zip(np.split(Bs, bounds), np.split(gs, bounds), strict=True)):
                BtB[k] = Bk.T @ Bk
                Btg[k] = Bk.T @ gk
            boots = []
            for _ in range(n_boot):
                pick = rng.integers(0, G, size=G)
                A = BtB[pick].sum(axis=0) + ridge * np.eye(p)
                boots.append(np.linalg.solve(A, Btg[pick].sum(axis=0)))
            boot = np.array(boots)
        names = [fr.names[i] for i in mod_cols] + ["const", "mu0"]
        return ResponsivenessModel(mod_cols, coef, boot, names)

    def averted(self, X: np.ndarray, mu0: np.ndarray) -> np.ndarray:
        """막은 고장 확률(= −효과)의 예측. 클수록 점검 효과가 크다."""
        return -(basis(X, mu0, self.mod_cols) @ self.coef)

    def averted_interval(
        self, X: np.ndarray, mu0: np.ndarray, level: float = 0.9
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.boot is None:
            raise ValueError("부트스트랩 계수가 없습니다")
        B = basis(X, mu0, self.mod_cols)
        draws = -(B @ self.boot.T)
        a = (1 - level) / 2
        return np.quantile(draws, a, axis=1), np.quantile(draws, 1 - a, axis=1)

    def multipliers(self) -> list[dict]:
        """사람이 읽는 표: 종류·수리 접수별 "위험 1 당 막는 고장" (= −β_g, 상수항·위험 항 제외)."""
        out = []
        base = float(self.coef[-1])  # μ0 항
        for n, c in zip(self.names[:-2], self.coef[:-2], strict=True):
            out.append({"name": n, "averted_per_risk": float(-(c + base))})
        return out
