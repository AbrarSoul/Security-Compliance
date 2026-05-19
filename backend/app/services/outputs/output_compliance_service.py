"""Orchestrates output scanning, audit logging, and monitoring events."""

import hashlib
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.output_scan import OutputScan
from app.repositories.output_scan_repository import OutputScanRepository
from app.services.audit_service import AuditService
from app.services.events.constants import (
    OUTPUT_BLOCKED,
    OUTPUT_GENERATED,
    OUTPUT_SCANNED,
    OUTPUT_WARNING,
    SUSPICIOUS_ACTIVITY,
)
from app.services.events.dispatcher import EventDispatcher
from app.services.events.types import DomainEventEnvelope
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.outputs.constants import (
    DECISION_BLOCK,
    DECISION_WARN,
    MASKED_OUTPUT_MAX_STORE,
    MAX_OUTPUT_LENGTH,
)
from app.services.outputs.engine import OutputScanningEngine
from app.services.outputs.types import OutputScanOutcome


class OutputComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OutputScanRepository(db)
        self.engine = OutputScanningEngine()
        self.monitoring = MonitoringService(db)
        self.dispatcher = EventDispatcher(db)
        self.audit = AuditService(db)

    async def scan_output(
        self,
        *,
        user_id: UUID,
        output_text: str,
        session_id: UUID | None = None,
        execution_request_id: UUID | None = None,
        prompt_scan_id: UUID | None = None,
        metadata: dict | None = None,
        can_read_all_sessions: bool = False,
    ) -> tuple[OutputScan, OutputScanOutcome]:
        text = output_text if output_text is not None else ""
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Output text is required",
            )
        if len(text) > MAX_OUTPUT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Output exceeds maximum length of {MAX_OUTPUT_LENGTH} characters",
            )

        if session_id is not None:
            await self.monitoring.get_session(
                session_id,
                user_id=user_id,
                can_read_all=can_read_all_sessions,
            )
        elif execution_request_id is not None:
            session = await self.monitoring.get_or_open_session_for_execution(
                user_id=user_id,
                execution_request_id=execution_request_id,
            )
            session_id = session.id

        outcome = self.engine.scan(text)
        output_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        stored_masked = outcome.masked_output
        if len(stored_masked) > MASKED_OUTPUT_MAX_STORE:
            stored_masked = stored_masked[:MASKED_OUTPUT_MAX_STORE]

        stored_redacted = outcome.redacted_output
        if stored_redacted and len(stored_redacted) > MASKED_OUTPUT_MAX_STORE:
            stored_redacted = stored_redacted[:MASKED_OUTPUT_MAX_STORE]

        scan = OutputScan(
            user_id=user_id,
            session_id=session_id,
            execution_request_id=execution_request_id,
            prompt_scan_id=prompt_scan_id,
            output_hash=output_hash,
            content_length=len(text),
            decision=outcome.decision,
            risk_score=outcome.risk_score,
            risk_level=outcome.risk_level,
            findings_json=[f.to_dict() for f in outcome.findings],
            masked_output=stored_masked,
            redacted_output=stored_redacted or None,
            blocking_reasons_json=outcome.blocking_reasons,
            warning_reasons_json=outcome.warning_reasons,
            recommendations_json=outcome.recommendations,
            metadata_json=metadata,
        )
        await self.repo.create(scan)

        await self.audit.log_output_scan(
            user_id,
            scan.id,
            outcome.decision,
            metadata={
                "risk_score": outcome.risk_score,
                "risk_level": outcome.risk_level,
                "finding_count": len(outcome.findings),
                "output_hash": output_hash,
                "can_display": outcome.can_display,
            },
        )

        await self._emit_events(
            user_id=user_id,
            session_id=session_id,
            scan_id=scan.id,
            outcome=outcome,
            output_hash=output_hash,
        )
        return scan, outcome

    async def get_scan(
        self,
        scan_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> OutputScan:
        if can_read_all:
            scan = await self.repo.get_by_id(scan_id)
        else:
            scan = await self.repo.get_for_user(scan_id, user_id)
        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output scan not found",
            )
        return scan

    async def list_scans(
        self,
        *,
        user_id: UUID,
        can_read_all: bool,
        session_id: UUID | None = None,
        decision: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OutputScan], int]:
        if session_id is not None:
            await self.monitoring.get_session(
                session_id,
                user_id=user_id,
                can_read_all=can_read_all,
            )
        owner_id = None if can_read_all else user_id
        scans = await self.repo.list_scans(
            user_id=owner_id,
            session_id=session_id,
            decision=decision,
            limit=limit,
            offset=offset,
        )
        total = await self.repo.count_scans(
            user_id=owner_id,
            session_id=session_id,
            decision=decision,
        )
        return scans, total

    async def _emit_events(
        self,
        *,
        user_id: UUID,
        session_id: UUID | None,
        scan_id: UUID,
        outcome: OutputScanOutcome,
        output_hash: str,
    ) -> None:
        base_payload = {
            "scan_id": str(scan_id),
            "decision": outcome.decision,
            "risk_score": outcome.risk_score,
            "risk_level": outcome.risk_level,
            "finding_count": len(outcome.findings),
            "output_hash": output_hash,
            "can_display": outcome.can_display,
        }

        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=OUTPUT_SCANNED,
                user_id=user_id,
                session_id=session_id,
                resource_type="output_scan",
                resource_id=scan_id,
                severity=_severity_for_decision(outcome.decision),
                payload={
                    **base_payload,
                    "finding_types": [f.finding_type for f in outcome.findings],
                },
            )
        )

        if outcome.decision == DECISION_BLOCK:
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=OUTPUT_BLOCKED,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="output_scan",
                    resource_id=scan_id,
                    severity="high",
                    payload={
                        **base_payload,
                        "blocking_reasons": outcome.blocking_reasons,
                    },
                )
            )
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=SUSPICIOUS_ACTIVITY,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="output_scan",
                    resource_id=scan_id,
                    severity="critical",
                    payload={
                        "description": "Output blocked due to compliance violations",
                        "blocking_reasons": outcome.blocking_reasons,
                    },
                )
            )
        elif outcome.decision == DECISION_WARN:
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=OUTPUT_WARNING,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="output_scan",
                    resource_id=scan_id,
                    severity="warning",
                    payload={
                        **base_payload,
                        "warning_reasons": outcome.warning_reasons,
                    },
                )
            )
        else:
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=OUTPUT_GENERATED,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="output_scan",
                    resource_id=scan_id,
                    severity="info",
                    payload=base_payload,
                )
            )


def _severity_for_decision(decision: str) -> str:
    if decision == DECISION_BLOCK:
        return "high"
    if decision == DECISION_WARN:
        return "warning"
    return "info"
