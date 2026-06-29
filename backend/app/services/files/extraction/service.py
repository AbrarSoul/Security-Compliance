"""Unified file extraction dispatcher and column conversion for scanning."""

from __future__ import annotations

from typing import Callable

from app.core.config import get_settings
from app.services.files.extraction.documents import extract_docx, extract_pdf
from app.services.files.extraction.structured import (
    extract_csv,
    extract_json,
    extract_jsonl,
    extract_ndjson,
    extract_tsv,
    extract_xml,
    extract_xlsx,
    extract_yaml,
    extract_yml,
)
from app.services.files.extraction.text import extract_log, extract_markdown, extract_txt
from app.services.files.extraction.types import ExtractedContent
from app.services.scanner.types import CellValue, ColumnSample

settings = get_settings()

_EXTRACTORS: dict[str, Callable[[bytes], ExtractedContent]] = {
    "csv": extract_csv,
    "tsv": extract_tsv,
    "json": extract_json,
    "jsonl": extract_jsonl,
    "ndjson": extract_ndjson,
    "txt": extract_txt,
    "xml": extract_xml,
    "yaml": extract_yaml,
    "yml": extract_yml,
    "log": extract_log,
    "md": extract_markdown,
    "pdf": extract_pdf,
    "docx": extract_docx,
    "xlsx": extract_xlsx,
}


def extract_file(file_type: str, content: bytes) -> ExtractedContent:
    extractor = _EXTRACTORS.get(file_type)
    if extractor is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return extractor(content)


def columns_from_extraction(extracted: ExtractedContent, max_rows: int | None = None) -> list[ColumnSample]:
    """Convert normalized extraction into column samples for pattern detectors."""
    max_rows = max_rows or settings.scan_max_sample_rows

    if extracted.records:
        keys: set[str] = set()
        for item in extracted.records[:max_rows]:
            keys.update(k for k in item if not k.startswith("_"))
        columns: dict[str, list[CellValue]] = {k: [] for k in sorted(keys)}
        location = "record" if extracted.file_type in {"json", "jsonl", "ndjson", "xml", "yaml", "yml"} else "row"
        for record_idx, item in enumerate(extracted.records[:max_rows], start=1):
            index = record_idx + 1 if location == "row" else record_idx
            for key in columns:
                columns[key].append(
                    CellValue(index=index, value=str(item.get(key, "")).strip())
                )
        return [ColumnSample(name=n, cells=v, location_type=location) for n, v in columns.items()]

    if extracted.text_blocks:
        cells = [
            CellValue(
                index=block.get("line", block.get("paragraph_index", idx)),
                value=block["text"],
            )
            for idx, block in enumerate(extracted.text_blocks[:max_rows], start=1)
            if block.get("text")
        ]
        return [ColumnSample(name="line", cells=cells, location_type="line")]

    return []
