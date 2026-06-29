from app.services.files.analysis.analyzer import FileAnalysisEngine
from app.services.scanner.detectors import ALL_DETECTORS
from app.services.files.extraction.service import columns_from_extraction, extract_file
from app.services.scanner.types import ColumnSample, DetectionResult


class ComplianceScanner:
    def __init__(self, detectors=None, analysis_engine: FileAnalysisEngine | None = None):
        self.detectors = detectors or ALL_DETECTORS
        self.analysis_engine = analysis_engine or FileAnalysisEngine()

    def scan_content(self, file_type: str, content: bytes) -> list[DetectionResult]:
        extracted = extract_file(file_type, content)
        columns = columns_from_extraction(extracted)
        pattern_findings = self.scan_columns(columns)
        _, report = self.analysis_engine.analyze_content(
            file_type, content, file_name="upload"
        )
        rule_findings = self.analysis_engine.analysis_findings_to_detections(report.findings)
        return self._merge_detections(pattern_findings, rule_findings)

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

    @staticmethod
    def _merge_detections(
        pattern_findings: list[DetectionResult],
        rule_findings: list[DetectionResult],
    ) -> list[DetectionResult]:
        seen: set[tuple[str, str | None]] = set()
        merged: list[DetectionResult] = []
        for finding in pattern_findings + rule_findings:
            key = (finding.finding_type, finding.column_name)
            if key in seen:
                continue
            seen.add(key)
            merged.append(finding)
        return merged
