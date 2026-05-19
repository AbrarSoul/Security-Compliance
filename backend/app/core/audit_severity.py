"""Audit log severity levels."""

INFO = "info"
LOW = "low"
MEDIUM = "medium"
HIGH = "high"
CRITICAL = "critical"

ALL: tuple[str, ...] = (INFO, LOW, MEDIUM, HIGH, CRITICAL)
