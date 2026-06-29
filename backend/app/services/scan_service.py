import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.models.scan_finding import ScanFinding
from app.models.scan_recommendation import ScanRecommendation
from app.repositories.file_repository import FileRepository
from app.repositories.scan_repository import ScanRepository
from app.services.audit_service import AuditService
from app.services.files.analysis import FileAnalysisEngine
from app.services.files.extraction.service import columns_from_extraction
from app.services.recommendations import RecommendationEngine
from app.services.rule_service import RuleService
from app.services.scanner.scanner import ComplianceScanner
from app.services.scoring import ComplianceScoringEngine
from app.storage.base import StorageBackend


class ScanService:
    def __init__(
        self,
        db: AsyncSession,
        storage: StorageBackend,
        scanner: ComplianceScanner | None = None,
        scoring_engine: ComplianceScoringEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
    ):
        self.db = db
        self.storage = storage
        self.files = FileRepository(db)
        self.scans = ScanRepository(db)
        self.analysis_engine = FileAnalysisEngine()
        self.scanner = scanner or ComplianceScanner(analysis_engine=self.analysis_engine)
        self.scoring_engine = scoring_engine or ComplianceScoringEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.rule_service = RuleService(db)
        self.audit = AuditService(db)

    async def create_and_run_scan(self, user_id: UUID, file_id: UUID):
        file_record = await self.files.get_by_id_for_user(file_id, user_id)
        if file_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        scan_id = uuid.uuid4()
        scan = await self.scans.create(scan_id=scan_id, user_id=user_id, file_id=file_id)
        scan.status = "running"
        scan.started_at = datetime.now(UTC)

        try:
            content = await self.storage.read(file_record.storage_key)
            extracted, analysis_report = self.analysis_engine.analyze_content(
                file_record.file_type,
                content,
                file_id=file_id,
                file_name=file_record.original_name,
            )
            columns = columns_from_extraction(extracted)
            pattern_findings = self.scanner.scan_columns(columns)
            rule_findings = self.analysis_engine.analysis_findings_to_detections(
                analysis_report.findings
            )
            detections = self.scanner._merge_detections(pattern_findings, rule_findings)

            finding_rows = [
                ScanFinding(
                    scan_id=scan.id,
                    finding_type=d.finding_type,
                    severity=d.severity,
                    column_name=d.column_name,
                    sample_count=d.sample_count,
                    match_rate=d.match_rate,
                    evidence_json=d.evidence,
                )
                for d in detections
            ]
            await self.scans.add_findings(finding_rows)

            score_result = self.scoring_engine.score(detections)
            combined_risk = min(
                100,
                max(score_result.risk_score, analysis_report.risk_score),
            )
            scan.risk_score = combined_risk
            scan.compliance_status = score_result.compliance_status
            scan.classification = score_result.classification
            breakdown = score_result.to_breakdown_dict()
            breakdown["file_analysis"] = analysis_report.to_dict()
            breakdown["compliance_score"] = analysis_report.compliance_score
            scan.score_breakdown_json = breakdown

            recommendations = self.recommendation_engine.generate(detections, score_result)
            recommendation_rows = [
                ScanRecommendation(
                    scan_id=scan.id,
                    priority=rec.priority,
                    title=rec.title,
                    description=rec.description,
                    action_type=rec.action_type,
                    finding_type=rec.finding_type,
                    column_name=rec.column_name,
                    metadata_json={
                        **rec.metadata,
                        "related_finding_types": rec.related_finding_types,
                    },
                )
                for rec in recommendations
            ]
            await self.scans.add_recommendations(recommendation_rows)

            rule_result = await self.rule_service.evaluate_detections(
                detections,
                risk_score=score_result.risk_score,
                compliance_status=score_result.compliance_status,
                classification=score_result.classification,
            )
            scan.rule_evaluation_json = rule_result.to_dict()

            scan.status = "completed"
            scan.completed_at = datetime.now(UTC)
        except Exception as exc:
            scan.status = "failed"
            scan.error_message = str(exc)[:2000]
            scan.completed_at = datetime.now(UTC)
            await self.scans.update_scan(scan)
            await self.audit.log(
                AuditAction.SCAN_FAILED,
                user_id=user_id,
                resource_type="scan",
                resource_id=scan.id,
                severity=audit_severity.HIGH,
                status="failure",
                metadata={"file_id": str(file_id), "error": scan.error_message},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Scan failed",
            ) from exc

        await self.scans.update_scan(scan)
        await self.db.refresh(scan, attribute_names=["findings", "recommendations", "file"])
        await self._audit_scan_completed(user_id, file_id, scan, finding_rows)
        return scan

    async def _audit_scan_completed(
        self,
        user_id: UUID,
        file_id: UUID,
        scan,
        findings: list[ScanFinding],
    ) -> None:
        await self.audit.log(
            AuditAction.SCAN_COMPLETED,
            user_id=user_id,
            resource_type="scan",
            resource_id=scan.id,
            severity=_severity_from_risk_score(scan.risk_score),
            status="success",
            metadata={
                "file_id": str(file_id),
                "risk_score": scan.risk_score,
                "compliance_status": scan.compliance_status,
                "classification": scan.classification,
                "findings_count": len(findings),
            },
        )
        await self.audit.log(
            AuditAction.FILE_SCANNED,
            user_id=user_id,
            resource_type="file",
            resource_id=file_id,
            severity=_severity_from_risk_score(scan.risk_score),
            status="success",
            metadata={"scan_id": str(scan.id), "risk_score": scan.risk_score},
        )
        if _should_log_risk_detected(scan, findings):
            await self.audit.log(
                AuditAction.COMPLIANCE_RISK_DETECTED,
                user_id=user_id,
                resource_type="scan",
                resource_id=scan.id,
                severity=audit_severity.HIGH,
                status="success",
                metadata={
                    "risk_score": scan.risk_score,
                    "compliance_status": scan.compliance_status,
                    "high_severity_findings": [
                        f.finding_type
                        for f in findings
                        if f.severity in ("high", "critical")
                    ],
                },
            )

    async def get_scan(self, scan_id: UUID, user_id: UUID):
        scan = await self.scans.get_by_id_for_user(scan_id, user_id)
        if scan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
        return scan

    async def list_scans(self, user_id: UUID, limit: int = 50, offset: int = 0):
        return await self.scans.list_by_user(user_id, limit=limit, offset=offset)


def _severity_from_risk_score(risk_score: int | None) -> str:
    if risk_score is None:
        return audit_severity.INFO
    if risk_score >= 80:
        return audit_severity.CRITICAL
    if risk_score >= 60:
        return audit_severity.HIGH
    if risk_score >= 40:
        return audit_severity.MEDIUM
    if risk_score >= 20:
        return audit_severity.LOW
    return audit_severity.INFO


def _should_log_risk_detected(scan, findings: list[ScanFinding]) -> bool:
    if scan.compliance_status in ("risky", "non_compliant"):
        return True
    if scan.risk_score is not None and scan.risk_score >= 50:
        return True
    return any(f.severity in ("high", "critical") for f in findings)
