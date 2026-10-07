"""무작위 파일럿이 관측 추정의 편향을 잡는가 — 같은 세계 안에서.

숨은 교란(hunch)이 있는 세계에서 설비의 일부(pilot_share)만 점검을 동전 던지기로 배정한다.
  · 나머지 설비의 로그로 AIPW 를 돌리면 숨은 교란 때문에 틀린다.
  · 파일럿 설비는 숨은 교란이 처치와 무관하므로 단순 평균 차이가 (넓지만) 맞는다.
  · 두 추정이 모순되는지(관측 추정이 파일럿 구간 밖인지)가 "관측 로그를 믿어도 되는가"에 대한 가장 직접적인 시험이다.
창이 겹치지 않도록 4주마다 한 시점만 쓴다.
"""

from __future__ import annotations

import numpy as np

from ..audit import run_audit
from ..causal import estimators as est
from ..causal.data import prepare
from ..sim.generate import simulate
from ..sim.world import WorldConfig


def pilot_demo(
    n_sites: int = 24, hunch: float = 1.0, pilot_share: float = 0.4, seed: int = 11, weeks: int = 156
) -> dict:
    cfg = WorldConfig(
        seed=seed, n_sites=n_sites, weeks=weeks, burn_in=78, hunch=hunch, pilot_share=pilot_share
    )
    w = simulate(cfg, truth_m=48)
    L, T = w.log, w.truth
    pilot = L["pilot"].to_numpy()
    # 1) 관측 로그(파일럿 설비 제외) 감사
    obs_log = L.loc[~pilot].reset_index(drop=True)
    fr_obs = prepare(obs_log)
    tau_obs = T["tau"].to_numpy()[~pilot][fr_obs.idx]
    audit = run_audit(obs_log, truth_ate=float(-tau_obs.mean()), n_folds=3, with_sensitivity=False)
    # 2) 파일럿 분석: 파일럿 설비, 창이 겹치지 않는 시점
    sel = pilot & L["y"].notna().to_numpy() & ~L["due"].to_numpy() & (L["week"].to_numpy() % cfg.horizon == 0)
    sub = L.loc[sel]
    tau_p = T["tau"].to_numpy()[sel]
    e = est.naive(sub["treated"].to_numpy(), sub["y"].to_numpy(), sub["asset"].to_numpy())
    # 같은 파일럿 데이터에 AIPW 를 쓰면 구간이 좁아지는가 (무작위이므로 편향은 없다)
    obs = audit["estimates"]["aipw"]
    contradicts = bool(obs["averted"] < -e.hi or obs["averted"] > -e.lo)
    return {
        "config": {
            "n_sites": n_sites,
            "hunch": hunch,
            "pilot_share": pilot_share,
            "weeks": weeks,
            "pilot_visit_rate": cfg.pilot_visit_rate,
        },
        "n_pilot_assets": int(L.loc[pilot, "asset"].nunique()),
        "n_pilot_windows": int(len(sub)),
        "n_pilot_treated": int(sub["treated"].sum()),
        "truth_pilot_averted": float(tau_p.mean()),
        "truth_obs_averted": float(tau_obs.mean()),
        "pilot_estimate": {**e.to_dict()},
        "observational_aipw": audit["estimates"]["aipw"],
        "observational_naive": audit["estimates"]["naive"],
        "observational_verdict": audit["verdict"],
        "negative_control": audit.get("negative_control"),
        "observational_contradicts_pilot": contradicts,
        "pilot_ci_includes_zero": bool(e.lo <= 0 <= e.hi),
        "pilot_rows_used": int(len(np.unique(sub["asset"]))),
    }
