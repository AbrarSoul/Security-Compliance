"""Create and deliver compliance notifications (Sprint 3 Step 6)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.services.notifications.constants import (
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_SENT,
    EMAIL_STATUS_SKIPPED,
    REPEATED_VIOLATION_THRESHOLD,
    REPEATED_VIOLATION_WINDOW_HOURS,
    SEVERITY_CRITICAL,
    SEVERITY_ORDER,
    TYPE_REPEATED_VIOLATION,
    TYPE_SYSTEM_SECURITY,
)
from app.services.notifications.email_sender import NotificationEmailSender
from app.services.notifications.event_mapper import NotificationSpec, map_event_to_spec
from app.services.notifications.pubsub import notification_pubsub


class NotificationService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        email_sender: NotificationEmailSender | None = None,
    ):
        self.db = db
        self.repo = NotificationRepository(db)
        self._email = email_sender or NotificationEmailSender()

    async def process_domain_event(self, envelope: dict[str, Any]) -> list[Notification]:
        event_type = str(envelope.get("event_type", ""))
        spec = map_event_to_spec(event_type, envelope)
        if spec is None:
            return []

        user_id_raw = envelope.get("user_id")
        if not user_id_raw:
            return []
        user_id = UUID(str(user_id_raw))

        created: list[Notification] = []
        primary = await self._deliver_to_user(user_id, spec, envelope)
        if primary:
            created.append(primary)
            await self._maybe_repeated_violation(user_id, spec, envelope, created)

        if spec.notify_admins:
            admin_ids = await self.repo.list_user_ids_by_role("admin")
            for admin_id in admin_ids:
                if admin_id == user_id:
                    continue
                admin_spec = NotificationSpec(
                    notification_type=TYPE_SYSTEM_SECURITY,
                    severity=SEVERITY_CRITICAL,
                    title=f"[Admin] {spec.title}",
                    message=spec.message,
                    notify_admins=False,
                )
                row = await self._deliver_to_user(admin_id, admin_spec, envelope)
                if row:
                    created.append(row)

        return created

    async def _deliver_to_user(
        self,
        user_id: UUID,
        spec: NotificationSpec,
        envelope: dict[str, Any],
    ) -> Notification | None:
        prefs = await self.repo.get_or_create_preferences(user_id)
        if not self._type_enabled(prefs, spec.notification_type):
            return None

        resource_id = envelope.get("resource_id")
        rid = UUID(str(resource_id)) if resource_id else None

        notification = Notification(
            user_id=user_id,
            notification_type=spec.notification_type,
            severity=spec.severity,
            title=spec.title,
            message=spec.message,
            event_type=str(envelope.get("event_type")),
            resource_type=envelope.get("resource_type"),
            resource_id=rid,
            metadata_json={
                "session_id": envelope.get("session_id"),
                "event_id": envelope.get("event_id"),
                "payload": envelope.get("payload"),
            },
        )
        await self.repo.create(notification)

        if prefs.email_enabled and self._meets_email_severity(prefs.email_min_severity, spec.severity):
            await self._send_email(user_id, notification)
        else:
            notification.email_status = EMAIL_STATUS_SKIPPED

        await self.repo.db.flush()

        if prefs.in_app_enabled or prefs.dashboard_alerts_enabled:
            await notification_pubsub.publish(
                user_id,
                self._to_alert_payload(notification),
            )

        return notification

    async def _send_email(self, user_id: UUID, notification: Notification) -> None:
        email = await self.repo.get_user_email(user_id)
        if not email:
            notification.email_status = EMAIL_STATUS_SKIPPED
            return

        subject = f"[ComplianceGuard] {notification.title}"
        body = f"{notification.message}\n\nSeverity: {notification.severity}\nType: {notification.notification_type}"
        ok, status = self._email.send(to_email=email, subject=subject, body=body)
        notification.email_status = EMAIL_STATUS_SENT if ok else (
            EMAIL_STATUS_FAILED if status == "failed" else EMAIL_STATUS_SKIPPED
        )
        if ok:
            notification.email_sent_at = datetime.now(UTC)

    async def _maybe_repeated_violation(
        self,
        user_id: UUID,
        spec: NotificationSpec,
        envelope: dict[str, Any],
        created: list[Notification],
    ) -> None:
        count = await self.repo.count_recent_by_type(
            user_id,
            spec.notification_type,
            window_hours=REPEATED_VIOLATION_WINDOW_HOURS,
        )
        if count != REPEATED_VIOLATION_THRESHOLD:
            return

        prefs = await self.repo.get_or_create_preferences(user_id)
        if not prefs.notify_repeated_violation:
            return

        repeat_spec = NotificationSpec(
            notification_type=TYPE_REPEATED_VIOLATION,
            severity=SEVERITY_CRITICAL,
            title="Repeated compliance violations",
            message=(
                f"You have {count} '{spec.notification_type}' notifications "
                f"in the last {REPEATED_VIOLATION_WINDOW_HOURS} hours."
            ),
            notify_admins=True,
        )
        row = await self._deliver_to_user(user_id, repeat_spec, envelope)
        if row:
            created.append(row)

    @staticmethod
    def _type_enabled(prefs, notification_type: str) -> bool:
        mapping = {
            "prompt_blocked": prefs.notify_prompt_blocked,
            "output_blocked": prefs.notify_output_blocked,
            "policy_violation": prefs.notify_policy_violation,
            "suspicious_activity": prefs.notify_suspicious_activity,
            "high_risk_execution": prefs.notify_high_risk_execution,
            "repeated_violation": prefs.notify_repeated_violation,
            "system_security_alert": prefs.notify_system_security,
        }
        return mapping.get(notification_type, True)

    @staticmethod
    def _meets_email_severity(min_severity: str, actual: str) -> bool:
        return SEVERITY_ORDER.get(actual, 0) >= SEVERITY_ORDER.get(min_severity, 2)

    @staticmethod
    def _to_alert_payload(notification: Notification) -> dict[str, Any]:
        return {
            "id": str(notification.id),
            "notification_type": notification.notification_type,
            "severity": notification.severity,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "event_type": notification.event_type,
            "resource_type": notification.resource_type,
            "resource_id": str(notification.resource_id) if notification.resource_id else None,
        }
