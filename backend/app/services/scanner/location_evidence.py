from collections.abc import Callable

from app.services.scanner import patterns
from app.services.scanner.types import MAX_LOCATIONS_IN_EVIDENCE, CellValue, ColumnSample


def collect_match_evidence(
    column: ColumnSample,
    predicate: Callable[[str], bool],
    *,
    mask: Callable[[str], str] | None = None,
    extra: dict | None = None,
) -> dict:
    """Build evidence dict with masked previews at specific row/record/line indices."""
    mask_fn = mask or patterns.mask_value
    matches = [c for c in column.cells if c.value and predicate(c.value)]
    locations = [
        {"index": c.index, "preview": mask_fn(c.value)}
        for c in matches[:MAX_LOCATIONS_IN_EVIDENCE]
    ]

    evidence: dict = {
        "location_type": column.location_type,
        "locations": locations,
        "masked_samples": [loc["preview"] for loc in locations],
    }
    if len(matches) > MAX_LOCATIONS_IN_EVIDENCE:
        evidence["additional_match_count"] = len(matches) - MAX_LOCATIONS_IN_EVIDENCE
    if extra:
        evidence.update(extra)
    return evidence


def collect_cell_evidence(
    cells: list[CellValue],
    *,
    location_type: str,
    mask: Callable[[str], str] | None = None,
    limit: int = MAX_LOCATIONS_IN_EVIDENCE,
    extra: dict | None = None,
) -> dict:
    """Build location evidence from an explicit list of matching cells."""
    mask_fn = mask or patterns.mask_value
    non_empty = [c for c in cells if c.value]
    shown = non_empty[:limit]
    locations = [{"index": c.index, "preview": mask_fn(c.value)} for c in shown]

    evidence: dict = {
        "location_type": location_type,
        "locations": locations,
        "masked_samples": [loc["preview"] for loc in locations],
    }
    if len(non_empty) > limit:
        evidence["additional_match_count"] = len(non_empty) - limit
    if extra:
        evidence.update(extra)
    return evidence
