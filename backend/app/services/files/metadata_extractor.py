import csv
import io
import json
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

import yaml

from app.core.config import get_settings
from app.services.files.supported_formats import (
    DELIMITED_DELIMITERS,
    DOCUMENT_EXTENSIONS,
    JSON_LINE_EXTENSIONS,
    SPREADSHEET_EXTENSIONS,
    TEXT_LIKE_EXTENSIONS,
    YAML_EXTENSIONS,
)
from app.services.files.document_text import document_lines
from app.services.files.excel_io import read_xlsx_sheets

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


def _local_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _find_xml_records(root: ET.Element) -> list[ET.Element]:
    queue: list[ET.Element] = [root]
    while queue:
        element = queue.pop(0)
        children = list(element)
        if len(children) >= 2:
            tags = [_local_tag(child.tag) for child in children]
            if len(set(tags)) == 1:
                return children
        queue.extend(children)
    return []


def extract_delimited_metadata(
    content: bytes, preview_rows: int, delimiter: str, format_name: str
) -> ExtractedMetadata:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return ExtractedMetadata(0, 0, [], [], {"format": format_name, "encoding": "utf-8"})

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
        extra_json={"format": format_name, "has_header": True},
    )


def extract_csv_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    return extract_delimited_metadata(content, preview_rows, ",", "csv")


def extract_tsv_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    return extract_delimited_metadata(content, preview_rows, "\t", "tsv")


def _structured_metadata_from_records(
    records: list[dict[str, Any]], preview_rows: int, format_name: str
) -> ExtractedMetadata:
    if not records:
        return ExtractedMetadata(0, 0, [], [], {"format": format_name, "structure": "array"})

    keys: set[str] = set()
    for item in records[:100]:
        keys.update(item.keys())
    columns = sorted(keys)
    schema = [{"name": k, "inferred_type": "mixed"} for k in columns]
    preview = records[:preview_rows]
    return ExtractedMetadata(
        row_count=len(records),
        column_count=len(columns),
        schema_json=schema,
        preview_json=preview,
        extra_json={"format": format_name, "structure": "array_of_objects"},
    )


def extract_json_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list):
        if not data:
            return ExtractedMetadata(0, 0, [], [], {"format": "json", "structure": "array"})

        if all(isinstance(item, dict) for item in data):
            return _structured_metadata_from_records(data, preview_rows, "json")

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


def extract_jsonl_metadata(content: bytes, preview_rows: int, format_name: str) -> ExtractedMetadata:
    records: list[dict[str, Any]] = []
    for line in content.decode("utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                records.append(parsed)
    return _structured_metadata_from_records(records, preview_rows, format_name)


def extract_yaml_metadata(content: bytes, preview_rows: int, format_name: str) -> ExtractedMetadata:
    data = yaml.safe_load(content.decode("utf-8", errors="replace"))

    if isinstance(data, list):
        if not data:
            return ExtractedMetadata(0, 0, [], [], {"format": format_name, "structure": "array"})
        if all(isinstance(item, dict) for item in data):
            return _structured_metadata_from_records(data, preview_rows, format_name)
        return ExtractedMetadata(
            row_count=len(data),
            column_count=1,
            schema_json=[{"name": "value", "inferred_type": type(data[0]).__name__}],
            preview_json=data[:preview_rows],
            extra_json={"format": format_name, "structure": "array"},
        )

    if isinstance(data, dict):
        return ExtractedMetadata(
            row_count=1,
            column_count=len(data),
            schema_json=[{"name": k, "inferred_type": type(v).__name__} for k, v in data.items()],
            preview_json=data,
            extra_json={"format": format_name, "structure": "object"},
        )

    return ExtractedMetadata(
        row_count=1,
        column_count=1,
        schema_json=[{"name": "value", "inferred_type": type(data).__name__}],
        preview_json=data,
        extra_json={"format": format_name, "structure": "scalar"},
    )


def extract_xml_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    root = ET.fromstring(content.decode("utf-8", errors="replace"))
    records = _find_xml_records(root)

    if records:
        columns: set[str] = set()
        for record in records[:100]:
            for child in record:
                columns.add(_local_tag(child.tag))
        sorted_columns = sorted(columns)
        schema = [{"name": col, "inferred_type": "string"} for col in sorted_columns]

        preview = []
        for record in records[:preview_rows]:
            row = {
                _local_tag(child.tag): (child.text or "").strip()
                for child in record
            }
            preview.append(row)

        return ExtractedMetadata(
            row_count=len(records),
            column_count=len(sorted_columns),
            schema_json=schema,
            preview_json=preview,
            extra_json={"format": "xml", "structure": "records", "root_tag": _local_tag(root.tag)},
        )

    lines = [text.strip() for text in root.itertext() if text.strip()]
    return ExtractedMetadata(
        row_count=len(lines),
        column_count=None,
        schema_json=[{"name": "text", "inferred_type": "string"}],
        preview_json=lines[:preview_rows],
        extra_json={"format": "xml", "structure": "text_nodes", "root_tag": _local_tag(root.tag)},
    )


def extract_txt_metadata(content: bytes, preview_rows: int, format_name: str = "txt") -> ExtractedMetadata:
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
            "format": format_name,
            "line_count": len(lines),
            "non_empty_line_count": len(non_empty),
            "char_count": len(text),
        },
    )


