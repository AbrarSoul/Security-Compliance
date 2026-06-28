"""User registration approval states."""

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"

APPROVAL_STATUSES = frozenset({APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED})
