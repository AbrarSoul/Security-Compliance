"""Threat detection engine."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.threats.detectors import (
    ALL_THREAT_DETECTORS,
    ThreatDetectorContext,
    detect_from_domain_event,
)
from app.services.threats.types import ThreatFinding


class ThreatDetectionEngine:
    def __init__(self, db: AsyncSession, *, user_id=None):
        self._ctx = ThreatDetectorContext(db, user_id=user_id)

    async def run_batch(self) -> list[ThreatFinding]:
        findings: list[ThreatFinding] = []
        seen: set[str] = set()
        for detector in ALL_THREAT_DETECTORS:
            for f in await detector(self._ctx):
                fp = f.fingerprint()
                if fp not in seen:
                    seen.add(fp)
                    findings.append(f)
        return findings

    async def analyze_event(self, envelope: dict[str, Any]) -> list[ThreatFinding]:
        return await detect_from_domain_event(self._ctx, envelope)