def extract_document_metadata(
    content: bytes, preview_rows: int, file_type: str
) -> ExtractedMetadata:
    lines, extra = document_lines(content, file_type)
    return ExtractedMetadata(
        row_count=len(lines),
        column_count=None,
        schema_json=[{"name": "line", "inferred_type": "string"}],
        preview_json=lines[:preview_rows],
        extra_json=extra,
    )


def _tabular_metadata_from_rows(
    rows: list[list[str]], preview_rows: int, format_name: str, extra: dict[str, Any]
) -> ExtractedMetadata:
    if not rows:
        return ExtractedMetadata(0, 0, [], [], extra)

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
        extra_json=extra,
    )


def extract_xlsx_metadata(content: bytes, preview_rows: int) -> ExtractedMetadata:
    sheets = read_xlsx_sheets(content)
    if not sheets:
        return ExtractedMetadata(
            0,
            0,
            [],
            [],
            {"format": "xlsx", "sheet_count": 0, "sheet_names": []},
        )

    sheet_names = [name for name, _ in sheets]
    total_rows = sum(max(len(rows) - 1, 0) for _, rows in sheets)
    max_columns = max(len(rows[0]) for _, rows in sheets)

    primary_name, primary_rows = sheets[0]
    primary = _tabular_metadata_from_rows(
        primary_rows,
        preview_rows,
        "xlsx",
        {
            "format": "xlsx",
            "sheet_count": len(sheets),
            "sheet_names": sheet_names,
            "primary_sheet": primary_name,
        },
    )
    return ExtractedMetadata(
        row_count=total_rows,
        column_count=max_columns,
        schema_json=primary.schema_json,
        preview_json=primary.preview_json,
        extra_json=primary.extra_json,
    )


def extract_metadata(file_type: str, content: bytes) -> ExtractedMetadata:
    preview_rows = settings.metadata_preview_rows
    if file_type == "csv":
        return extract_csv_metadata(content, preview_rows)
    if file_type == "tsv":
        return extract_tsv_metadata(content, preview_rows)
    if file_type == "json":
        return extract_json_metadata(content, preview_rows)
    if file_type in JSON_LINE_EXTENSIONS:
        return extract_jsonl_metadata(content, preview_rows, file_type)
    if file_type in YAML_EXTENSIONS:
        return extract_yaml_metadata(content, preview_rows, file_type)
    if file_type == "xml":
        return extract_xml_metadata(content, preview_rows)
    if file_type in TEXT_LIKE_EXTENSIONS:
        return extract_txt_metadata(content, preview_rows, file_type)
    if file_type in DOCUMENT_EXTENSIONS:
        return extract_document_metadata(content, preview_rows, file_type)
    if file_type in SPREADSHEET_EXTENSIONS:
        return extract_xlsx_metadata(content, preview_rows)
    raise ValueError(f"Unsupported file type: {file_type}")
