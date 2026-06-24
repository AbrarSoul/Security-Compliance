"""GAIRA assessment orchestration."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gaira import AIApplication, GairaAssessment
from app.repositories.compliance_model_repository import ComplianceModelRepository
from app.repositories.gaira_repository import GairaRepository
from app.repositories.scan_repository import ScanRepository
from app.services.gaira.constants import (
    ASSESSMENT_TYPES,
    CHECK_STATUS_DONE,
    CHECK_STATUS_IN_PROGRESS,
    CHECK_STATUS_NONE,
    GAIRA_STATUS_DONE,
    GAIRA_STATUS_IN_PROGRESS,
    GAIRA_STATUS_NONE,
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_SUPERSEDED,
)
from app.services.gaira.engine import compute_assessment, normalize_risk_level
from app.services.gaira.framework import GairaFramework, get_gaira_framework


class GairaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GairaRepository(db)
        self.scans = ScanRepository(db)
        self.models = ComplianceModelRepository(db)
        self.framework = get_gaira_framework()

    def get_framework(self) -> GairaFramework:
        return self.framework

    async def create_application(
        self,
        *,
        payload: dict,
        created_by_user_id: UUID,
    ) -> AIApplication:
        application = AIApplication(
            name=payload["name"],
            code=payload.get("code"),
            company=payload.get("company"),
            department=payload.get("department"),
            owner_name=payload.get("owner_name"),
            purpose=payload.get("purpose"),
            audience=payload.get("audience"),
            scope_includes=payload.get("scope_includes"),
            scope_excludes=payload.get("scope_excludes"),
            technology_description=payload.get("technology_description"),
            ai_provider=payload.get("ai_provider"),
            compliance_model_id=payload.get("compliance_model_id"),
            metadata_json=payload.get("metadata_json"),
            created_by_user_id=created_by_user_id,
            gaira_status=GAIRA_STATUS_NONE,
            compliance_check_status=CHECK_STATUS_NONE,
            dpia_status=CHECK_STATUS_NONE,
        )
        return await self.repo.create_application(application)

    async def update_application(self, application_id: UUID, payload: dict) -> AIApplication:
        application = await self.repo.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        for field in (
            "name",
            "code",
            "company",
            "department",
            "owner_name",
            "purpose",
            "audience",
            "scope_includes",
            "scope_excludes",
            "technology_description",
            "ai_provider",
            "compliance_model_id",
            "ai_act_category",
            "risk_level",
            "deployed_at",
            "next_assessment_at",
            "is_active",
            "metadata_json",
        ):
            if field in payload and payload[field] is not None:
                setattr(application, field, payload[field])
        return await self.repo.update_application(application)

    async def get_application(self, application_id: UUID) -> AIApplication | None:
        return await self.repo.get_application(application_id)

    async def list_applications(
        self, *, active_only: bool = True, limit: int = 50, offset: int = 0
    ) -> tuple[list[AIApplication], int]:
        return await self.repo.list_applications(
            active_only=active_only, limit=limit, offset=offset
        )

    async def start_assessment(
        self,
        application_id: UUID,
        *,
        assessment_type: str,
        created_by_user_id: UUID,
        scan_id: UUID | None = None,
    ) -> GairaAssessment:
        if assessment_type not in ASSESSMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid assessment_type. Expected one of: {', '.join(ASSESSMENT_TYPES)}",
            )

        application = await self.repo.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        if scan_id is not None:
            scan = await self.scans.get_by_id(scan_id)
            if scan is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

        answers = await self._build_prefill(application, scan_id=scan_id)

        assessment = GairaAssessment(
            application_id=application_id,
            assessment_type=assessment_type,
            status=STATUS_DRAFT,
            framework_version=self.framework.version,
            answers_json=answers,
            scan_id=scan_id,
            created_by_user_id=created_by_user_id,
        )
        assessment = await self.repo.create_assessment(assessment)

        if assessment_type in {"gaira_light", "gaira_comprehensive"}:
            application.gaira_status = GAIRA_STATUS_IN_PROGRESS
        elif assessment_type == "compliance_check":
            application.compliance_check_status = CHECK_STATUS_IN_PROGRESS
        await self.repo.update_application(application)
        return assessment

    async def update_answers(
        self,
        assessment_id: UUID,
        *,
        answers: dict,
        merge: bool = True,
    ) -> GairaAssessment:
        assessment = await self.repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        if assessment.status == STATUS_SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submitted assessments cannot be edited",
            )

        current = dict(assessment.answers_json or {})
        if merge:
            current.update(answers)
        else:
            current = answers
        assessment.answers_json = current
        return await self.repo.update_assessment(assessment)

    async def compute_assessment(self, assessment_id: UUID) -> GairaAssessment:
        assessment = await self.repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

        module = self.framework.get_module(assessment.assessment_type)
        questions = module.get("questions", []) if module else []
        result = compute_assessment(
            assessment.assessment_type,
            assessment.answers_json or {},
            questions,
        )
        assessment.computed_json = asdict(result)
        if result.risk_level:
            assessment.overall_risk_level = result.risk_level
        return await self.repo.update_assessment(assessment)

    async def get_assessment(self, assessment_id: UUID) -> GairaAssessment | None:
        return await self.repo.get_assessment(assessment_id)

    async def submit_assessment(
        self,
        assessment_id: UUID,
        *,
        user_id: UUID,
        overall_risk_level: str | None = None,
        proceed_decision: str | None = None,
        decision_comments: str | None = None,
    ) -> GairaAssessment:
        assessment = await self.compute_assessment(assessment_id)
        computed = assessment.computed_json or {}
        flags = computed.get("flags") or []

        if "second_line_required" in flags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Second-line review is required for flagged Step 4 answers before submit",
            )

        previous = await self.repo.get_latest_submitted_assessment(
            assessment.application_id, assessment.assessment_type
        )

        assessment.status = STATUS_SUBMITTED
        assessment.submitted_at = datetime.now(UTC)
        assessment.decision_by_user_id = user_id
        if overall_risk_level:
            assessment.overall_risk_level = normalize_risk_level(overall_risk_level)
        if proceed_decision:
            assessment.proceed_decision = proceed_decision
        if decision_comments:
            assessment.decision_comments = decision_comments

        application = assessment.application
        if application is None:
            application = await self.repo.get_application(assessment.application_id)

        if assessment.assessment_type in {"gaira_light", "gaira_comprehensive", "ai_risk_levels"}:
            application.gaira_status = GAIRA_STATUS_DONE
            if assessment.overall_risk_level:
                application.risk_level = assessment.overall_risk_level
        if assessment.assessment_type == "compliance_check":
            application.compliance_check_status = CHECK_STATUS_DONE

        if previous and previous.id != assessment.id:
            previous.status = STATUS_SUPERSEDED
            await self.repo.update_assessment(previous)

        await self.repo.update_assessment(assessment)
        await self.repo.update_application(application)
        return assessment

    async def _build_prefill(
        self, application: AIApplication, *, scan_id: UUID | None
    ) -> dict:
        answers: dict = {}

        metadata_map = {
            "company": "company",
            "department": "department",
            "application_owner": "owner_name",
            "name_of_application": "name",
            "scope_of_assessment_includes": "scope_includes",
            "scope_of_assessment_does_not_include": "scope_excludes",
        }
        for meta_key, attr in metadata_map.items():
            value = getattr(application, attr, None)
            if value:
                answers[meta_key] = {"value": value, "source": "application"}

        if application.purpose:
            answers["1.02"] = {"value": application.purpose, "source": "application"}
        if application.technology_description:
            answers["1.05"] = {
                "value": application.technology_description,
                "source": "application",
            }
        if application.ai_provider:
            answers["1.06"] = {"value": application.ai_provider, "source": "application"}

        if application.compliance_model_id:
            model = await self.models.get_by_id(application.compliance_model_id)
            if model:
                if model.provider:
                    answers.setdefault(
                        "1.06",
                        {"value": model.provider, "source": "compliance_model"},
                    )
                if model.data_leaves_platform:
                    answers["4.01"] = {
                        "value": "Yes",
                        "source": "compliance_model",
                        "note": "Model metadata indicates data leaves platform",
                    }
                if model.logging_enabled is False:
                    answers["4.20"] = {
                        "value": "No",
                        "source": "compliance_model",
                        "flagged": True,
                    }

        if scan_id:
            scan = await self.scans.get_by_id(scan_id)
            if scan and scan.findings:
                pii_types = {
                    "email",
                    "phone",
                    "name",
                    "pii",
                    "personal_data",
                    "ssn",
                    "credit_card",
                }
                has_pii = any(f.finding_type in pii_types for f in scan.findings)
                if has_pii:
                    answers["4.06"] = {
                        "value": "Yes",
                        "source": "scan",
                        "note": "Scan detected personal data in dataset",
                    }

        return answers

    def roaia_rows(self, applications: list[AIApplication]) -> list[dict]:
        rows = []
        for app in applications:
            latest = None
            if app.assessments:
                submitted = [a for a in app.assessments if a.status == STATUS_SUBMITTED]
                latest = submitted[0] if submitted else app.assessments[0]
            rows.append(
                {
                    "id": str(app.id),
                    "name": app.name,
                    "purpose": app.purpose,
                    "owner_name": app.owner_name,
                    "audience": app.audience,
                    "ai_provider": app.ai_provider,
                    "technology_description": app.technology_description,
                    "ai_act_category": app.ai_act_category,
                    "compliance_check_status": app.compliance_check_status,
                    "dpia_status": app.dpia_status,
                    "gaira_status": app.gaira_status,
                    "risk_level": app.risk_level,
                    "deployed_at": app.deployed_at,
                    "next_assessment_at": app.next_assessment_at,
                    "latest_assessment_id": str(latest.id) if latest else None,
                    "latest_assessment_type": latest.assessment_type if latest else None,
                }
            )
        return rows
