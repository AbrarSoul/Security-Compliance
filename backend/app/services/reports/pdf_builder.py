from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _status_color(status: str | None) -> colors.Color:
    mapping = {
        "compliant": colors.HexColor("#16a34a"),
        "risky": colors.HexColor("#ca8a04"),
        "non_compliant": colors.HexColor("#dc2626"),
    }
    return mapping.get(status or "", colors.HexColor("#374151"))


def build_report_pdf(report_data: dict[str, Any]) -> bytes:
    """Generate a PDF compliance report from the report JSON structure."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Compliance Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=12,
        textColor=colors.HexColor("#111827"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#1f2937"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
    )

    story: list = []

    story.append(Paragraph("Security Compliance Report", title_style))
    story.append(
        Paragraph(
            f"Generated: {report_data.get('generated_at', 'N/A')}<br/>"
            f"Report ID: {report_data.get('report_id', 'N/A')}<br/>"
            f"Scan ID: {report_data.get('scan_id', 'N/A')}",
            body_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Executive summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary = report_data.get("executive_summary", {})
    file_info = report_data.get("file", {})
    summary_rows = [
        ["File", file_info.get("name", "N/A")],
        ["Risk Score", str(summary.get("risk_score", "N/A"))],
        ["Compliance Status", (summary.get("compliance_status") or "N/A").replace("_", " ").title()],
        ["Classification", (summary.get("classification") or "N/A").title()],
        ["Total Findings", str(summary.get("total_findings", 0))],
        ["Highest Severity", (summary.get("highest_severity") or "N/A").title()],
    ]
    summary_table = Table(summary_rows, colWidths=[1.8 * inch, 4.5 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.15 * inch))

    status = summary.get("compliance_status")
    status_color = _status_color(status)
    story.append(
        Paragraph(
            f'<font color="{status_color.hexval()}">'
            f"<b>Overall status: {(status or 'unknown').replace('_', ' ').title()}</b></font>",
            body_style,
        )
    )

    # Detected issues
    issues = report_data.get("detected_issues", [])
    story.append(Paragraph("Detected Issues", heading_style))
    if issues:
        issue_rows = [["Type", "Severity", "Column", "Samples", "Match %"]]
        for issue in issues:
            match_pct = issue.get("match_rate")
            match_str = f"{match_pct * 100:.1f}%" if match_pct is not None else "—"
            issue_rows.append(
                [
                    issue.get("type", ""),
                    issue.get("severity", "").title(),
                    issue.get("column") or "—",
                    str(issue.get("sample_count", 0)),
                    match_str,
                ]
            )
        issues_table = Table(issue_rows, colWidths=[1.1 * inch, 0.9 * inch, 1.4 * inch, 0.8 * inch, 0.8 * inch])
        issues_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(issues_table)
    else:
        story.append(Paragraph("No sensitive data patterns were detected.", body_style))

    # Recommendations
    recs = report_data.get("recommendations", [])
    story.append(Paragraph("Recommendations", heading_style))
    if recs:
        for i, rec in enumerate(recs, start=1):
            priority = rec.get("priority", "medium").upper()
            story.append(
                Paragraph(
                    f"<b>{i}. [{priority}] {rec.get('title', '')}</b><br/>"
                    f"{rec.get('description', '')}<br/>"
                    f"<i>Action: {rec.get('action_type', '').replace('_', ' ')}</i>",
                    body_style,
                )
            )
            story.append(Spacer(1, 0.08 * inch))
    else:
        story.append(Paragraph("No recommendations required.", body_style))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "<i>This report was generated automatically. "
            "Review findings before making compliance decisions.</i>",
            ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.grey),
        )
    )

    doc.build(story)
    return buffer.getvalue()
