"""AI application registration approval workflow statuses."""

REGISTRATION_PENDING_AUDITOR = "pending_auditor"
REGISTRATION_PENDING_ADMIN = "pending_admin"
REGISTRATION_APPROVED = "approved"
REGISTRATION_REJECTED = "rejected"

REGISTRATION_STATUSES = frozenset(
    {
        REGISTRATION_PENDING_AUDITOR,
        REGISTRATION_PENDING_ADMIN,
        REGISTRATION_APPROVED,
        REGISTRATION_REJECTED,
    }
)
