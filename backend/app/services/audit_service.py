"""Centralized append-only audit logging."""

from __future__ import annotations

import copy
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit_severity
from app.core.audit_actions import AuditAction
from app.core.request_context import RequestContext, get_request_context
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "refresh_token",
        "access_token",
        "token",
        "secret",
        "authorization",
    }
)


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None

    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in _SENSITIVE_KEYS else _walk(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_walk(item) for item in obj]
        return obj

    return _walk(copy.deepcopy(metadata))


class AuditService:
    """Persists immutable audit log entries."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def log(
        self,
        action: str,
        *,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        severity: str | None = audit_severity.INFO,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
        request_context: RequestContext | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        ctx = request_context or get_request_context()
        entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            status=status,
            metadata_json=_sanitize_metadata(metadata),
            request_id=request_id or (ctx.request_id if ctx else None),
            ip_address=ip_address or (ctx.ip_address if ctx else None),
            user_agent=user_agent or (ctx.user_agent if ctx else None),
        )
        return await self.repo.create(entry)

    # --- Helpers for future policy / rule / execution APIs ---

    async def log_rule_created(
        self, user_id: UUID, rule_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.RULE_CREATED,
            user_id=user_id,
            resource_type="rule",
            resource_id=rule_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_rule_updated(
        self, user_id: UUID, rule_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.RULE_UPDATED,
            user_id=user_id,
            resource_type="rule",
            resource_id=rule_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_rule_disabled(
        self, user_id: UUID, rule_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.RULE_DISABLED,
            user_id=user_id,
            resource_type="rule",
            resource_id=rule_id,
            severity=audit_severity.MEDIUM,
            metadata=metadata,
        )

    async def log_policy_created(
        self, user_id: UUID, policy_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.POLICY_CREATED,
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_policy_updated(
        self, user_id: UUID, policy_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.POLICY_UPDATED,
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_policy_activation(
        self,
        user_id: UUID,
        policy_id: UUID,
        *,
        is_active: bool,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        action = AuditAction.POLICY_ACTIVATED if is_active else AuditAction.POLICY_DEACTIVATED
        return await self.log(
            action,
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_policy_archived(
        self, user_id: UUID, policy_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.POLICY_ARCHIVED,
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_model_registered(
        self, user_id: UUID, model_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.MODEL_REGISTERED,
            user_id=user_id,
            resource_type="compliance_model",
            resource_id=model_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_model_updated(
        self, user_id: UUID, model_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.MODEL_UPDATED,
            user_id=user_id,
            resource_type="compliance_model",
            resource_id=model_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_model_validated(
        self, user_id: UUID, validation_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        severity = audit_severity.INFO
        if metadata and metadata.get("risk_level") in ("high", "critical"):
            severity = audit_severity.MEDIUM
        return await self.log(
            AuditAction.MODEL_VALIDATED,
            user_id=user_id,
            resource_type="model_validation",
            resource_id=validation_id,
            severity=severity,
            metadata=metadata,
        )

    async def log_model_validation_blocked(
        self, user_id: UUID, validation_id: UUID, metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        return await self.log(
            AuditAction.MODEL_VALIDATION_BLOCKED,
            user_id=user_id,
            resource_type="model_validation",
            resource_id=validation_id,
            severity=audit_severity.HIGH,
            status="blocked",
            metadata=metadata,
        )

    async def log_execution_decision(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        decision: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        action_map = {
            "allow": AuditAction.EXECUTION_ALLOWED,
            "warn": AuditAction.EXECUTION_WARNED,
            "block": AuditAction.EXECUTION_BLOCKED,
            "requested": AuditAction.EXECUTION_REQUESTED,
        }
        action = action_map.get(decision.lower(), AuditAction.EXECUTION_REQUESTED)
        severity = audit_severity.HIGH if decision.lower() == "block" else audit_severity.MEDIUM
        return await self.log(
            action,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=severity,
            status="success" if decision.lower() != "block" else "blocked",
            metadata=metadata,
        )

    async def log_execution_start_requested(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.EXECUTION_START_REQUESTED,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=audit_severity.INFO,
            metadata=metadata,
        )

    async def log_execution_started(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.EXECUTION_STARTED,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=audit_severity.INFO,
            status="success",
            metadata=metadata,
        )

    async def log_execution_warning_acknowledged(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.EXECUTION_WARNING_ACKNOWLEDGED,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=audit_severity.MEDIUM,
            metadata=metadata,
        )

    async def log_execution_blocked(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.EXECUTION_BLOCKED,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=audit_severity.HIGH,
            status="blocked",
            metadata=metadata,
        )

    async def log_execution_start_unauthorized(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.EXECUTION_START_UNAUTHORIZED,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=audit_severity.HIGH,
            status="failure",
            metadata=metadata,
        )

    async def log_output_scan(
        self,
        user_id: UUID,
        output_scan_id: UUID,
        decision: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        action_map = {
            "allow": AuditAction.OUTPUT_ALLOWED,
            "warn": AuditAction.OUTPUT_WARNED,
            "block": AuditAction.OUTPUT_BLOCKED,
        }
        action = action_map.get(decision.lower(), AuditAction.OUTPUT_SCANNED)
        severity = (
            audit_severity.HIGH
            if decision.lower() == "block"
            else audit_severity.MEDIUM
            if decision.lower() == "warn"
            else audit_severity.INFO
        )
        status = "blocked" if decision.lower() == "block" else "success"
        meta = {"decision": decision, **(metadata or {})}
        await self.log(
            AuditAction.OUTPUT_SCANNED,
            user_id=user_id,
            resource_type="output_scan",
            resource_id=output_scan_id,
            severity=audit_severity.INFO,
            status="success",
            metadata=meta,
        )
        return await self.log(
            action,
            user_id=user_id,
            resource_type="output_scan",
            resource_id=output_scan_id,
            severity=severity,
            status=status,
            metadata=meta,
        )

    async def log_guard_enforcement(
        self,
        user_id: UUID,
        execution_request_id: UUID,
        *,
        decision: str,
        source: str,
        interrupted: bool,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        action = AuditAction.GUARD_ENFORCED
        if interrupted:
            await self.log(
                AuditAction.EXECUTION_INTERRUPTED,
                user_id=user_id,
                resource_type="execution_request",
                resource_id=execution_request_id,
                severity=audit_severity.HIGH,
                status="interrupted",
                metadata=metadata,
            )
        if decision == "block":
            if source == "prompt":
                action = AuditAction.GUARD_PROMPT_BLOCKED
            elif source == "output":
                action = AuditAction.GUARD_OUTPUT_BLOCKED
        severity = (
            audit_severity.HIGH
            if decision == "block"
            else audit_severity.MEDIUM
            if decision == "warn"
            else audit_severity.INFO
        )
        return await self.log(
            action,
            user_id=user_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
            severity=severity,
            status="blocked" if decision == "block" else "success",
            metadata={"decision": decision, "source": source, **(metadata or {})},
        )


    async def log_gap_analysis_run(
        self,
        *,
        user_id: UUID | None,
        run_id: UUID,
        gaps_found: int,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.log(
            AuditAction.GAP_ANALYSIS_RUN,
            user_id=user_id,
            resource_type="gap_analysis_run",
            resource_id=run_id,
            severity=audit_severity.INFO,
            metadata={"gaps_found": gaps_found, **(metadata or {})},
        )

    async def log_gap_detected(
        self,
        *,
        user_id: UUID | None,
        gap_id: UUID,
        gap_type: str,
        severity: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        sev = severity if severity in audit_severity.ALL else audit_severity.MEDIUM
        return await self.log(
            AuditAction.GAP_DETECTED,
            user_id=user_id,
            resource_type="compliance_gap",
            resource_id=gap_id,
            severity=sev,
            metadata={"gap_type": gap_type, **(metadata or {})},
        )

    async def log_gap_status_change(
        self,
        *,
        user_id: UUID | None,
        gap_id: UUID,
        new_status: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        action = (
            AuditAction.GAP_RESOLVED
            if new_status == "resolved"
            else AuditAction.GAP_ACKNOWLEDGED
        )
        return await self.log(
            action,
            user_id=user_id,
            resource_type="compliance_gap",
            resource_id=gap_id,
            severity=audit_severity.INFO,
            metadata={"status": new_status, **(metadata or {})},
        )


async def audit_log(
    db: AsyncSession,
    action: str,
    *,
    user_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    severity: str | None = audit_severity.INFO,
    status: str = "success",
    metadata: dict[str, Any] | None = None,
    request_context: RequestContext | None = None,
) -> AuditLog:
    """Reusable helper to append an audit log row using the current DB session."""
    return await AuditService(db).log(
        action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=severity,
        status=status,
        metadata=metadata,
        request_context=request_context,
    )
