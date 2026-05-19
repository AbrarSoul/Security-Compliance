from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateReportRequest(BaseModel):
    scan_id: UUID


class ReportSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scan_id: UUID
    created_at: datetime
    executive_summary: dict[str, Any] = Field(
        description="Subset of summary for list views",
    )


class ReportDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scan_id: UUID
    created_at: datetime
    summary: dict[str, Any] = Field(validation_alias="summary_json", serialization_alias="summary")
    has_json_export: bool = False
    has_pdf_export: bool = False

    @classmethod
    def from_report(cls, report) -> "ReportDetailResponse":
        return cls(
            id=report.id,
            scan_id=report.scan_id,
            created_at=report.created_at,
            summary_json=report.summary_json or {},
            has_json_export=bool(report.json_storage_key),
            has_pdf_export=bool(report.pdf_storage_key),
        )


class ReportListResponse(BaseModel):
    items: list[ReportSummaryResponse]
    total: int
    limit: int
    offset: int


class ReportGenerateResponse(BaseModel):
    message: str = "Report generated successfully"
    report: ReportDetailResponse
