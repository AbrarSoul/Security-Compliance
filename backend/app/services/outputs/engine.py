from app.services.outputs.decision_engine import OutputDecisionEngine
from app.services.outputs.detectors import ALL_OUTPUT_DETECTORS
from app.services.outputs.masking import mask_output
from app.services.outputs.scoring import score_findings
from app.services.outputs.types import OutputFinding, OutputScanOutcome


class OutputScanningEngine:
    def __init__(self, detectors=None, decision_engine: OutputDecisionEngine | None = None):
        self.detectors = detectors or ALL_OUTPUT_DETECTORS
        self.decision_engine = decision_engine or OutputDecisionEngine()

    def scan(self, output_text: str) -> OutputScanOutcome:
        text = output_text.strip()
        findings = self._run_detectors(text)
        findings = self._dedupe(findings)
        risk_score, risk_level = score_findings(findings)
        masked = mask_output(text)
        return self.decision_engine.decide(
            findings=findings,
            risk_score=risk_score,
            risk_level=risk_level,
            masked_output=masked,
        )

    def _run_detectors(self, text: str) -> list[OutputFinding]:
        results: list[OutputFinding] = []
        for detector in self.detectors:
            results.extend(detector.detect(text))
        return results

    @staticmethod
    def _dedupe(findings: list[OutputFinding]) -> list[OutputFinding]:
        seen: set[str] = set()
        unique: list[OutputFinding] = []
        for f in findings:
            key = f"{f.finding_type}:{f.message}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        return unique
