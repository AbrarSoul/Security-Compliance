import csv
import io
import json
from typing import Any

from app.core.config import get_settings
from app.services.scanner.types import ColumnSample

settings = get_settings()


def _normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_csv_columns(content: bytes, max_rows: int) -> list[ColumnSample]:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []

    header = [col.strip() or f"column_{i}" for i, col in enumerate(rows[0])]
    data_rows = rows[1 : max_rows + 1] if len(rows) > 1 else []

    columns: dict[str, list[str]] = {name: [] for name in header}
    for row in data_rows:
        for i, name in enumerate(header):
            columns[name].append(_normalize_cell(row[i] if i < len(row) else ""))

    return [ColumnSample(name=n, values=v) for n, v in columns.items()]


def load_json_columns(content: bytes, max_rows: int) -> list[ColumnSample]:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        keys: set[str] = set()
        for item in data[:max_rows]:
            keys.update(item.keys())
        columns: dict[str, list[str]] = {k: [] for k in sorted(keys)}
        for item in data[:max_rows]:
            for key in columns:
                columns[key].append(_normalize_cell(item.get(key)))
        return [ColumnSample(name=n, values=v) for n, v in columns.items()]

    if isinstance(data, dict):
        return [ColumnSample(name=k, values=[_normalize_cell(v)]) for k, v in data.items()]

    return [ColumnSample(name="value", values=[_normalize_cell(data)])]


def load_txt_columns(content: bytes, max_rows: int) -> list[ColumnSample]:
    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()[:max_rows]
    return [ColumnSample(name="line", values=[ln.strip() for ln in lines if ln.strip()])]


def load_dataset_columns(file_type: str, content: bytes) -> list[ColumnSample]:
    max_rows = settings.scan_max_sample_rows
    if file_type == "csv":
        return load_csv_columns(content, max_rows)
    if file_type == "json":
        return load_json_columns(content, max_rows)
    if file_type == "txt":
        return load_txt_columns(content, max_rows)
    raise ValueError(f"Unsupported file type: {file_type}")
