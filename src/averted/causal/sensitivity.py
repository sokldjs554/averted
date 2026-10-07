"""미관측 교란에 대한 민감도 — 숨은 교란은 데이터로 없앨 수 없으니 "얼마나 강하면 결론이 뒤집히나"를 보여 준다.

벤치마크 방식(Cinelli–Hazlett 의 생각을 단순화): 관측된 공변량 묶음 하나를 일부러 빼고 다시 추정한다.
그 변수를 몰랐다면 추정이 얼마나 움직였나 = "그 정도로 강한 미관측 교란이 있다면 이만큼 움직일 수 있다"는 현실적 눈금.
이 눈금이 추정 효과보다 크면 결론이 숨은 교란 하나에 뒤집힐 수 있다는 뜻이다.
"""

from __future__ import annotations

from . import estimators as est
from . import nuisance as nu_mod
from .data import Frame

DEFAULT_GROUPS = {
    "민원·A/S 접수 (cmp)": ["cmp"],
    "직전 점검 판정·최근 고장 (grade_last, bd)": ["grade_last", "bd"],
    "연식·중요도 (age, crit)": ["age", "crit"],
    "수리 접수 여부 (open_wo)": ["open_wo"],
}


def benchmark_drop(
    fr: Frame, full: est.Estimate, groups: dict | None = None, n_folds: int = 3, seed: int = 0
) -> list[dict]:
    out = []
    for label, cols in (groups or DEFAULT_GROUPS).items():
        keep = [i for i, n in enumerate(fr.names) if n not in cols]
        if len(keep) == len(fr.names):
            continue
        nu = nu_mod.crossfit(fr.X[:, keep], fr.T, fr.Y, fr.asset, n_folds=n_folds, seed=seed)
        e = est.aipw(fr.T, fr.Y, fr.asset, nu)
        out.append({"group": label, "effect_without": e.effect, "shift": float(e.effect - full.effect)})
    return out


def tipping(full: est.Estimate, benchmarks: list[dict]) -> dict:
    """결론이 뒤집히는 데 필요한 미관측 편향(%p)과, 관측된 가장 강한 교란 묶음이 만든 이동량의 비교."""
    need_point = abs(full.effect)  # 점추정이 0 이 되려면
    need_ci = (
        abs(full.effect) - 1.96 * full.se if abs(full.effect) > 1.96 * full.se else 0.0
    )  # 구간이 0 을 포함하려면
    strongest = max((abs(b["shift"]) for b in benchmarks), default=0.0)
    return {
        "bias_to_zero_point": float(need_point),
        "bias_to_zero_ci": float(max(need_ci, 0.0)),
        "strongest_observed_shift": float(strongest),
        "fragile": bool(strongest >= max(need_ci, 0.0) and strongest > 0),
        "ratio": float(strongest / need_point) if need_point > 0 else float("inf"),
    }
