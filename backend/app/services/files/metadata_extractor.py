import csv
import io
import json
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

settings = get_settings()


@dataclass
class ExtractedMetadata:
    row_count: int | None
    column_count: int | None
    schema_json: list[dict[str, str]] | dict[str, Any] | None
    preview_json: list | dict | str | None
    extra_json: dict[str, Any] | None


def _infer_type(values: list[str]) -> str:
    if not values:
        return "unknown"
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "string"

    if all(v.isdigit() for v in non_empty):
        return "integer"
    if all(_is_float(v) for v in non_empty):
        return "float"
    if all(v.lower() in ("true", "false") for v in non_empty):
        return "boolean"
    return "string"


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_csv_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return ExtractedMetadata(0, 0, [], [], {"encoding": "utf-8"})

    header = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    columns = [col.strip() or f"column_{i}" for i, col in enumerate(header)]

    schema = []
    for i, col in enumerate(columns):
        samples = [row[i] if i < len(row) else "" for row in data_rows[:100]]
        schema.append({"name": col, "inferred_type": _infer_type(samples)})

    preview = []
    for row in data_rows[:preview_rows]:
        preview.append({columns[i]: row[i] if i < len(row) else "" for i in range(len(columns))})

    return ExtractedMetadata(
        row_count=len(data_rows),
        column_count=len(columns),
        schema_json=schema,
        preview_json=preview,
        extra_json={"format": "csv", "has_header": True},
    )


def extract_json_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list):
        if not data:
            return ExtractedMetadata(0, 0, [], [], {"format": "json", "structure": "array"})

        if all(isinstance(item, dict) for item in data):
            keys: set[str] = set()
            for item in data[:100]:
                keys.update(item.keys())
            columns = sorted(keys)
            schema = [{"name": k, "inferred_type": "mixed"} for k in columns]
            preview = data[:preview_rows]
            return ExtractedMetadata(
                row_count=len(data),
                column_count=len(columns),
                schema_json=schema,
                preview_json=preview,
                extra_json={"format": "json", "structure": "array_of_objects"},
            )

        return ExtractedMetadata(
            row_count=len(data),
            column_count=1,
            schema_json=[{"name": "value", "inferred_type": type(data[0]).__name__}],
            preview_json=data[:preview_rows],
            extra_json={"format": "json", "structure": "array"},
        )

    if isinstance(data, dict):
        return ExtractedMetadata(
            row_count=1,
            column_count=len(data),
            schema_json=[{"name": k, "inferred_type": type(v).__name__} for k, v in data.items()],
            preview_json=data,
            extra_json={"format": "json", "structure": "object"},
        )

    return ExtractedMetadata(
        row_count=1,
        column_count=1,
        schema_json=[{"name": "value", "inferred_type": type(data).__name__}],
        preview_json=data,
        extra_json={"format": "json", "structure": "scalar"},
    )


def extract_txt_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()
    non_empty = [ln for ln in lines if ln.strip()]

    preview = lines[:preview_rows]
    return ExtractedMetadata(
        row_count=len(lines),
        column_count=None,
        schema_json=[{"name": "line", "inferred_type": "string"}],
        preview_json=preview,
        extra_json={
            "format": "txt",
            "line_count": len(lines),
            "non_empty_line_count": len(non_empty),
            "char_count": len(text),
        },
    )


def extract_metadata(file_type: str, content: bytes) -> ExtractedMetadata:
    preview_rows = settings.metadata_preview_rows
    if file_type == "csv":
        return extract_csv_metadata(content, preview_rows)
    if file_type == "json":
        return extract_json_metadata(content, preview_rows)
    if file_type == "txt":
        return extract_txt_metadata(content, preview_rows)
    raise ValueError(f"Unsupported file type: {file_type}")
