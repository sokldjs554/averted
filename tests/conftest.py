from __future__ import annotations

import pandas as pd
import pytest

from averted.sim.generate import simulate
from averted.sim.world import WorldConfig

# pandas 3 는 Copy-on-Write 가 기본이라 to_numpy() 가 읽기 전용 배열을 돌려준다.
# 로컬 pandas 2.x 에서도 같은 조건으로 시험해 그 차이가 CI 에서야 드러나지 않게 한다.
pd.options.mode.copy_on_write = True


@pytest.fixture(scope="session")
def tiny_cfg() -> WorldConfig:
    return WorldConfig(seed=5, n_sites=3, assets_min=60, assets_max=80, weeks=70, burn_in=40)


@pytest.fixture(scope="session")
def tiny(tiny_cfg):
    return simulate(tiny_cfg, truth_m=24)


@pytest.fixture(scope="session")
def toy_artifacts(tmp_path_factory):
    """작은 세계 하나를 끝까지 평가해 만든 산출물 폴더 — API·정적 빌드 테스트가 공유한다."""
    import json

    from averted.eval.protocol import run_scenario

    root = tmp_path_factory.mktemp("art")
    cfg = WorldConfig(seed=2, n_sites=3, assets_min=50, assets_max=60, weeks=96, burn_in=40)
    run_scenario(cfg, "toy", "시험용", out_dir=root / "scenarios", truth_m=16, ks=(4, 8), verbose=False)
    (root / "manifest.json").write_text(json.dumps({"version": "test", "built_at": "t"}))
    return root
