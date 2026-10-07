"""산출물 저장소 — artifacts/ 의 JSON 을 읽어 API 가 서빙한다. 시나리오 계산은 오프라인(scripts/run_all.py)에서 끝난다."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


def artifact_dir() -> Path:
    return Path(os.environ.get("AVERTED_ARTIFACT_DIR", "artifacts"))


class Store:
    def __init__(self, root: Path | None = None):
        self.root = root or artifact_dir()

    def _read(self, rel: str):
        p = self.root / rel
        if not p.exists():
            return None
        return json.loads(p.read_text())

    @lru_cache(maxsize=64)  # noqa: B019
    def scenario(self, sid: str) -> dict | None:
        if not sid.isidentifier():
            return None
        return self._read(f"scenarios/{sid}.json")

    def scenario_ids(self) -> list[str]:
        d = self.root / "scenarios"
        return sorted(p.stem for p in d.glob("*.json")) if d.exists() else []

    def artifact(self, name: str):
        if name not in {"manifest", "learning_curve", "coverage", "hunch_sweep", "pilot_demo"}:
            return None
        return self._read(f"{name}.json")
