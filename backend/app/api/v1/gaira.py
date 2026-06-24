"""GAIRA AI risk assessment APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import GAIRA_MANAGE, GAIRA_READ, GAIRA_READ_ALL
from app.db.session import get_db
from app.schemas.gaira import (
    AIApplicationCreate,
    AIApplicationListResponse,
    AIApplicationResponse,
    AIApplicationUpdate,
    GairaAssessmentListResponse,
    GairaAssessmentResponse,
    GairaFrameworkResponse,
    GairaModuleDetailResponse,
    GairaModuleSummary,
    RoaiaListResponse,
    RoaiaRow,
    StartAssessmentRequest,
    SubmitAssessmentRequest,
    UpdateAnswersRequest,
)
from app.services.gaira.gaira_service import GairaService

router = APIRouter(prefix="/gaira", tags=["gaira"])


def get_gaira_service(db: AsyncSession = Depends(get_db)) -> GairaService:
    return GairaService(db)


@router.get("/framework", response_model=GairaFrameworkResponse)
async def get_framework(
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    framework = service.get_framework()
    return GairaFrameworkResponse(
        version=framework.version,
        modules=[GairaModuleSummary(**item) for item in framework.list_modules()],
    )


@router.get("/framework/{module_key}", response_model=GairaModuleDetailResponse)
async def get_framework_module(
    module_key: str,
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    module = service.get_framework().get_module(module_key)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return GairaModuleDetailResponse(**module)


@router.get("/roaia", response_model=RoaiaListResponse)
async def list_roaia(
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    applications, total = await service.list_applications(
        active_only=active_only, limit=limit, offset=offset
    )
    rows = service.roaia_rows(applications)
    return RoaiaListResponse(items=[RoaiaRow(**row) for row in rows], total=total)


@router.post("/applications", response_model=AIApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: AIApplicationCreate,
    auth: AuthContext = Depends(require_permission(GAIRA_MANAGE)),
    service: GairaService = Depends(get_gaira_service),
):
    application = await service.create_application(
        payload=body.model_dump(),
        created_by_user_id=auth.user.id,
    )
    return AIApplicationResponse.model_validate(application)


@router.get("/applications", response_model=AIApplicationListResponse)
async def list_applications(
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    items, total = await service.list_applications(
        active_only=active_only, limit=limit, offset=offset
    )
    return AIApplicationListResponse(
        items=[AIApplicationResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/applications/{application_id}", response_model=AIApplicationResponse)
async def get_application(
    application_id: UUID,
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    application = await service.get_application(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return AIApplicationResponse.model_validate(application)


@router.patch("/applications/{application_id}", response_model=AIApplicationResponse)
async def update_application(
    application_id: UUID,
    body: AIApplicationUpdate,
    _auth: AuthContext = Depends(require_permission(GAIRA_MANAGE)),
    service: GairaService = Depends(get_gaira_service),
):
    application = await service.update_application(
        application_id, body.model_dump(exclude_unset=True)
    )
    return AIApplicationResponse.model_validate(application)


@router.post(
    "/applications/{application_id}/assessments",
    response_model=GairaAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_assessment(
    application_id: UUID,
    body: StartAssessmentRequest,
    auth: AuthContext = Depends(require_permission(GAIRA_MANAGE)),
    service: GairaService = Depends(get_gaira_service),
):
    assessment = await service.start_assessment(
        application_id,
        assessment_type=body.assessment_type,
        created_by_user_id=auth.user.id,
        scan_id=body.scan_id,
    )
    return GairaAssessmentResponse.model_validate(assessment)


@router.get(
    "/applications/{application_id}/assessments",
    response_model=GairaAssessmentListResponse,
)
async def list_assessments(
    application_id: UUID,
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    application = await service.get_application(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    items = application.assessments if application.assessments else []
    return GairaAssessmentListResponse(
        items=[GairaAssessmentResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.get("/assessments/{assessment_id}", response_model=GairaAssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    assessment = await service.get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return GairaAssessmentResponse.model_validate(assessment)


@router.patch("/assessments/{assessment_id}/answers", response_model=GairaAssessmentResponse)
async def update_assessment_answers(
    assessment_id: UUID,
    body: UpdateAnswersRequest,
    _auth: AuthContext = Depends(require_permission(GAIRA_MANAGE)),
    service: GairaService = Depends(get_gaira_service),
):
    assessment = await service.update_answers(
        assessment_id, answers=body.answers, merge=body.merge
    )
    return GairaAssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/compute", response_model=GairaAssessmentResponse)
async def compute_assessment(
    assessment_id: UUID,
    _auth: AuthContext = Depends(require_any_permission(GAIRA_READ, GAIRA_READ_ALL)),
    service: GairaService = Depends(get_gaira_service),
):
    assessment = await service.compute_assessment(assessment_id)
    return GairaAssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/submit", response_model=GairaAssessmentResponse)
async def submit_assessment(
    assessment_id: UUID,
    body: SubmitAssessmentRequest,
    auth: AuthContext = Depends(require_permission(GAIRA_MANAGE)),
    service: GairaService = Depends(get_gaira_service),
):
    assessment = await service.submit_assessment(
        assessment_id,
        user_id=auth.user.id,
        overall_risk_level=body.overall_risk_level,
        proceed_decision=body.proceed_decision,
        decision_comments=body.decision_comments,
    )
    return GairaAssessmentResponse.model_validate(assessment)
