"""Security monitoring, threat persistence, alerting, and user behavior analysis."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit_severity
from app.core.audit_actions import AuditAction
from app.models.notification import Notification
from app.models.security_threat import SecurityEventLog, SecurityThreat, ThreatDetectionRun
from app.repositories.notification_repository import NotificationRepository
from app.repositories.threat_repository import ThreatRepository
from app.services.audit_service import AuditService
from app.services.events.constants import SUSPICIOUS_ACTIVITY
from app.services.events.dispatcher import EventDispatcher
from app.services.events.types import DomainEventEnvelope
from app.services.notifications.constants import (
    SEVERITY_CRITICAL,
    TYPE_SUSPICIOUS_ACTIVITY,
)
from app.services.notifications.pubsub import notification_pubsub
from app.services.threats.constants import (
    SECURITY_EVENT_ANALYSIS_RUN,
    SECURITY_EVENT_THREAT_DETECTED,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    THREAT_STATUS_INVESTIGATING,
    THREAT_STATUS_OPEN,
    THREAT_STATUS_RESOLVED,
)
from app.services.threats.scoring import aggregate_security_posture, compute_threat_score
from app.services.threats.threat_engine import ThreatDetectionEngine
from app.services.threats.types import ThreatFinding


class SecurityMonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ThreatRepository(db)
        self.audit = AuditService(db)
        self._notifications = NotificationRepository(db)

    async def run_detection(self, *, triggered_by_user_id: UUID | None) -> ThreatDetectionRun:
        engine = ThreatDetectionEngine(self.db)
        findings = await engine.run_batch()

        run = ThreatDetectionRun(
            triggered_by_user_id=triggered_by_user_id,
            started_at=datetime.now(UTC),
        )
        await self.repo.create_run(run)

        counts = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0}
        threats: list[SecurityThreat] = []

        for finding in findings:
            threat = await self._persist_finding(
                finding, detection_run_id=run.id, counts=counts
            )
            threats.append(threat)

        run.threats_found = len(threats)
        run.critical_count = counts.get(SEVERITY_CRITICAL, 0)
        run.high_count = counts.get(SEVERITY_HIGH, 0)
        run.medium_count = counts.get(SEVERITY_MEDIUM, 0)
        run.low_count = counts.get(SEVERITY_LOW, 0)
        run.completed_at = datetime.now(UTC)
        run.summary_json = {
            "security_posture": aggregate_security_posture(threats),
            "threat_types": list({t.threat_type for t in threats}),
        }
        await self.db.flush()

        await self._log_security_event(
            event_type=SECURITY_EVENT_ANALYSIS_RUN,
            message=f"Threat analysis completed: {run.threats_found} threats found",
            user_id=triggered_by_user_id,
            severity=audit_severity.INFO,
            payload=run.summary_json,
        )
        await self.audit.log(
            AuditAction.THREAT_ANALYSIS_RUN,
            user_id=triggered_by_user_id,
            resource_type="threat_detection_run",
            resource_id=run.id,
            severity=audit_severity.INFO,
            metadata={"threats_found": run.threats_found, **(run.summary_json or {})},
        )
        return run

    async def process_domain_event(self, envelope: dict[str, Any]) -> list[SecurityThreat]:
        if envelope.get("resource_type") == "security_threat":
            return []
        engine = ThreatDetectionEngine(self.db)
        findings = await engine.analyze_event(envelope)
        created: list[SecurityThreat] = []
        counts: dict[str, int] = {}
        for finding in findings:
            threat = await self._persist_finding(finding, counts=counts)
            created.append(threat)
        return created

    async def _persist_finding(
        self,
        finding: ThreatFinding,
        *,
        detection_run_id: UUID | None = None,
        counts: dict[str, int] | None = None,
    ) -> SecurityThreat:
        score = compute_threat_score(finding.severity, finding.recurrence_count)
        threat = SecurityThreat(
            detection_run_id=detection_run_id,
            user_id=finding.user_id,
            threat_type=finding.threat_type,
            category=finding.category,
            severity=finding.severity,
            threat_score=score,
            title=finding.title,
            description=finding.description,
            status=THREAT_STATUS_OPEN,
            fingerprint=finding.fingerprint(),
            source_event_type=finding.source_event_type,
            session_id=finding.session_id,
            resource_type=finding.resource_type,
            resource_id=finding.resource_id,
            metadata_json=finding.metadata or None,
        )
        await self.repo.create_threat(threat)
        if counts is not None:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1

        await self._log_security_event(
            event_type=SECURITY_EVENT_THREAT_DETECTED,
            message=finding.title,
            user_id=finding.user_id,
            threat_id=threat.id,
            threat_type=finding.threat_type,
            severity=finding.severity,
            payload=finding.metadata,
        )

        await self.audit.log(
            AuditAction.THREAT_DETECTED,
            user_id=finding.user_id,
            resource_type="security_threat",
            resource_id=threat.id,
            severity=finding.severity,
            metadata={"threat_type": finding.threat_type, "threat_score": score},
        )
        await self._alert_threat(threat, finding)
        return threat

    async def _log_security_event(
        self,
        *,
        event_type: str,
        message: str,
        user_id: UUID | None = None,
        threat_id: UUID | None = None,
        threat_type: str | None = None,
        severity: str = audit_severity.INFO,
        payload: dict | None = None,
    ) -> SecurityEventLog:
        log = SecurityEventLog(
            user_id=user_id,
            threat_id=threat_id,
            event_type=event_type,
            threat_type=threat_type,
            severity=severity,
            message=message,
            payload_json=payload,
        )
        return await self.repo.create_event_log(log)

    async def _alert_threat(self, threat: SecurityThreat, finding: ThreatFinding) -> None:
        if threat.user_id is None:
            return
        prefs = await self._notifications.get_or_create_preferences(threat.user_id)
        if not prefs.notify_suspicious_activity:
            return

        notification = Notification(
            user_id=threat.user_id,
            notification_type=TYPE_SUSPICIOUS_ACTIVITY,
            severity=threat.severity,
            title=threat.title,
            message=threat.description,
            event_type=SUSPICIOUS_ACTIVITY,
            resource_type="security_threat",
            resource_id=threat.id,
            metadata_json={"threat_type": threat.threat_type, "threat_score": threat.threat_score},
        )
        await self._notifications.create(notification)

        if prefs.in_app_enabled or prefs.dashboard_alerts_enabled:
            await notification_pubsub.publish(
                threat.user_id,
                {
                    "id": str(notification.id),
                    "notification_type": TYPE_SUSPICIOUS_ACTIVITY,
                    "severity": threat.severity,
                    "title": threat.title,
                    "message": threat.description,
                    "threat_id": str(threat.id),
                },
            )

        dispatcher = EventDispatcher(self.db)
        await dispatcher.publish(
            DomainEventEnvelope(
                event_type=SUSPICIOUS_ACTIVITY,
                user_id=threat.user_id,
                session_id=finding.session_id,
                resource_type="security_threat",
                resource_id=threat.id,
                severity=threat.severity,
                payload={
                    "threat_type": threat.threat_type,
                    "title": threat.title,
                    "threat_score": threat.threat_score,
                },
            )
        )

    async def get_dashboard(self, *, user_id: UUID | None, can_read_all: bool):
        scope_user = None if can_read_all else user_id
        open_threats, total = await self.repo.list_open_threats(
            user_id=scope_user, limit=25
        )
        latest_run = await self.repo.get_latest_run()
        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for t in open_threats:
            by_severity[t.severity] = by_severity.get(t.severity, 0) + 1
            by_type[t.threat_type] = by_type.get(t.threat_type, 0) + 1
        posture = aggregate_security_posture(open_threats)
        if latest_run and latest_run.summary_json:
            posture = latest_run.summary_json.get("security_posture", posture)
        return {
            "open_threats": open_threats,
            "open_total": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "security_posture": posture,
            "latest_run": latest_run,
        }

    async def analyze_user_behavior(self, *, user_id: UUID | None, can_read_all: bool):
        since = datetime.now(UTC) - timedelta(hours=24)
        rows = await self.repo.count_threats_by_user(since)
        if not can_read_all and user_id:
            rows = [(uid, c, avg) for uid, c, avg in rows if uid == user_id]
        return [
            {
                "user_id": str(uid),
                "threat_count": count,
                "avg_threat_score": round(avg, 1),
                "risk_level": (
                    "critical" if avg >= 85 else "high" if avg >= 70 else "medium" if avg >= 50 else "low"
                ),
            }
            for uid, count, avg in rows
        ]

    async def investigate_threat(self, threat_id: UUID, actor_id: UUID) -> SecurityThreat:
        threat = await self.repo.get_threat(threat_id)
        if threat is None:
            raise ValueError("Threat not found")
        await self.repo.update_threat_status(threat, THREAT_STATUS_INVESTIGATING)
        await self.audit.log(
            AuditAction.THREAT_INVESTIGATING,
            user_id=actor_id,
            resource_type="security_threat",
            resource_id=threat.id,
            severity=audit_severity.INFO,
        )
        return threat

    async def resolve_threat(self, threat_id: UUID, actor_id: UUID) -> SecurityThreat:
        threat = await self.repo.get_threat(threat_id)
        if threat is None:
            raise ValueError("Threat not found")
        await self.repo.update_threat_status(
            threat, THREAT_STATUS_RESOLVED, resolved_at=datetime.now(UTC)
        )
        await self.audit.log(
            AuditAction.THREAT_RESOLVED,
            user_id=actor_id,
            resource_type="security_threat",
            resource_id=threat.id,
            severity=audit_severity.INFO,
        )
        return threat
