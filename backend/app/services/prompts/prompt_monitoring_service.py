"""Orchestrates prompt scanning, persistence, and monitoring pipeline events."""

import hashlib
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_scan import PromptScan
from app.repositories.prompt_scan_repository import PromptScanRepository
from app.services.events.constants import (
    PROMPT_BLOCKED,
    PROMPT_SCANNED,
    PROMPT_SUBMITTED,
    PROMPT_WARNING,
    SUSPICIOUS_ACTIVITY,
)
from app.services.events.dispatcher import EventDispatcher
from app.services.events.types import DomainEventEnvelope
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.prompts.constants import (
    DECISION_BLOCK,
    DECISION_WARN,
    MASKED_PROMPT_MAX_STORE,
    MAX_PROMPT_LENGTH,
)
from app.services.prompts.engine import PromptScanningEngine
from app.services.prompts.types import PromptScanOutcome


class PromptMonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PromptScanRepository(db)
        self.engine = PromptScanningEngine()
        self.monitoring = MonitoringService(db)
        self.dispatcher = EventDispatcher(db)

    async def scan_prompt(
        self,
        *,
        user_id: UUID,
        prompt: str,
        session_id: UUID | None = None,
        execution_request_id: UUID | None = None,
        metadata: dict | None = None,
        can_read_all_sessions: bool = False,
    ) -> tuple[PromptScan, PromptScanOutcome]:
        text = prompt if prompt is not None else ""
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt text is required",
            )
        if len(text) > MAX_PROMPT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters",
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
        prompt_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        stored_masked = outcome.masked_prompt
        if len(stored_masked) > MASKED_PROMPT_MAX_STORE:
            stored_masked = stored_masked[:MASKED_PROMPT_MAX_STORE]

        scan = PromptScan(
            user_id=user_id,
            session_id=session_id,
            execution_request_id=execution_request_id,
            prompt_hash=prompt_hash,
            content_length=len(text),
            decision=outcome.decision,
            risk_score=outcome.risk_score,
            risk_level=outcome.risk_level,
            findings_json=[f.to_dict() for f in outcome.findings],
            masked_prompt=stored_masked,
            blocking_reasons_json=outcome.blocking_reasons,
            warning_reasons_json=outcome.warning_reasons,
            recommendations_json=outcome.recommendations,
            metadata_json=metadata,
        )
        await self.repo.create(scan)

        await self._emit_events(
            user_id=user_id,
            session_id=session_id,
            scan_id=scan.id,
            outcome=outcome,
            prompt_hash=prompt_hash,
        )
        return scan, outcome

    async def get_scan(
        self,
        scan_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> PromptScan:
        if can_read_all:
            scan = await self.repo.get_by_id(scan_id)
        else:
            scan = await self.repo.get_for_user(scan_id, user_id)
        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt scan not found",
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
    ) -> tuple[list[PromptScan], int]:
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
        outcome: PromptScanOutcome,
        prompt_hash: str,
    ) -> None:
        base_payload = {
            "scan_id": str(scan_id),
            "decision": outcome.decision,
            "risk_score": outcome.risk_score,
            "risk_level": outcome.risk_level,
            "finding_count": len(outcome.findings),
            "prompt_hash": prompt_hash,
        }

        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=PROMPT_SUBMITTED,
                user_id=user_id,
                session_id=session_id,
                resource_type="prompt_scan",
                resource_id=scan_id,
                severity=_severity_for_decision(outcome.decision),
                payload=base_payload,
            )
        )

        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=PROMPT_SCANNED,
                user_id=user_id,
                session_id=session_id,
                resource_type="prompt_scan",
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
                    event_type=PROMPT_BLOCKED,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="prompt_scan",
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
                    resource_type="prompt_scan",
                    resource_id=scan_id,
                    severity="critical",
                    payload={
                        "description": "Prompt blocked due to policy violations",
                        "blocking_reasons": outcome.blocking_reasons,
                    },
                )
            )
        elif outcome.decision == DECISION_WARN:
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=PROMPT_WARNING,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="prompt_scan",
                    resource_id=scan_id,
                    severity="warning",
                    payload={
                        **base_payload,
                        "warning_reasons": outcome.warning_reasons,
                    },
                )
            )


def _severity_for_decision(decision: str) -> str:
    if decision == DECISION_BLOCK:
        return "high"
    if decision == DECISION_WARN:
        return "warning"
    return "info"
