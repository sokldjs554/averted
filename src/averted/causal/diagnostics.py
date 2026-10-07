"""식별 가능성 진단 — "이 로그로 효과를 말해도 되는가"를 추정 전에, 그리고 추정과 함께 점검한다.

겹침(overlap)      처치 확률이 0 이나 1 에 붙은 행이 많으면 그 행들의 반사실은 데이터에 없다.
균형(balance)      가중 후 처치군과 대조군의 공변량이 비슷해졌는가 (표준화 평균 차이 SMD, 0.1 이하가 관례).
음성 대조 결과      점검이 원인이 될 수 없는 결과(점검 이전 구간의 고장)에 "효과"가 나오면 숨은 교란이 있다는 신호.
"""

from __future__ import annotations

import numpy as np

from . import estimators as est
from . import nuisance as nu_mod
from .data import Frame


def overlap(nu: nu_mod.Nuisance, T: np.ndarray, bins: int = 20) -> dict:
    e = nu.e_raw
    edges = np.linspace(0, 1, bins + 1)
    h1, _ = np.histogram(e[T == 1], bins=edges)
    h0, _ = np.histogram(e[T == 0], bins=edges)
    w1 = T / nu.e
    w0 = (1 - T) / (1 - nu.e)
    ess_t = est.effective_sample_size(w1[T == 1])
    ess_c = est.effective_sample_size(w0[T == 0])
    return {
        "share_below_1pct": float(np.mean(e < 0.01)),
        "share_above_99pct": float(np.mean(e > 0.99)),
        "share_extreme": float(np.mean((e < 0.01) | (e > 0.99))),
        "treated_share": float(T.mean()),
        "e_quantiles": {str(q): float(np.quantile(e, q)) for q in (0.01, 0.1, 0.5, 0.9, 0.99)},
        "hist_edges": edges.tolist(),
        "hist_treated": h1.tolist(),
        "hist_control": h0.tolist(),
        "ess_treated": ess_t,
        "ess_control": ess_c,
        "ess_ratio_treated": float(ess_t / max(int(T.sum()), 1)),
        "ess_ratio_control": float(ess_c / max(int((1 - T).sum()), 1)),
        "n_treated": int(T.sum()),
        "n_control": int((1 - T).sum()),
    }


def _smd(x, T, w=None):
    if w is None:
        w = np.ones_like(x)
    w1, w0 = w * T, w * (1 - T)
    m1 = np.sum(w1 * x) / np.sum(w1)
    m0 = np.sum(w0 * x) / np.sum(w0)
    v1 = np.sum(w1 * (x - m1) ** 2) / np.sum(w1)
    v0 = np.sum(w0 * (x - m0) ** 2) / np.sum(w0)
    sd = np.sqrt((v1 + v0) / 2)
    return float((m1 - m0) / sd) if sd > 0 else 0.0


def balance(fr: Frame, nu: nu_mod.Nuisance) -> list[dict]:
    """공변량별 SMD (원자료 / 역확률 가중 후). 사이트 더미는 묶어서 최댓값만 본다."""
    w = fr.T / nu.e + (1 - fr.T) / (1 - nu.e)
    rows = []
    site_raw, site_w = [], []
    for j, name in enumerate(fr.names):
        x = fr.X[:, j]
        if x.std() == 0:
            continue
        raw, wt = _smd(x, fr.T), _smd(x, fr.T, w)
        if name.startswith("site_"):
            site_raw.append(abs(raw))
            site_w.append(abs(wt))
            continue
        rows.append({"name": name, "smd_raw": raw, "smd_weighted": wt})
    if site_raw:
        rows.append({"name": "site (최대)", "smd_raw": max(site_raw), "smd_weighted": max(site_w)})
    return rows


def negative_control(fr: Frame, n_folds: int = 5, seed: int = 0) -> dict | None:
    """처치 이전 구간의 결과(y_prior)에 대한 AIPW "효과" — 0 이어야 한다."""
    if fr.y_prior is None:
        return None
    ok = ~np.isnan(fr.y_prior)
    if ok.sum() < 500:
        return None
    sub = fr.subset(ok)
    nu = nu_mod.crossfit(sub.X, sub.T, sub.y_prior, sub.asset, n_folds=n_folds, seed=seed)
    e = est.aipw(sub.T, sub.y_prior, sub.asset, nu)
    z = e.effect / e.se if e.se > 0 else 0.0
    return {"effect": e.effect, "se": e.se, "lo": e.lo, "hi": e.hi, "z": float(z), "flag": bool(abs(z) > 2.0)}
