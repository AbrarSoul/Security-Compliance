"""Compliance gap analysis engine."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gaps.rules import ALL_GAP_DETECTORS, GapRuleContext
from app.services.gaps.types import GapFinding


class GapAnalysisEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._ctx = GapRuleContext(db)

    async def run_all(self) -> list[GapFinding]:
        findings: list[GapFinding] = []
        seen: set[str] = set()
        for detector in ALL_GAP_DETECTORS:
            batch = await detector(self._ctx)
            for f in batch:
                fp = f.fingerprint()
                if fp not in seen:
                    seen.add(fp)
                    findings.append(f)
        return findings
