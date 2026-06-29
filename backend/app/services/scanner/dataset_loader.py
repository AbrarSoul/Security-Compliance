"""Load column samples from uploaded files via the unified extraction service."""

from app.services.files.extraction.service import columns_from_extraction, extract_file
from app.services.scanner.types import ColumnSample


def load_dataset_columns(file_type: str, content: bytes) -> list[ColumnSample]:
    extracted = extract_file(file_type, content)
    return columns_from_extraction(extracted)
