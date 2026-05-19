"""SMTP email delivery for compliance notifications."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class NotificationEmailSender:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def send(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
    ) -> tuple[bool, str]:
        """
        Send email. Returns (success, status).
        When SMTP is disabled, logs and returns skipped status.
        """
        if not self._settings.smtp_enabled:
            logger.info(
                "Notification email (SMTP disabled) to=%s subject=%s",
                to_email,
                subject,
            )
            return False, "skipped"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._settings.smtp_from
        msg["To"] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(
                self._settings.smtp_host,
                self._settings.smtp_port,
                timeout=self._settings.smtp_timeout_seconds,
            ) as smtp:
                if self._settings.smtp_use_tls:
                    smtp.starttls()
                if self._settings.smtp_user and self._settings.smtp_password:
                    smtp.login(self._settings.smtp_user, self._settings.smtp_password)
                smtp.send_message(msg)
            return True, "sent"
        except Exception:
            logger.exception("Failed to send notification email to %s", to_email)
            return False, "failed"
