"""Unit tests for shared compliance evaluation orchestrator."""

import uuid
from datetime import UTC, datetime

from app.models.compliance_model import ComplianceModel
from app.services.compliance import ComplianceEvaluationOrchestrator


def _model(**kwargs) -> ComplianceModel:
    defaults = {
        "id": uuid.uuid4(),
        "code": "orch-model",
        "name": "Orchestrator Model",
        "provider": "Internal",
        "model_type": "local_model",
        "endpoint_url": None,
        "data_retention_policy": None,
        "logging_enabled": False,
        "data_leaves_platform": False,
        "is_approved": True,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return ComplianceModel(**defaults)


class _FakeFinding:
    def __init__(self, finding_type: str):
        self.finding_type = finding_type
        self.severity = "medium"
        self.column_name = None
        self.sample_count = 1
        self.match_rate = 1.0


class _FakeScan:
    def __init__(self, finding_types: set[str], classification: str = "internal"):
        self.findings = [_FakeFinding(t) for t in finding_types]
        self.classification = classification
        self.risk_score = 25
        self.compliance_status = "risky"


def test_orchestrator_evaluates_without_duplicate_rule_pass():
    orchestrator = ComplianceEvaluationOrchestrator()
    scan = _FakeScan({"email"})
    model = _model()

    bundle = orchestrator.evaluate(scan, model, active_policies=[], enabled_rules=[])

    assert bundle.rule_result.rules_evaluated == 0
    assert bundle.policy_result.policies_evaluated == 0
    assert bundle.model_result.decision in ("allow", "warn", "block")
