"""Load normalized GAIRA framework from bundled JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

FRAMEWORK_PATH = Path(__file__).resolve().parents[2] / "data" / "gaira" / "framework_v1.json"
SOURCE_JSON_PATH = (
    Path(__file__).resolve().parents[4] / "GAIRA" / "Rosenthal_GAIRA.json"
)
# parents[4]: gaira -> services -> app -> backend -> Security-Compliance


class GairaFramework:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def version(self) -> str | None:
        return self.data.get("version")

    @property
    def modules(self) -> dict[str, Any]:
        return self.data.get("modules", {})

    def get_module(self, key: str) -> dict[str, Any] | None:
        return self.modules.get(key)

    def list_modules(self) -> list[dict[str, str]]:
        return [
            {
                "key": key,
                "title": module.get("title", key),
                "question_count": len(module.get("questions", [])),
            }
            for key, module in self.modules.items()
            if key != "roaia"
        ]

    def questions_for_module(self, key: str) -> list[dict[str, Any]]:
        module = self.get_module(key)
        if not module:
            return []
        return list(module.get("questions", []))


@lru_cache(maxsize=1)
def get_gaira_framework() -> GairaFramework:
    if not FRAMEWORK_PATH.exists():
        from app.services.gaira.parser import write_framework

        if SOURCE_JSON_PATH.exists():
            write_framework(SOURCE_JSON_PATH, FRAMEWORK_PATH)
        else:
            raise FileNotFoundError(
                f"GAIRA framework not found at {FRAMEWORK_PATH} and source missing at {SOURCE_JSON_PATH}"
            )
    data = json.loads(FRAMEWORK_PATH.read_text(encoding="utf-8"))
    return GairaFramework(data)


def reload_gaira_framework() -> GairaFramework:
    get_gaira_framework.cache_clear()
    return get_gaira_framework()
