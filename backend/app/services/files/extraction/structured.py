"""Extract structured/tabular file formats."""

from __future__ import annotations

import io
import json
from typing import Any
from xml.etree import ElementTree as ET

import pandas as pd
import yaml

from app.services.files.excel_io import read_xlsx_sheets
from app.services.files.extraction.types import ExtractedContent
from app.services.files.extraction.utils import (
    analyze_dataframe_quality,
    dataframe_to_records,
    dataframe_to_table,
    decode_text,
    local_tag,
    normalize_cell,
)


def extract_csv(content: bytes) -> ExtractedContent:
    df = pd.read_csv(io.BytesIO(content))
    quality = analyze_dataframe_quality(df)
    return ExtractedContent(
        file_type="csv",
        tables=[dataframe_to_table(df, "csv")],
        metadata={"encoding": "utf-8", "delimiter": ","},
        records=dataframe_to_records(df),
        structure={"headings": list(df.columns.astype(str)), "sections": [], "pages": [], "sheets": []},
        data_quality=quality,
    )


def extract_tsv(content: bytes) -> ExtractedContent:
    df = pd.read_csv(io.BytesIO(content), sep="\t")
    quality = analyze_dataframe_quality(df)
    return ExtractedContent(
        file_type="tsv",
        tables=[dataframe_to_table(df, "tsv")],
        metadata={"encoding": "utf-8", "delimiter": "\t"},
        records=dataframe_to_records(df),
        structure={"headings": list(df.columns.astype(str)), "sections": [], "pages": [], "sheets": []},
        data_quality=quality,
    )


def _quality_from_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return analyze_dataframe_quality(pd.DataFrame())
    df = pd.DataFrame(records)
    return analyze_dataframe_quality(df)


def extract_json(content: bytes) -> ExtractedContent:
    data = json.loads(decode_text(content))
    records: list[dict[str, Any]] = []
    structure: dict[str, Any] = {"headings": [], "sections": [], "pages": [], "sheets": []}

    if isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data):
            records = [{str(k): normalize_cell(v) for k, v in item.items()} for item in data]
            structure["headings"] = sorted({k for item in records[:100] for k in item})
        else:
            records = [{"value": normalize_cell(item)} for item in data]
            structure["headings"] = ["value"]
    elif isinstance(data, dict):
        records = [{str(k): normalize_cell(v) for k, v in data.items()}]
        structure["headings"] = list(data.keys())
    else:
        records = [{"value": normalize_cell(data)}]
        structure["headings"] = ["value"]

    quality = _quality_from_records(records)
    table = None
    if records:
        df = pd.DataFrame(records)
        table = dataframe_to_table(df, "json")

    return ExtractedContent(
        file_type="json",
        tables=[table] if table else [],
        metadata={"structure": type(data).__name__},
        records=records[:1000],
        structure=structure,
        data_quality=quality,
    )


def _extract_json_lines(content: bytes, file_type: str) -> ExtractedContent:
    records: list[dict[str, Any]] = []
    for line in decode_text(content).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            records.append({str(k): normalize_cell(v) for k, v in parsed.items()})

    quality = _quality_from_records(records)
    headings = sorted({k for item in records[:100] for k in item}) if records else []
    tables = []
    if records:
        tables = [dataframe_to_table(pd.DataFrame(records), file_type)]

    return ExtractedContent(
        file_type=file_type,
        tables=tables,
        metadata={"line_count": len(records)},
        records=records[:1000],
        structure={"headings": headings, "sections": [], "pages": [], "sheets": []},
        data_quality=quality,
    )


def extract_jsonl(content: bytes) -> ExtractedContent:
    return _extract_json_lines(content, "jsonl")


def extract_ndjson(content: bytes) -> ExtractedContent:
    return _extract_json_lines(content, "ndjson")


def _find_xml_records(root: ET.Element) -> list[ET.Element]:
    queue: list[ET.Element] = [root]
    while queue:
        element = queue.pop(0)
        children = list(element)
        if len(children) >= 2:
            tags = [local_tag(child.tag) for child in children]
            if len(set(tags)) == 1:
                return children
        queue.extend(children)
    return []


