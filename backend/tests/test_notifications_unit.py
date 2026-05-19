"""Unit tests for notification mapping and preferences."""

from app.services.events.constants import (
    EXECUTION_INTERRUPTED,
    POLICY_VIOLATION,
    PROMPT_BLOCKED,
    RULE_TRIGGERED,
    SUSPICIOUS_ACTIVITY,
)
from app.services.notifications.constants import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_ORDER,
    TYPE_HIGH_RISK_EXECUTION,
    TYPE_POLICY_VIOLATION,
    TYPE_PROMPT_BLOCKED,
    TYPE_SUSPICIOUS_ACTIVITY,
)
from app.services.notifications.event_mapper import map_event_to_spec


def test_map_prompt_blocked():
    spec = map_event_to_spec(
        PROMPT_BLOCKED,
        {
            "event_type": PROMPT_BLOCKED,
            "severity": "high",
            "payload": {"reason": "PII detected"},
        },
    )
    assert spec is not None
    assert spec.notification_type == TYPE_PROMPT_BLOCKED
    assert spec.severity == SEVERITY_HIGH
    assert "PII" in spec.message


def test_map_policy_violation_notifies_admins():
    spec = map_event_to_spec(
        POLICY_VIOLATION,
        {"event_type": POLICY_VIOLATION, "payload": {"policy_name": "data-retention"}},
    )
    assert spec is not None
    assert spec.notification_type == TYPE_POLICY_VIOLATION
    assert spec.notify_admins is True


def test_map_suspicious_activity_critical():
    spec = map_event_to_spec(
        SUSPICIOUS_ACTIVITY,
        {"event_type": SUSPICIOUS_ACTIVITY, "payload": {"detail": "rate limit"}},
    )
    assert spec is not None
    assert spec.notification_type == TYPE_SUSPICIOUS_ACTIVITY
    assert spec.severity == SEVERITY_CRITICAL


def test_map_rule_triggered_only_on_block():
    assert map_event_to_spec(RULE_TRIGGERED, {"payload": {"action": "warn"}}) is None
    spec = map_event_to_spec(
        RULE_TRIGGERED,
        {"event_type": RULE_TRIGGERED, "payload": {"action": "block", "rule_name": "no-pii"}},
    )
    assert spec is not None
    assert spec.notification_type == TYPE_POLICY_VIOLATION


def test_map_execution_interrupted_high_risk():
    spec = map_event_to_spec(
        EXECUTION_INTERRUPTED,
        {
            "event_type": EXECUTION_INTERRUPTED,
            "payload": {"risk_score": 85},
        },
    )
    assert spec is not None
    assert spec.notification_type == TYPE_HIGH_RISK_EXECUTION
    assert spec.severity == SEVERITY_CRITICAL


def test_severity_order_for_email_threshold():
    assert SEVERITY_ORDER["critical"] >= SEVERITY_ORDER["high"]
    assert SEVERITY_ORDER["high"] >= SEVERITY_ORDER["warning"]
