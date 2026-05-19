from app.services.scanner.detectors import ALL_DETECTORS
from app.services.scanner.dataset_loader import load_dataset_columns
from app.services.scanner.types import ColumnSample, DetectionResult


class ComplianceScanner:
    def __init__(self, detectors=None):
        self.detectors = detectors or ALL_DETECTORS

    def scan_content(self, file_type: str, content: bytes) -> list[DetectionResult]:
        columns = load_dataset_columns(file_type, content)
        return self.scan_columns(columns)

    def scan_columns(self, columns: list[ColumnSample]) -> list[DetectionResult]:
        findings: list[DetectionResult] = []
        seen: set[tuple[str, str | None]] = set()

        for column in columns:
            for detector in self.detectors:
                result = detector.detect(column)
                if result is None:
                    continue
                key = (result.finding_type, result.column_name)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(result)

        return findings
