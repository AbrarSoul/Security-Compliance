"""Load NIST AI RMF control catalog from bundled JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTROLS_PATH = Path(__file__).resolve().parents[2] / "data" / "nist_ai_rmf" / "controls_v1.json"


class NistAiRmfFramework:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def version(self) -> str:
        return str(self.data.get("version", "1.0"))

    @property
    def profile(self) -> dict[str, Any]:
        return dict(self.data.get("profile", {}))

    @property
    def controls(self) -> list[dict[str, Any]]:
        return list(self.data.get("controls", []))

    def get_control(self, control_id: str) -> dict[str, Any] | None:
        for control in self.controls:
            if control.get("id") == control_id:
                return control
        return None

    def controls_for_function(self, function: str) -> list[dict[str, Any]]:
        fn = function.upper()
        return [c for c in self.controls if c.get("function") == fn]


@lru_cache(maxsize=1)
def get_nist_ai_rmf_framework() -> NistAiRmfFramework:
    if not CONTROLS_PATH.exists():
        raise FileNotFoundError(
            f"NIST AI RMF controls not found at {CONTROLS_PATH}. "
            "Run backend/scripts/generate_nist_controls.py"
        )
    data = json.loads(CONTROLS_PATH.read_text(encoding="utf-8"))
    return NistAiRmfFramework(data)


def reload_nist_ai_rmf_framework() -> NistAiRmfFramework:
    get_nist_ai_rmf_framework.cache_clear()
    return get_nist_ai_rmf_framework()
