"""Shared helpers for file extraction."""

from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd

DATE_LIKE_PATTERN = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    r"|\d{4}-\d{2}-\d{2}T"
)

MAX_DQ_LOCATIONS = 10


def _is_missing(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def _file_row_number(df_index: int) -> int:
    """1-based row in file (row 1 = header)."""
    return int(df_index) + 2


def _row_preview(df: pd.DataFrame, row_idx: int, highlight_col: str | None = None) -> str:
    parts: list[str] = []
    for col in df.columns:
        val = normalize_cell(df.at[row_idx, col])
        label = str(col)
        if highlight_col and str(col) == highlight_col:
            parts.append(f"{label}=(empty)")
        elif val:
            parts.append(f"{label}={val[:40]}")
    return ", ".join(parts[:6]) if parts else "(empty row)"


def decode_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def local_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def normalize_cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def is_date_like(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    return bool(DATE_LIKE_PATTERN.match(stripped))


def is_numeric_series(series: pd.Series) -> bool:
    non_empty = series.dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]
    if non_empty.empty:
        return False
    return pd.to_numeric(non_empty, errors="coerce").notna().mean() >= 0.9


def is_categorical_series(series: pd.Series, max_unique_ratio: float = 0.2) -> bool:
    non_empty = series.dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]
    if len(non_empty) < 2:
        return False
    unique_ratio = non_empty.nunique() / len(non_empty)
    return unique_ratio <= max_unique_ratio


def analyze_dataframe_quality(df: pd.DataFrame) -> dict[str, Any]:
    """Statistical data-quality findings for tabular data."""
    if df.empty:
        return {
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "missing_values": {},
            "duplicate_rows": 0,
            "findings": [{"type": "empty_dataset", "severity": "medium", "message": "Dataset has no rows"}],
        }

    columns_info: list[dict[str, Any]] = []
    missing_values: dict[str, int] = {}
    findings: list[dict[str, Any]] = []

    for col in df.columns:
        col_name = str(col)
        series = df[col]
        missing = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
        missing_values[col_name] = missing
        col_info: dict[str, Any] = {
            "name": col_name,
            "missing_count": missing,
            "missing_rate": round(missing / len(df), 4) if len(df) else 0,
        }
        if is_numeric_series(series):
            col_info["inferred_type"] = "numeric"
        elif is_date_like(str(series.dropna().iloc[0])) if series.dropna().size else False:
            col_info["inferred_type"] = "date_like"
        elif is_categorical_series(series):
            col_info["inferred_type"] = "categorical"
            col_info["unique_values"] = int(series.dropna().nunique())
        else:
            col_info["inferred_type"] = "text"
        columns_info.append(col_info)

        if missing > 0:
            missing_mask = _is_missing(series)
            missing_indices = [_file_row_number(i) for i in df.index[missing_mask]]
            locations = [
                {
                    "index": row_num,
                    "column": col_name,
                    "preview": _row_preview(df, row_num - 2, highlight_col=col_name),
                    "value": "(empty)",
                }
                for row_num in missing_indices[:MAX_DQ_LOCATIONS]
            ]
            findings.append({
                "type": "missing_values",
                "severity": "medium" if missing / len(df) < 0.5 else "high",
                "column": col_name,
                "message": f"Column '{col_name}' has {missing} missing value(s)",
                "evidence": {
                    "missing_count": missing,
                    "missing_rate": round(missing / len(df), 4),
                    "column": col_name,
                    "location_type": "row",
                    "locations": locations,
                    "additional_match_count": max(0, len(missing_indices) - len(locations)),
                },
            })

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows > 0:
        dup_mask = df.duplicated(keep=False)
        dup_indices = sorted({_file_row_number(i) for i in df.index[dup_mask]})
        locations = [
            {
                "index": row_num,
                "preview": _row_preview(df, row_num - 2),
            }
            for row_num in dup_indices[:MAX_DQ_LOCATIONS]
        ]
        findings.append({
            "type": "duplicate_rows",
            "severity": "medium",
            "message": f"Found {duplicate_rows} duplicate row(s)",
            "evidence": {
                "duplicate_count": duplicate_rows,
                "location_type": "row",
                "locations": locations,
                "additional_match_count": max(0, len(dup_indices) - len(locations)),
            },
        })

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns_info,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "findings": findings,
    }


def dataframe_to_records(df: pd.DataFrame, limit: int = 1000) -> list[dict[str, Any]]:
    sample = df.head(limit)
    return [
        {str(k): normalize_cell(v) for k, v in row.items()}
        for row in sample.to_dict(orient="records")
    ]


def dataframe_to_table(df: pd.DataFrame, name: str = "data") -> dict[str, Any]:
    headers = [str(c) for c in df.columns]
    rows = [[normalize_cell(v) for v in row] for row in df.head(50).values.tolist()]
    return {"name": name, "headers": headers, "rows": rows, "row_count": len(df)}