def extract_xml(content: bytes) -> ExtractedContent:
    root = ET.fromstring(decode_text(content))
    records: list[dict[str, Any]] = []
    record_elements = _find_xml_records(root)

    if record_elements:
        for element in record_elements:
            records.append({
                local_tag(child.tag): normalize_cell(child.text)
                for child in element
            })
    else:
        for idx, text in enumerate((t.strip() for t in root.itertext() if t.strip()), start=1):
            records.append({"line": idx, "text": text})

    quality = _quality_from_records(records) if records and "line" not in records[0] else None
    headings = sorted({k for item in records[:100] for k in item}) if records else []

    tables = []
    if records and "line" not in records[0]:
        tables = [dataframe_to_table(pd.DataFrame(records), "xml")]

    text_lines = [t.strip() for t in root.itertext() if t.strip()][:500]
    return ExtractedContent(
        file_type="xml",
        text_blocks=[{"text": t, "line": i} for i, t in enumerate(text_lines, start=1)],
        tables=tables,
        metadata={"root_tag": local_tag(root.tag), "record_count": len(records)},
        records=records[:1000],
        structure={"headings": headings, "sections": [local_tag(root.tag)], "pages": [], "sheets": []},
        data_quality=quality,
    )


def _extract_yaml(content: bytes, file_type: str) -> ExtractedContent:
    data = yaml.safe_load(decode_text(content))
    records: list[dict[str, Any]] = []
    headings: list[str] = []

    if isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data):
            records = [{str(k): normalize_cell(v) for k, v in item.items()} for item in data]
            headings = sorted({k for item in records[:100] for k in item})
        else:
            records = [{"value": normalize_cell(item)} for item in data]
            headings = ["value"]
    elif isinstance(data, dict):
        records = [{str(k): normalize_cell(v) for k, v in data.items()}]
        headings = list(data.keys())
    elif data is not None:
        records = [{"value": normalize_cell(data)}]
        headings = ["value"]

    quality = _quality_from_records(records) if records else analyze_dataframe_quality(pd.DataFrame())
    tables = []
    if records:
        tables = [dataframe_to_table(pd.DataFrame(records), file_type)]

    return ExtractedContent(
        file_type=file_type,
        tables=tables,
        metadata={"structure": type(data).__name__ if data is not None else "empty"},
        records=records[:1000],
        structure={"headings": headings, "sections": [], "pages": [], "sheets": []},
        data_quality=quality,
    )


def extract_yaml(content: bytes) -> ExtractedContent:
    return _extract_yaml(content, "yaml")


def extract_yml(content: bytes) -> ExtractedContent:
    return _extract_yaml(content, "yml")


def extract_xlsx(content: bytes) -> ExtractedContent:
    sheets = read_xlsx_sheets(content)
    all_records: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    sheet_names: list[str] = []
    total_rows = 0
    max_cols = 0

    for sheet_name, rows in sheets:
        sheet_names.append(sheet_name)
        if not rows:
            continue
        header = [normalize_cell(c) or f"column_{i}" for i, c in enumerate(rows[0])]
        data_rows = rows[1:] if len(rows) > 1 else []
        df = pd.DataFrame(
            [{header[i]: normalize_cell(row[i] if i < len(row) else "") for i in range(len(header))}
             for row in data_rows]
        )
        if df.empty and header:
            df = pd.DataFrame(columns=header)
        tables.append({
            **dataframe_to_table(df, sheet_name),
            "sheet": sheet_name,
        })
        sheet_records = dataframe_to_records(df)
        for rec in sheet_records:
            rec["_sheet"] = sheet_name
        all_records.extend(sheet_records)
        total_rows += len(data_rows)
        max_cols = max(max_cols, len(header))

    combined_df = pd.DataFrame(all_records) if all_records else pd.DataFrame()
    quality = analyze_dataframe_quality(combined_df) if not combined_df.empty else {
        "row_count": total_rows,
        "column_count": max_cols,
        "columns": [],
        "missing_values": {},
        "duplicate_rows": 0,
        "findings": [],
    }

    return ExtractedContent(
        file_type="xlsx",
        tables=tables,
        metadata={"sheet_count": len(sheets), "sheet_names": sheet_names},
        records=all_records[:1000],
        structure={
            "headings": list(combined_df.columns.astype(str)) if not combined_df.empty else [],
            "sections": [],
            "pages": [],
            "sheets": sheet_names,
        },
        data_quality=quality,
    )
