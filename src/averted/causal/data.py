"""분석용 데이터 준비 — 로그(분석가가 볼 수 있는 표)에서 공변량 행렬 X, 처치 T, 결과 Y 를 만든다.

원칙: 정답(truth)과 숨은 손상 D 는 여기에 들어오지 않는다. 법정 점검 기한이 된 설비(due)는 처치가 달력으로 결정돼
처치 변이가 없으므로(겹침 위반) 분석 대상에서 빼고, 별도로 표시한다.

`LogSpec` 으로 열 이름을 매핑하면 시뮬레이터가 아닌 실제 로그(예: 유비스 마스터 점검·A/S 이력)도 같은 코드로 분석한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..sim.world import CATEGORIES

CAT_KEYS = [c.key for c in CATEGORIES]


@dataclass(frozen=True)
class LogSpec:
    """로그의 열 이름 매핑. 행 = (설비, 주) 한 건. 처치 = 그 주에 점검했는가, 결과 = 그 주부터 H주 안의 비계획 고장."""

    unit: str = "asset"
    time: str = "week"
    treatment: str = "treated"
    outcome: str = "y"
    site: str | None = "site"  # 사이트(고객사·건물) 열. 있으면 더미로 보정에 쓴다
    numeric: tuple[str, ...] = ("age", "crit", "grade_last", "wsv", "bd", "cmp", "open_wo")
    categorical: tuple[str, ...] = ("cat",)
    due: str | None = "due"  # 법정 점검 기한 여부(달력으로 처치가 결정되는 행) — 없으면 None
    prior_outcome: str | None = "y_prev"  # 처치 이전 구간의 같은 결과(음성 대조 결과) — 없으면 None
    category_levels: dict = field(default_factory=lambda: {"cat": CAT_KEYS})

    def required(self) -> list[str]:
        cols = [self.unit, self.time, self.treatment, self.outcome, *self.numeric, *self.categorical]
        if self.site:
            cols.append(self.site)
        return cols


DEFAULT_SPEC = LogSpec()


@dataclass
class Frame:
    """분석 대상 행들. 행 순서는 원래 로그의 부분집합 (idx 가 원래 행 번호)."""

    idx: np.ndarray
    X: np.ndarray
    T: np.ndarray
    Y: np.ndarray
    asset: np.ndarray
    week: np.ndarray
    site: np.ndarray
    names: list[str]
    y_prior: np.ndarray | None = None

    def __len__(self) -> int:
        return len(self.T)

    def subset(self, mask: np.ndarray) -> Frame:
        return Frame(
            self.idx[mask],
            self.X[mask],
            self.T[mask],
            self.Y[mask],
            self.asset[mask],
            self.week[mask],
            self.site[mask],
            self.names,
            None if self.y_prior is None else self.y_prior[mask],
        )

    def col(self, name: str) -> np.ndarray:
        return self.X[:, self.names.index(name)]


def design_matrix(
    log: pd.DataFrame, spec: LogSpec = DEFAULT_SPEC, include_site: bool = True, n_sites: int | None = None
):
    cols, names = [], []
    for c in spec.categorical:
        levels = spec.category_levels.get(c) or sorted(log[c].dropna().unique())
        for k in levels:
            cols.append((log[c] == k).to_numpy(dtype=np.float64))
            names.append(f"{c}_{k}")
    for c in spec.numeric:
        cols.append(log[c].to_numpy(dtype=np.float64))
        names.append(c)
    if include_site and spec.site:
        s = log[spec.site].to_numpy()
        levels = (
            range(int(n_sites if n_sites is not None else s.max() + 1))
            if np.issubdtype(s.dtype, np.integer)
            else sorted(set(s))
        )
        for lv in levels:
            cols.append((s == lv).astype(np.float64))
            names.append(f"site_{lv}")
    return np.column_stack(cols), names


def validate(log: pd.DataFrame, spec: LogSpec = DEFAULT_SPEC) -> None:
    missing = [c for c in spec.required() if c not in log.columns]
    if missing:
        raise ValueError(f"로그에 필요한 열이 없습니다: {missing}")
    t = log[spec.treatment].dropna().unique()
    if not set(np.asarray(t).tolist()) <= {0, 1}:
        raise ValueError("처치 열은 0/1 이어야 합니다")


def prepare(
    log: pd.DataFrame,
    spec: LogSpec = DEFAULT_SPEC,
    include_site: bool = True,
    drop_due: bool = True,
    n_sites: int | None = None,
) -> Frame:
    """결과가 아직 관측되지 않은 행(창이 데이터 밖)과 법정 점검 기한 행을 제외한다."""
    validate(log, spec)
    keep = log[spec.outcome].notna().to_numpy()
    if drop_due and spec.due and spec.due in log.columns:
        keep &= ~log[spec.due].to_numpy(dtype=bool)
    sub = log.loc[keep]
    X, names = design_matrix(sub, spec, include_site=include_site, n_sites=n_sites)
    site = sub[spec.site].to_numpy() if spec.site else np.zeros(len(sub), dtype=int)
    y_prior = None
    if spec.prior_outcome and spec.prior_outcome in sub.columns:
        y_prior = sub[spec.prior_outcome].to_numpy(dtype=np.float64)
    return Frame(
        idx=np.flatnonzero(keep),
        X=X,
        T=sub[spec.treatment].to_numpy(dtype=np.int8),
        Y=sub[spec.outcome].to_numpy(dtype=np.float64),
        asset=sub[spec.unit].to_numpy(),
        week=sub[spec.time].to_numpy(),
        site=site,
        names=names,
        y_prior=y_prior,
    )
