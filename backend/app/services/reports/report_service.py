import json
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.models.report import Report
from app.repositories.report_repository import ReportRepository
from app.services.audit_service import AuditService
from app.repositories.scan_repository import ScanRepository
from app.services.reports.json_builder import build_report_json
from app.services.reports.pdf_builder import build_report_pdf
from app.storage.base import StorageBackend


class ReportService:
    def __init__(self, db: AsyncSession, storage: StorageBackend):
        self.db = db
        self.storage = storage
        self.reports = ReportRepository(db)
        self.scans = ScanRepository(db)
        self.audit = AuditService(db)

    async def generate_report(self, user_id: UUID, scan_id: UUID) -> Report:
        scan = await self.scans.get_by_id_for_user(scan_id, user_id)
        if scan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

        if scan.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan must be completed before generating a report",
            )

        existing = await self.reports.get_by_scan_id(scan_id)
        if existing:
            await self._delete_stored_files(existing)
            await self.reports.delete(existing)

        if not scan.file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated file not found",
            )

        report_id = uuid.uuid4()
        file_metadata = scan.file.metadata_row

        summary = build_report_json(
            report_id=report_id,
            scan=scan,
            file_record=scan.file,
            file_metadata=file_metadata,
        )

        json_bytes = json.dumps(summary, indent=2, default=str).encode("utf-8")
        pdf_bytes = build_report_pdf(summary)

        json_key = self.storage.build_report_storage_key(user_id, report_id, "json")
        pdf_key = self.storage.build_report_storage_key(user_id, report_id, "pdf")

        await self.storage.save(json_key, json_bytes)
        await self.storage.save(pdf_key, pdf_bytes)

        report = Report(
            id=report_id,
            scan_id=scan_id,
            user_id=user_id,
            summary_json=summary,
            json_storage_key=json_key,
            pdf_storage_key=pdf_key,
        )
        await self.reports.create(report)
        await self.audit.log(
            AuditAction.REPORT_GENERATED,
            user_id=user_id,
            resource_type="report",
            resource_id=report.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={
                "scan_id": str(scan_id),
                "risk_score": scan.risk_score,
                "compliance_status": scan.compliance_status,
            },
        )
        return report

    async def get_report(
        self,
        report_id: UUID,
        user_id: UUID,
        *,
        can_read_all: bool = False,
    ) -> Report:
        if can_read_all:
            report = await self.reports.get_by_id(report_id)
        else:
            report = await self.reports.get_by_id_for_user(report_id, user_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report

    async def list_reports(
        self,
        user_id: UUID,
        *,
        can_read_all: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Report]:
        if can_read_all:
            return await self.reports.list_all(limit=limit, offset=offset)
        return await self.reports.list_by_user(user_id, limit=limit, offset=offset)

    async def export_report(
        self,
        report_id: UUID,
        user_id: UUID,
        fmt: str,
        *,
        can_read_all: bool = False,
    ) -> tuple[bytes, str, str]:
        report = await self.get_report(report_id, user_id, can_read_all=can_read_all)
        fmt = fmt.lower()

        if fmt == "json":
            if report.json_storage_key:
                try:
                    content = await self.storage.read(report.json_storage_key)
                except FileNotFoundError:
                    content = json.dumps(report.summary_json, indent=2, default=str).encode("utf-8")
            else:
                content = json.dumps(report.summary_json, indent=2, default=str).encode("utf-8")
            filename = f"compliance-report-{report.id}.json"
            media_type = "application/json"
            return content, filename, media_type

        if fmt == "pdf":
            if not report.pdf_storage_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="PDF export not available",
                )
            try:
                content = await self.storage.read(report.pdf_storage_key)
            except FileNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="PDF file not found in storage",
                ) from exc
            filename = f"compliance-report-{report.id}.pdf"
            media_type = "application/pdf"
            return content, filename, media_type

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'json' or 'pdf'",
        )

    async def _delete_stored_files(self, report: Report) -> None:
        for key in (report.json_storage_key, report.pdf_storage_key):
            if key:
                try:
                    await self.storage.delete(key)
                except FileNotFoundError:
                    pass
