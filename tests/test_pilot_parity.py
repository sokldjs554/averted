"""브라우저 포트(console/pilot.js)가 파이썬 계획기와 같은 값을 내는지 — 정적 데모는 이 JS 로 계산한다."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from averted.causal import pilot

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
def test_js_port_matches_python(tmp_path):
    rng = np.random.default_rng(0)
    cases = []
    for _ in range(40):
        base = float(rng.uniform(0.03, 0.3))
        eff = float(rng.uniform(0.3, 6.0))
        n_assets = int(rng.integers(20, 3000))
        weeks = int(rng.choice([8, 13, 26, 52, 104]))
        share = float(rng.choice([0.1, 0.3, 0.5]))
        icc = float(rng.choice([0.0, 0.02, 0.05]))
        p = pilot.plan(base, eff, n_assets, weeks, share, icc)
        cases.append(
            {
                "base_rate": base,
                "averted_pp": eff,
                "n_assets": n_assets,
                "weeks": weeks,
                "treat_share": share,
                "icc": icc,
                "power": p.power,
                "min_detectable_pp": p.min_detectable_pp,
                "required_weeks": pilot.required_weeks(base, eff, n_assets, share, icc),
                "required_assets": pilot.required_assets(base, eff, weeks, share, icc),
            }
        )
    f = tmp_path / "cases.json"
    f.write_text(json.dumps(cases))
    proc = subprocess.run(
        ["node", str(ROOT / "scripts" / "check_pilot_parity.cjs"), str(f)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout.strip().splitlines()[-1])["mismatches"] == 0
