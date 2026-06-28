from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    audit_logs,
    compliance_guard,
    compliance_models,
    compliance_posture,
    executions,
    files,
    gaira,
    gaps,
    monitoring,
    nist_ai_rmf,
    notifications,
    output_monitoring,
    prompt_monitoring,
    policies,
    protected,
    rbac_access,
    reports,
    rules,
    scans,
    scoring,
    threats,
    users,
)
from app.auth.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(files.router)
api_router.include_router(scans.router)
api_router.include_router(reports.router)
api_router.include_router(scoring.router)
api_router.include_router(rules.router)
api_router.include_router(policies.router)
api_router.include_router(compliance_models.router)
api_router.include_router(executions.router)
api_router.include_router(analytics.router)
api_router.include_router(gaps.router)
api_router.include_router(compliance_posture.router)
api_router.include_router(gaira.router)
api_router.include_router(nist_ai_rmf.router)
api_router.include_router(threats.router)
api_router.include_router(monitoring.router)
api_router.include_router(prompt_monitoring.router)
api_router.include_router(output_monitoring.router)
api_router.include_router(compliance_guard.router)
api_router.include_router(notifications.router)
api_router.include_router(audit_logs.router)
api_router.include_router(users.router)
api_router.include_router(rbac_access.router)
api_router.include_router(protected.router)
