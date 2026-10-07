"""정적 데모 빌드 — 콘솔이 읽는 경로마다 파일이 구워지고, 라이브 API 와 같은 응답인가."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from averted.api import main as api
from averted.api.store import Store

ROOT = Path(__file__).resolve().parents[1]


def test_static_build_matches_live_api(toy_artifacts, tmp_path):
    out = tmp_path / "demo"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_static_demo.py"),
            "--out",
            str(out),
            "--artifacts",
            str(toy_artifacts),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    html = (out / "index.html").read_text()
    assert "window.AVERTED_STATIC = true" in html and "정적 데모" in html
    # app.js 가 정적 모드에서 읽는 경로: /v1/scenarios, /v1/scenarios/{id}, /v1/schema, /version
    for name in ("v1_scenarios", "v1_scenarios_toy", "v1_schema", "version"):
        assert (out / "api" / f"{name}.json").exists(), name
    api.store = Store(toy_artifacts)
    live = TestClient(api.app).get("/v1/scenarios/toy").json()
    baked = json.loads((out / "api" / "v1_scenarios_toy.json").read_text())
    assert baked == live
    for f in ("style.css", "charts.js", "pilot.js", "app.js", ".nojekyll"):
        assert (out / f).exists(), f
