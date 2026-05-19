"""Sprint 3 Step 10: performance indexes for monitoring and analytics

Revision ID: 025
Revises: 024
Create Date: 2026-05-19

"""

from typing import Sequence, Union

from alembic import op

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Outbox worker claims pending rows ordered by created_at
    op.create_index(
        "ix_event_outbox_status_created",
        "event_outbox",
        ["status", "created_at"],
        unique=False,
    )
    # Analytics / threat detectors filter by user + time
    op.create_index(
        "ix_domain_events_user_occurred",
        "domain_events",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_scans_user_scanned",
        "prompt_scans",
        ["user_id", "scanned_at"],
        unique=False,
    )
    op.create_index(
        "ix_output_scans_user_scanned",
        "output_scans",
        ["user_id", "scanned_at"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "is_read", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_security_threats_user_status_detected",
        "security_threats",
        ["user_id", "status", "detected_at"],
        unique=False,
    )
    op.create_index(
        "ix_execution_requests_user_created",
        "execution_requests",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_guard_enforcement_user_created",
        "guard_enforcement_logs",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_guard_enforcement_user_created", table_name="guard_enforcement_logs")
    op.drop_index("ix_execution_requests_user_created", table_name="execution_requests")
    op.drop_index("ix_security_threats_user_status_detected", table_name="security_threats")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_output_scans_user_scanned", table_name="output_scans")
    op.drop_index("ix_prompt_scans_user_scanned", table_name="prompt_scans")
    op.drop_index("ix_domain_events_user_occurred", table_name="domain_events")
    op.drop_index("ix_event_outbox_status_created", table_name="event_outbox")
