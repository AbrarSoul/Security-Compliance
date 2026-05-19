"""Map domain events to notification specs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.permissions import ROLE_ADMIN
from app.services.events.constants import (
    EXECUTION_BLOCKED,
    EXECUTION_INTERRUPTED,
    GUARD_OUTPUT_BLOCKED,
    GUARD_PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    POLICY_VIOLATION,
    PROMPT_BLOCKED,
    RULE_TRIGGERED,
    SUSPICIOUS_ACTIVITY,
)
from app.services.notifications.constants import (
    SEVERITIES,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_WARNING,
    TYPE_HIGH_RISK_EXECUTION,
    TYPE_OUTPUT_BLOCKED,
    TYPE_POLICY_VIOLATION,
    TYPE_PROMPT_BLOCKED,
    TYPE_SUSPICIOUS_ACTIVITY,
    TYPE_SYSTEM_SECURITY,
)

_NOTIFY_EVENT_TYPES = frozenset(
    {
        PROMPT_BLOCKED,
        OUTPUT_BLOCKED,
        POLICY_VIOLATION,
        SUSPICIOUS_ACTIVITY,
        EXECUTION_BLOCKED,
        EXECUTION_INTERRUPTED,
        GUARD_PROMPT_BLOCKED,
        GUARD_OUTPUT_BLOCKED,
        RULE_TRIGGERED,
    }
)


@dataclass(frozen=True)
class NotificationSpec:
    notification_type: str
    severity: str
    title: str
    message: str
    notify_admins: bool = False


def _parse_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _risk_score(payload: dict[str, Any], inner: dict[str, Any]) -> int | None:
    for key in ("risk_score", "score"):
        raw = inner.get(key) if key in inner else payload.get(key)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    return None


def map_event_to_spec(event_type: str, envelope: dict[str, Any]) -> NotificationSpec | None:
    if event_type not in _NOTIFY_EVENT_TYPES:
        return None

    inner = envelope.get("payload") or {}
    severity_raw = str(envelope.get("severity") or inner.get("severity") or SEVERITY_WARNING)
    risk = _risk_score(envelope, inner)

    if event_type in (PROMPT_BLOCKED, GUARD_PROMPT_BLOCKED):
        return NotificationSpec(
            notification_type=TYPE_PROMPT_BLOCKED,
            severity=severity_raw if severity_raw in SEVERITIES else SEVERITY_HIGH,
            title="Prompt blocked",
            message=inner.get("reason") or inner.get("message") or "A prompt was blocked by compliance policy.",
        )

    if event_type in (OUTPUT_BLOCKED, GUARD_OUTPUT_BLOCKED):
        return NotificationSpec(
            notification_type=TYPE_OUTPUT_BLOCKED,
            severity=severity_raw if severity_raw in SEVERITIES else SEVERITY_HIGH,
            title="Output blocked",
            message=inner.get("reason") or inner.get("message") or "Model output was blocked before display.",
        )

    if event_type == POLICY_VIOLATION:
        return NotificationSpec(
            notification_type=TYPE_POLICY_VIOLATION,
            severity=SEVERITY_HIGH,
            title="Policy violation",
            message=inner.get("message") or inner.get("policy_name") or "A compliance policy was violated.",
            notify_admins=True,
        )

    if event_type == SUSPICIOUS_ACTIVITY:
        return NotificationSpec(
            notification_type=TYPE_SUSPICIOUS_ACTIVITY,
            severity=SEVERITY_CRITICAL,
            title="Suspicious activity detected",
            message=inner.get("message") or inner.get("detail") or "Suspicious activity was detected.",
            notify_admins=True,
        )

    if event_type == RULE_TRIGGERED:
        action = str(inner.get("action", "")).lower()
        if action not in ("block", "deny", "reject"):
            return None
        return NotificationSpec(
            notification_type=TYPE_POLICY_VIOLATION,
            severity=SEVERITY_WARNING,
            title="Compliance rule triggered",
            message=inner.get("rule_name") or inner.get("message") or "A runtime rule was triggered.",
        )

    if event_type in (EXECUTION_BLOCKED, EXECUTION_INTERRUPTED):
        sev = SEVERITY_CRITICAL if event_type == EXECUTION_INTERRUPTED else SEVERITY_HIGH
        if risk is not None and risk >= 70:
            sev = SEVERITY_CRITICAL
        return NotificationSpec(
            notification_type=TYPE_HIGH_RISK_EXECUTION,
            severity=sev,
            title="High-risk execution",
            message=inner.get("message")
            or (
                "Execution was interrupted by the compliance guard."
                if event_type == EXECUTION_INTERRUPTED
                else "Execution was blocked due to compliance risk."
            ),
            notify_admins=sev == SEVERITY_CRITICAL,
        )

    return None


def should_notify_admins(spec: NotificationSpec) -> bool:
    return spec.notify_admins


def admin_role_name() -> str:
    return ROLE_ADMIN
