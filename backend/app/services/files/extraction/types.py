"""Normalized extraction result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedContent:
    """Common normalized structure returned by every extract_* function."""

    file_type: str
    text_blocks: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=lambda: {
        "headings": [],
        "sections": [],
        "pages": [],
        "sheets": [],
    })
    data_quality: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_type": self.file_type,
            "text_blocks": self.text_blocks,
            "tables": self.tables,
            "metadata": self.metadata,
            "records": self.records,
            "structure": self.structure,
            "data_quality": self.data_quality,
        }

    @classmethod
    def empty(cls, file_type: str) -> ExtractedContent:
        return cls(file_type=file_type)
