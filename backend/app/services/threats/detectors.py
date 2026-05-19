"""Threat detection rules over monitoring data."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.models.execution_request import ExecutionRequest
from app.models.prompt_scan import PromptScan
from app.services.events.constants import (
    EXECUTION_BLOCKED,
    EXECUTION_INTERRUPTED,
    GUARD_PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    POLICY_VIOLATION,
    PROMPT_BLOCKED,
)
from app.services.prompts.constants import FINDING_JAILBREAK, FINDING_PROMPT_INJECTION
from app.services.threats.constants import (
    CATEGORY_API_ABUSE,
    CATEGORY_EXECUTION,
    CATEGORY_POLICY,
    CATEGORY_PROMPT_SECURITY,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    THREAT_ABNORMAL_EXECUTION,
    THREAT_EXCESSIVE_BLOCKS,
    THREAT_EXTERNAL_API_ABUSE,
    THREAT_JAILBREAK,
    THREAT_PROMPT_INJECTION,
    THREAT_REPEATED_POLICY_VIOLATION,
    THREAT_SUSPICIOUS_PROMPT,
    BLOCKED_REQUEST_THRESHOLD,
    EXECUTION_BURST_THRESHOLD,
    EXTERNAL_API_ABUSE_THRESHOLD,
    POLICY_VIOLATION_THRESHOLD,
    WINDOW_HOURS,
)
from app.services.threats.types import ThreatFinding


class ThreatDetectorContext:
    def __init__(self, db: AsyncSession, *, user_id: UUID | None = None):
        self.db = db
        self.user_id = user_id
        self.since = datetime.now(UTC) - timedelta(hours=WINDOW_HOURS)


async def detect_prompt_injection_and_jailbreak(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    findings: list[ThreatFinding] = []
    query = select(PromptScan).where(PromptScan.scanned_at >= ctx.since)
    if ctx.user_id:
        query = query.where(PromptScan.user_id == ctx.user_id)
    result = await ctx.db.execute(query.order_by(PromptScan.scanned_at.desc()).limit(200))
    for scan in result.scalars().all():
        raw_findings = scan.findings_json or []
        types = {f.get("finding_type") for f in raw_findings if isinstance(f, dict)}
        if FINDING_PROMPT_INJECTION in types:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_PROMPT_INJECTION,
                    category=CATEGORY_PROMPT_SECURITY,
                    severity=SEVERITY_CRITICAL,
                    title="Prompt injection attack detected",
                    description="A prompt scan detected injection patterns attempting to override system instructions.",
                    user_id=scan.user_id,
                    session_id=scan.session_id,
                    resource_type="prompt_scan",
                    resource_id=scan.id,
                    metadata={"decision": scan.decision, "risk_score": scan.risk_score},
                )
            )
        if FINDING_JAILBREAK in types:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_JAILBREAK,
                    category=CATEGORY_PROMPT_SECURITY,
                    severity=SEVERITY_CRITICAL,
                    title="Jailbreak attempt detected",
                    description="A prompt scan detected jailbreak or safety-bypass language.",
                    user_id=scan.user_id,
                    session_id=scan.session_id,
                    resource_type="prompt_scan",
                    resource_id=scan.id,
                    metadata={"decision": scan.decision, "risk_score": scan.risk_score},
                )
            )
    return findings


async def detect_suspicious_prompt_activity(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    query = (
        select(PromptScan.user_id, func.count())
        .where(
            PromptScan.scanned_at >= ctx.since,
            PromptScan.decision.in_(("block", "warn")),
        )
        .group_by(PromptScan.user_id)
    )
    if ctx.user_id:
        query = query.where(PromptScan.user_id == ctx.user_id)
    rows = (await ctx.db.execute(query)).all()
    findings: list[ThreatFinding] = []
    for uid, count in rows:
        if int(count) >= 3:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_SUSPICIOUS_PROMPT,
                    category=CATEGORY_PROMPT_SECURITY,
                    severity=SEVERITY_HIGH,
                    title="Suspicious prompt activity",
                    description=f"User submitted {count} blocked or warned prompts in {WINDOW_HOURS}h.",
                    user_id=uid,
                    metadata={"blocked_or_warned_count": int(count), "window_hours": WINDOW_HOURS},
                    recurrence_count=int(count),
                )
            )
    return findings


async def detect_excessive_blocked_requests(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    block_types = (PROMPT_BLOCKED, OUTPUT_BLOCKED, GUARD_PROMPT_BLOCKED, EXECUTION_BLOCKED)
    query = (
        select(DomainEvent.user_id, func.count())
        .where(DomainEvent.occurred_at >= ctx.since, DomainEvent.event_type.in_(block_types))
        .group_by(DomainEvent.user_id)
    )
    if ctx.user_id:
        query = query.where(DomainEvent.user_id == ctx.user_id)
    findings: list[ThreatFinding] = []
    for uid, count in (await ctx.db.execute(query)).all():
        if uid and int(count) >= BLOCKED_REQUEST_THRESHOLD:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_EXCESSIVE_BLOCKS,
                    category=CATEGORY_EXECUTION,
                    severity=SEVERITY_HIGH,
                    title="Excessive blocked requests",
                    description=f"{count} blocked events in the last {WINDOW_HOURS} hours.",
                    user_id=uid,
                    metadata={"blocked_count": int(count)},
                    recurrence_count=int(count),
                )
            )
    return findings


async def detect_repeated_policy_violations(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    query = (
        select(DomainEvent.user_id, func.count())
        .where(
            DomainEvent.occurred_at >= ctx.since,
            DomainEvent.event_type == POLICY_VIOLATION,
        )
        .group_by(DomainEvent.user_id)
    )
    if ctx.user_id:
        query = query.where(DomainEvent.user_id == ctx.user_id)
    findings: list[ThreatFinding] = []
    for uid, count in (await ctx.db.execute(query)).all():
        if uid and int(count) >= POLICY_VIOLATION_THRESHOLD:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_REPEATED_POLICY_VIOLATION,
                    category=CATEGORY_POLICY,
                    severity=SEVERITY_HIGH,
                    title="Repeated policy violations",
                    description=f"{count} policy violations detected in {WINDOW_HOURS}h.",
                    user_id=uid,
                    metadata={"violation_count": int(count)},
                    recurrence_count=int(count),
                )
            )
    return findings


async def detect_abnormal_execution_behavior(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    findings: list[ThreatFinding] = []
    query = (
        select(ExecutionRequest.user_id, func.count())
        .where(ExecutionRequest.created_at >= ctx.since)
        .group_by(ExecutionRequest.user_id)
    )
    if ctx.user_id:
        query = query.where(ExecutionRequest.user_id == ctx.user_id)
    for uid, count in (await ctx.db.execute(query)).all():
        if int(count) >= EXECUTION_BURST_THRESHOLD:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_ABNORMAL_EXECUTION,
                    category=CATEGORY_EXECUTION,
                    severity=SEVERITY_MEDIUM,
                    title="Abnormal execution volume",
                    description=f"{count} execution requests in {WINDOW_HOURS}h exceeds normal baseline.",
                    user_id=uid,
                    metadata={"execution_count": int(count)},
                    recurrence_count=int(count),
                )
            )

    interrupted_q = (
        select(ExecutionRequest.user_id, func.count())
        .where(
            ExecutionRequest.created_at >= ctx.since,
            ExecutionRequest.status.in_(("interrupted", "blocked")),
        )
        .group_by(ExecutionRequest.user_id)
    )
    if ctx.user_id:
        interrupted_q = interrupted_q.where(ExecutionRequest.user_id == ctx.user_id)
    for uid, count in (await ctx.db.execute(interrupted_q)).all():
        if int(count) >= 3:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_ABNORMAL_EXECUTION,
                    category=CATEGORY_EXECUTION,
                    severity=SEVERITY_HIGH,
                    title="Abnormal blocked/interrupted executions",
                    description=f"{count} executions blocked or interrupted in {WINDOW_HOURS}h.",
                    user_id=uid,
                    metadata={"interrupted_count": int(count)},
                    recurrence_count=int(count),
                )
            )
    return findings


async def detect_external_api_abuse(ctx: ThreatDetectorContext) -> list[ThreatFinding]:
    query = (
        select(ExecutionRequest.user_id, func.count())
        .where(
            ExecutionRequest.created_at >= ctx.since,
            ExecutionRequest.is_external_api.is_(True),
            ExecutionRequest.status.in_(("blocked", "interrupted", "failed")),
        )
        .group_by(ExecutionRequest.user_id)
    )
    if ctx.user_id:
        query = query.where(ExecutionRequest.user_id == ctx.user_id)
    findings: list[ThreatFinding] = []
    for uid, count in (await ctx.db.execute(query)).all():
        if int(count) >= EXTERNAL_API_ABUSE_THRESHOLD:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_EXTERNAL_API_ABUSE,
                    category=CATEGORY_API_ABUSE,
                    severity=SEVERITY_CRITICAL,
                    title="Repeated external API abuse",
                    description=(
                        f"{count} failed or blocked external API executions in {WINDOW_HOURS}h."
                    ),
                    user_id=uid,
                    metadata={"external_blocked_count": int(count)},
                    recurrence_count=int(count),
                )
            )
    return findings


async def detect_from_domain_event(
    ctx: ThreatDetectorContext, envelope: dict
) -> list[ThreatFinding]:
    """Real-time hints from a single domain event."""
    event_type = str(envelope.get("event_type", ""))
    user_raw = envelope.get("user_id")
    user_id = UUID(str(user_raw)) if user_raw else None
    inner = envelope.get("payload") or {}
    findings: list[ThreatFinding] = []

    if event_type == POLICY_VIOLATION:
        findings.append(
            ThreatFinding(
                threat_type=THREAT_REPEATED_POLICY_VIOLATION,
                category=CATEGORY_POLICY,
                severity=SEVERITY_HIGH,
                title="Policy violation event",
                description=inner.get("message") or "A policy violation was detected.",
                user_id=user_id,
                source_event_type=event_type,
                metadata=inner,
            )
        )
    elif event_type in (PROMPT_BLOCKED, GUARD_PROMPT_BLOCKED):
        reasons = inner.get("blocking_reasons") or inner.get("finding_types") or []
        reason_str = " ".join(str(r) for r in reasons).lower()
        if "injection" in reason_str or "prompt_injection" in reason_str:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_PROMPT_INJECTION,
                    category=CATEGORY_PROMPT_SECURITY,
                    severity=SEVERITY_CRITICAL,
                    title="Prompt injection blocked",
                    description="Prompt blocked due to injection patterns.",
                    user_id=user_id,
                    source_event_type=event_type,
                    metadata=inner,
                )
            )
        if "jailbreak" in reason_str:
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_JAILBREAK,
                    category=CATEGORY_PROMPT_SECURITY,
                    severity=SEVERITY_CRITICAL,
                    title="Jailbreak attempt blocked",
                    description="Prompt blocked due to jailbreak patterns.",
                    user_id=user_id,
                    source_event_type=event_type,
                    metadata=inner,
                )
            )
    elif event_type in (EXECUTION_BLOCKED, EXECUTION_INTERRUPTED):
        if inner.get("is_external_api") or inner.get("external"):
            findings.append(
                ThreatFinding(
                    threat_type=THREAT_EXTERNAL_API_ABUSE,
                    category=CATEGORY_API_ABUSE,
                    severity=SEVERITY_HIGH,
                    title="External API execution blocked",
                    description="An external API execution was blocked or interrupted.",
                    user_id=user_id,
                    source_event_type=event_type,
                    metadata=inner,
                )
            )
    return findings


ALL_THREAT_DETECTORS = [
    detect_prompt_injection_and_jailbreak,
    detect_suspicious_prompt_activity,
    detect_excessive_blocked_requests,
    detect_repeated_policy_violations,
    detect_abnormal_execution_behavior,
    detect_external_api_abuse,
]
