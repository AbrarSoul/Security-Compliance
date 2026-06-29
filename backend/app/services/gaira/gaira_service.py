"""GAIRA assessment orchestration."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gaira import AIApplication, GairaAssessment
from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.core.gaira_registration import (
    REGISTRATION_APPROVED,
    REGISTRATION_PENDING_ADMIN,
    REGISTRATION_PENDING_AUDITOR,
    REGISTRATION_REJECTED,
)

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
from app.repositories.compliance_model_repository import ComplianceModelRepository
from app.services.audit_service import AuditService
from app.services.notifications.constants import (
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    TYPE_GAIRA_APPLICATION,
)
from app.services.notifications.notification_service import NotificationService
from app.services.gaira.engine import compute_assessment, normalize_risk_level
from app.services.gaira.framework import GairaFramework, get_gaira_framework


class GairaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GairaRepository(db)
        self.scans = ScanRepository(db)
        self.models = ComplianceModelRepository(db)
        self.framework = get_gaira_framework()
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)

    def get_framework(self) -> GairaFramework:
        return self.framework

    async def create_application(
        self,
        *,
        payload: dict,
        created_by_user_id: UUID,
        auto_approve: bool = False,
    ) -> AIApplication:
        registration_status = REGISTRATION_APPROVED if auto_approve else REGISTRATION_PENDING_AUDITOR
        is_active = auto_approve

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
            registration_status=registration_status,
            is_active=is_active,
            approved_by_user_id=created_by_user_id if auto_approve else None,
            approved_at=datetime.now(UTC) if auto_approve else None,
        )
        application = await self.repo.create_application(application)

        await self.audit.log(
            AuditAction.GAIRA_APPLICATION_REGISTERED,
            user_id=created_by_user_id,
            resource_type="ai_application",
            resource_id=application.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={
                "name": application.name,
                "registration_status": registration_status,
                "auto_approve": auto_approve,
            },
        )

        if not auto_approve:
            await self.notifications.notify_role(
                "auditor",
                notification_type=TYPE_GAIRA_APPLICATION,
                severity=SEVERITY_HIGH,
                title="New AI application registration",
                message=(
                    f"'{application.name}' was registered and is awaiting auditor review."
                ),
                event_type=AuditAction.GAIRA_APPLICATION_REGISTERED,
                resource_type="ai_application",
                resource_id=application.id,
                exclude_user_id=created_by_user_id,
            )

        return application

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

    async def list_pending_auditor(
        self, *, limit: int = 100, offset: int = 0
    ) -> tuple[list[AIApplication], int]:
        return await self.repo.list_by_registration_status(
            REGISTRATION_PENDING_AUDITOR, limit=limit, offset=offset
        )

    async def list_pending_admin(
        self, *, limit: int = 100, offset: int = 0
    ) -> tuple[list[AIApplication], int]:
        return await self.repo.list_by_registration_status(
            REGISTRATION_PENDING_ADMIN, limit=limit, offset=offset
        )

    async def count_pending_auditor(self) -> int:
        return await self.repo.count_by_registration_status(REGISTRATION_PENDING_AUDITOR)

    async def count_pending_admin(self) -> int:
        return await self.repo.count_by_registration_status(REGISTRATION_PENDING_ADMIN)

    async def submit_auditor_feedback(
        self,
        application_id: UUID,
        *,
        feedback: str,
        auditor_user_id: UUID,
    ) -> AIApplication:
        application = await self.repo.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if application.registration_status != REGISTRATION_PENDING_AUDITOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only applications awaiting auditor review can receive feedback",
            )

        application.registration_status = REGISTRATION_PENDING_ADMIN
        application.auditor_feedback = feedback.strip()
        application.auditor_reviewed_by_user_id = auditor_user_id
        application.auditor_reviewed_at = datetime.now(UTC)
        application = await self.repo.update_application(application)

        await self.audit.log(
            AuditAction.GAIRA_APPLICATION_REVIEWED,
            user_id=auditor_user_id,
            resource_type="ai_application",
            resource_id=application.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={"name": application.name},
        )

        await self.notifications.notify_role(
            "admin",
            notification_type=TYPE_GAIRA_APPLICATION,
            severity=SEVERITY_HIGH,
            title="AI application ready for admin decision",
            message=(
                f"Auditor reviewed '{application.name}'. "
                "Open GAIRA approvals to approve or reject the registration."
            ),
            event_type=AuditAction.GAIRA_APPLICATION_REVIEWED,
            resource_type="ai_application",
            resource_id=application.id,
            exclude_user_id=auditor_user_id,
        )

        if application.created_by_user_id:
            await self.notifications.notify_user(
                application.created_by_user_id,
                notification_type=TYPE_GAIRA_APPLICATION,
                severity=SEVERITY_INFO,
                title="Auditor review completed",
                message=(
                    f"Your AI application '{application.name}' was reviewed by an auditor "
                    "and is now awaiting admin approval."
                ),
                event_type=AuditAction.GAIRA_APPLICATION_REVIEWED,
                resource_type="ai_application",
                resource_id=application.id,
            )

        return application

    async def approve_application(
        self,
        application_id: UUID,
        *,
        admin_user_id: UUID,
    ) -> AIApplication:
        application = await self.repo.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if application.registration_status != REGISTRATION_PENDING_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only applications awaiting admin approval can be approved",
            )

        application.registration_status = REGISTRATION_APPROVED
        application.is_active = True
        application.approved_by_user_id = admin_user_id
        application.approved_at = datetime.now(UTC)
        application.rejected_by_user_id = None
        application.rejected_at = None
        application.rejection_reason = None
        application = await self.repo.update_application(application)

        await self.audit.log(
            AuditAction.GAIRA_APPLICATION_APPROVED,
            user_id=admin_user_id,
            resource_type="ai_application",
            resource_id=application.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={"name": application.name},
        )

        if application.created_by_user_id:
            await self.notifications.notify_user(
                application.created_by_user_id,
                notification_type=TYPE_GAIRA_APPLICATION,
                severity=SEVERITY_INFO,
                title="AI application approved",
                message=(
                    f"Your AI application '{application.name}' was approved. "
                    "You can now start GAIRA assessments."
                ),
                event_type=AuditAction.GAIRA_APPLICATION_APPROVED,
                resource_type="ai_application",
                resource_id=application.id,
            )

        return application

    async def reject_application(
        self,
        application_id: UUID,
        *,
        reason: str,
        admin_user_id: UUID,
    ) -> AIApplication:
        application = await self.repo.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if application.registration_status not in {
            REGISTRATION_PENDING_ADMIN,
            REGISTRATION_PENDING_AUDITOR,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending applications can be rejected",
            )

        application.registration_status = REGISTRATION_REJECTED
        application.is_active = False
        application.rejected_by_user_id = admin_user_id
        application.rejected_at = datetime.now(UTC)
        application.rejection_reason = reason.strip()
        application = await self.repo.update_application(application)

        await self.audit.log(
            AuditAction.GAIRA_APPLICATION_REJECTED,
            user_id=admin_user_id,
            resource_type="ai_application",
            resource_id=application.id,
            severity=audit_severity.MEDIUM,
            status="success",
            metadata={"name": application.name, "reason": application.rejection_reason},
        )

        if application.created_by_user_id:
            await self.notifications.notify_user(
                application.created_by_user_id,
                notification_type=TYPE_GAIRA_APPLICATION,
                severity=SEVERITY_WARNING,
                title="AI application rejected",
                message=(
                    f"Your AI application '{application.name}' was rejected. "
                    f"Reason: {application.rejection_reason}"
                ),
                event_type=AuditAction.GAIRA_APPLICATION_REJECTED,
                resource_type="ai_application",
                resource_id=application.id,
            )

        return application

    def _ensure_registration_approved(self, application: AIApplication) -> None:
        if application.registration_status != REGISTRATION_APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This AI application must be approved before assessments can begin. "
                    f"Current registration status: {application.registration_status}."
                ),
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

        self._ensure_registration_approved(application)

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
