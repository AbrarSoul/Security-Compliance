from typing import Protocol

from app.services.scanner.types import ColumnSample, DetectionResult


class Detector(Protocol):
    name: str

    def detect(self, column: ColumnSample) -> DetectionResult | None: ...
