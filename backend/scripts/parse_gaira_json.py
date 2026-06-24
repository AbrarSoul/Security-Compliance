#!/usr/bin/env python3
"""Generate normalized GAIRA framework JSON from Rosenthal spreadsheet export."""

from pathlib import Path

from app.services.gaira.parser import write_framework


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    project_root = backend_root.parent
    source = project_root / "GAIRA" / "Rosenthal_GAIRA.json"
    output = backend_root / "app" / "data" / "gaira" / "framework_v1.json"
    framework = write_framework(source, output)
    modules = framework.get("modules", {})
    print(f"Wrote {output}")
    for key, module in modules.items():
        q_count = len(module.get("questions", []))
        print(f"  - {key}: {q_count} questions")


if __name__ == "__main__":
    main()
