"""Parse Rosenthal GAIRA spreadsheet JSON into a normalized framework schema."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

WORKSHEET_KEYS: dict[str, str] = {
    "AI Risk Levels E": "ai_risk_levels",
    "GAIRA Light E": "gaira_light",
    "GAIRA Comprehensive E": "gaira_comprehensive",
    "AI Act Check E": "ai_act_check",
    "AI Act - Four Questions": "ai_act_four_questions",
    "Compliance Check E": "compliance_check",
    "ROAIA E": "roaia",
}

YES_NO_OPTIONS = ["Yes", "No", "N/A", "Unknown"]
RISK_LEVEL_OPTIONS = ["Low", "Medium", "High", "Very high"]
PROCEED_OPTIONS = [
    "Proceed as planned",
    "Proceed with conditions",
    "Do not proceed",
    "Further review required",
]


def _cell(row: list[Any], index: int) -> Any:
    if index < len(row):
        return row[index]
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_question_id(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text or text.startswith("Step"):
            return None
        if text.endswith(":") and not re.match(r"^\d", text):
            return None
        if text in {"Answer", "Explanation:", "Instruction:", "Recommendation:"}:
            return None
        return text
    if isinstance(raw, (int, float)):
        major = int(raw)
        minor = round((raw - major) * 100)
        return f"{major}.{minor:02d}"
    return None


def _extract_step_id(label: str) -> str | None:
    match = re.match(r"Step\s+(\d+)\s*:", label, re.IGNORECASE)
    return match.group(1) if match else None


def _infer_answer_type(row: list[Any], module_key: str) -> str:
    answer_cell = _clean_text(_cell(row, 3))
    if answer_cell == "(select)":
        return "select"
    if module_key == "ai_risk_levels":
        return "boolean"
    if answer_cell and answer_cell not in {"(select)", "(please make all selections above)"}:
        return "text"
    label = _clean_text(_cell(row, 0)) or ""
    if label.endswith(":"):
        return "metadata"
    return "text"


def _default_options(answer_type: str, question_text: str) -> list[str]:
    if answer_type == "boolean":
        return ["Yes", "No"]
    if answer_type != "select":
        return []
    lower = question_text.lower()
    if "overall risk level" in lower:
        return RISK_LEVEL_OPTIONS
    if "decision on how to proceed" in lower or "decision on how to proceed" in lower:
        return PROCEED_OPTIONS
    if "will you do a dpia" in lower:
        return ["Yes", "No", "N/A"]
    return YES_NO_OPTIONS


def _is_metadata_row(row: list[Any]) -> bool:
    label = _clean_text(_cell(row, 0))
    if not label or label.startswith("Step"):
        return False
    if not label.endswith(":"):
        return False
    if normalize_question_id(label):
        return False
    return True


def parse_worksheet(module_key: str, rows: list[list[Any]]) -> dict[str, Any]:
    title: str | None = None
    version: str | None = None
    overview: str | None = None
    metadata_fields: list[dict[str, str]] = []
    steps: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []

    current_step: dict[str, Any] | None = None
    pending_instruction: str | None = None

    for row in rows:
        col0 = _cell(row, 0)
        col1 = _clean_text(_cell(row, 1))

        if title is None and isinstance(col0, str) and len(col0) > 10:
            title = col0
            continue
        if version is None and isinstance(col0, str) and col0.lower().startswith("version"):
            version = col0
            continue
        if overview is None and col1 and len(col1) > 200:
            overview = col1
            continue

        if isinstance(col0, str) and col0.startswith("Step "):
            step_id = _extract_step_id(col0)
            if step_id:
                current_step = {
                    "id": step_id,
                    "title": col1 or col0,
                    "instruction": pending_instruction,
                }
                steps.append(current_step)
                pending_instruction = None
            continue

        if col1 and col1.startswith("Instruction:"):
            pending_instruction = col1.removeprefix("Instruction:").strip()
            if current_step and not current_step.get("instruction"):
                current_step["instruction"] = pending_instruction
            continue

        if _is_metadata_row(row):
            metadata_fields.append(
                {
                    "key": _clean_text(col0).rstrip(":").lower().replace(" ", "_"),
                    "label": _clean_text(col0).rstrip(":"),
                    "example_value": _clean_text(_cell(row, 2)) or _clean_text(_cell(row, 3)),
                }
            )
            continue

        question_id = normalize_question_id(col0)
        if not question_id or not col1:
            continue

        answer_type = _infer_answer_type(row, module_key)
        if answer_type == "metadata":
            continue

        explanation = _clean_text(_cell(row, 5))
        questions.append(
            {
                "id": question_id,
                "text": col1,
                "step_id": current_step["id"] if current_step else None,
                "answer_type": answer_type,
                "explanation": explanation,
                "options": _default_options(answer_type, col1),
            }
        )

    return {
        "key": module_key,
        "title": title or module_key,
        "version": version,
        "overview": overview,
        "metadata_fields": metadata_fields,
        "steps": steps,
        "questions": questions,
    }


def parse_roaia(rows: list[list[Any]]) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        if _cell(row, 0) == "ID":
            columns = [_clean_text(_cell(row, i)) for i in range(len(row)) if _clean_text(_cell(row, i))]
            break
    return {
        "key": "roaia",
        "title": "Records of AI Activities (ROAIA)",
        "columns": columns,
    }


def parse_gaira_file(source_path: Path) -> dict[str, Any]:
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    modules: dict[str, Any] = {}

    for sheet_name, module_key in WORKSHEET_KEYS.items():
        rows = raw.get(sheet_name)
        if not rows:
            continue
        if module_key == "roaia":
            modules[module_key] = parse_roaia(rows)
        else:
            modules[module_key] = parse_worksheet(module_key, rows)

    return {
        "source": source_path.name,
        "version": modules.get("gaira_light", {}).get("version")
        or modules.get("ai_risk_levels", {}).get("version"),
        "modules": modules,
    }


def write_framework(source_path: Path, output_path: Path) -> dict[str, Any]:
    framework = parse_gaira_file(source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(framework, indent=2, ensure_ascii=False), encoding="utf-8")
    return framework
