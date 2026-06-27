import csv
import io
import json
from typing import Any

from app.core.config import get_settings
from app.services.scanner.types import CellValue, ColumnSample

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

    columns: dict[str, list[CellValue]] = {name: [] for name in header}
    for row_offset, row in enumerate(data_rows):
        # Row 1 is the header; first data row is row 2 (spreadsheet-style).
        row_index = row_offset + 2
        for i, name in enumerate(header):
            columns[name].append(
                CellValue(index=row_index, value=_normalize_cell(row[i] if i < len(row) else ""))
            )

    return [
        ColumnSample(name=n, cells=v, location_type="row")
        for n, v in columns.items()
    ]


def load_json_columns(content: bytes, max_rows: int) -> list[ColumnSample]:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        keys: set[str] = set()
        for item in data[:max_rows]:
            keys.update(item.keys())
        columns: dict[str, list[CellValue]] = {k: [] for k in sorted(keys)}
        for record_idx, item in enumerate(data[:max_rows], start=1):
            for key in columns:
                columns[key].append(
                    CellValue(index=record_idx, value=_normalize_cell(item.get(key)))
                )
        return [
            ColumnSample(name=n, cells=v, location_type="record")
            for n, v in columns.items()
        ]

    if isinstance(data, dict):
        return [
            ColumnSample(
                name=k,
                cells=[CellValue(index=1, value=_normalize_cell(v))],
                location_type="field",
            )
            for k, v in data.items()
        ]

    return [
        ColumnSample(
            name="value",
            cells=[CellValue(index=1, value=_normalize_cell(data))],
            location_type="field",
        )
    ]


def load_txt_columns(content: bytes, max_rows: int) -> list[ColumnSample]:
    text = content.decode("utf-8", errors="replace")
    cells: list[CellValue] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        if line_num > max_rows:
            break
        stripped = line.strip()
        if stripped:
            cells.append(CellValue(index=line_num, value=stripped))
    return [ColumnSample(name="line", cells=cells, location_type="line")]


def load_dataset_columns(file_type: str, content: bytes) -> list[ColumnSample]:
    max_rows = settings.scan_max_sample_rows
    if file_type == "csv":
        return load_csv_columns(content, max_rows)
    if file_type == "json":
        return load_json_columns(content, max_rows)
    if file_type == "txt":
        return load_txt_columns(content, max_rows)
    raise ValueError(f"Unsupported file type: {file_type}")
