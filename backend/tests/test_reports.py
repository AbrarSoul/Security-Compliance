import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.reports import ReportDetailResponse
from app.services.reports.json_builder import build_report_json
from app.services.reports.pdf_builder import build_report_pdf
from app.services.reports.report_service import ReportService


def _make_scan():
    finding = SimpleNamespace(
        id=uuid.uuid4(),
        finding_type="email",
        severity="medium",
        column_name="email",
        sample_count=10,
        match_rate=0.9,
        evidence_json={"masked_samples": ["te***@example.com"]},
    )
    recommendation = SimpleNamespace(
        id=uuid.uuid4(),
        priority="medium",
        title="Anonymize email addresses",
        description="Apply hashing to column 'email'.",
        action_type="anonymize",
        finding_type="email",
        column_name="email",
    )
    return SimpleNamespace(
        id=uuid.uuid4(),
        status="completed",
        risk_score=45,
        compliance_status="risky",
        classification="confidential",
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        score_breakdown_json={"risk_score": 45},
        findings=[finding],
        recommendations=[recommendation],
    )


def _make_file():
    metadata = SimpleNamespace(row_count=100, column_count=5)
    return SimpleNamespace(
        id=uuid.uuid4(),
        original_name="customers.csv",
        file_type="csv",
        size_bytes=4096,
        metadata_row=metadata,
    )


def test_report_detail_response_from_report():
    report = SimpleNamespace(
        id=uuid.uuid4(),
        scan_id=uuid.uuid4(),
        created_at=datetime.now(UTC),
        summary_json={"executive_summary": {"risk_score": 45, "compliance_status": "risky"}},
        json_storage_key="user/reports/foo.json",
        pdf_storage_key="user/reports/foo.pdf",
    )
    response = ReportDetailResponse.from_report(report)
    assert response.id == report.id
    assert response.summary["executive_summary"]["risk_score"] == 45
    assert response.has_json_export is True
    assert response.has_pdf_export is True


def test_build_report_json_structure():
    report_id = uuid.uuid4()
    scan = _make_scan()
    file_record = _make_file()
    data = build_report_json(
        report_id=report_id,
        scan=scan,
        file_record=file_record,
        file_metadata=file_record.metadata_row,
    )
    assert data["report_id"] == str(report_id)
    assert data["executive_summary"]["compliance_status"] == "risky"
    assert len(data["detected_issues"]) == 1
    assert len(data["recommendations"]) == 1
    assert data["compliance_score"]["risk_score"] == 45
    json.dumps(data)


def test_build_report_pdf_returns_pdf_bytes():
    report_id = uuid.uuid4()
    scan = _make_scan()
    file_record = _make_file()
    data = build_report_json(
        report_id=report_id,
        scan=scan,
        file_record=file_record,
        file_metadata=file_record.metadata_row,
    )
    pdf = build_report_pdf(data)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500


@pytest.mark.asyncio
async def test_export_report_pdf_regenerates_when_storage_missing():
    report_id = uuid.uuid4()
    user_id = uuid.uuid4()
    summary = {
        "report_id": str(report_id),
        "executive_summary": {"risk_score": 45, "compliance_status": "risky"},
        "detected_issues": [],
        "recommendations": [],
        "compliance_score": {"risk_score": 45},
    }
    report = SimpleNamespace(
        id=report_id,
        pdf_storage_key=f"{user_id}/reports/{report_id}.pdf",
        summary_json=summary,
    )
    storage = MagicMock()
    storage.read = AsyncMock(side_effect=FileNotFoundError("missing"))
    storage.save = AsyncMock()

    service = ReportService(db=MagicMock(), storage=storage)
    service.get_report = AsyncMock(return_value=report)

    content, filename, media_type = await service.export_report(
        report_id, user_id, "pdf"
    )

    assert content[:4] == b"%PDF"
    assert filename == f"compliance-report-{report_id}.pdf"
    assert media_type == "application/pdf"
    storage.save.assert_awaited_once_with(report.pdf_storage_key, content)


def test_build_report_pdf_empty_findings():
    report_id = uuid.uuid4()
    scan = _make_scan()
    scan.findings = []
    scan.recommendations = []
    scan.risk_score = 0
    scan.compliance_status = "compliant"
    scan.classification = "public"
    file_record = _make_file()
    data = build_report_json(
        report_id=report_id,
        scan=scan,
        file_record=file_record,
        file_metadata=file_record.metadata_row,
    )
    pdf = build_report_pdf(data)
    assert pdf[:4] == b"%PDF"
