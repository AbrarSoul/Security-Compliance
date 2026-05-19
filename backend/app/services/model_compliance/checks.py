"""Built-in model-vs-dataset risk checks."""

from app.models.compliance_model import ComplianceModel
from app.services.model_compliance.types import DatasetContext, ModelContext, ModelRiskCheck


def build_model_context(model: ComplianceModel) -> ModelContext:
    return ModelContext(
        name=model.name,
        provider=model.provider,
        model_type=model.model_type,
        endpoint_url=model.endpoint_url,
        data_retention_policy=model.data_retention_policy,
        logging_enabled=model.logging_enabled,
        data_leaves_platform=model.data_leaves_platform,
        is_approved=model.is_approved,
    )


def run_model_risk_checks(
    dataset: DatasetContext,
    model: ModelContext,
) -> list[ModelRiskCheck]:
    checks: list[ModelRiskCheck] = []
    checks.append(_check_external_api_sensitive(dataset, model))
    checks.append(_check_cloud_restricted(dataset, model))
    checks.append(_check_unknown_provider(model))
    checks.append(_check_logging_sensitive(dataset, model))
    checks.append(_check_stores_user_data(dataset, model))
    checks.append(_check_unapproved_endpoint(model))
    checks.append(_check_lacks_privacy_metadata(model))
    checks.append(_check_confidential_external(dataset, model))
    return [c for c in checks if c.triggered]


def _check_external_api_sensitive(
    dataset: DatasetContext, model: ModelContext
) -> ModelRiskCheck:
    triggered = model.is_external and dataset.has_sensitive_data
    return ModelRiskCheck(
        code="external_api_sensitive_data",
        title="External API with sensitive data",
        description="An external API model is paired with sensitive dataset fields",
        risk_level="critical" if dataset.is_high_risk_classification else "high",
        suggested_action="block" if dataset.is_high_risk_classification else "warn",
        triggered=triggered,
    )


def _check_cloud_restricted(dataset: DatasetContext, model: ModelContext) -> ModelRiskCheck:
    triggered = model.is_cloud and dataset.is_high_risk_classification
    return ModelRiskCheck(
        code="cloud_restricted_data",
        title="Cloud model with restricted data",
        description="Cloud-hosted model used with confidential or restricted classification",
        risk_level="high",
        suggested_action="block",
        triggered=triggered,
    )


def _check_unknown_provider(model: ModelContext) -> ModelRiskCheck:
    return ModelRiskCheck(
        code="unknown_provider",
        title="Unknown model provider",
        description="Model provider is missing or not recognized",
        risk_level="medium",
        suggested_action="warn",
        triggered=model.provider_unknown,
    )


def _check_logging_sensitive(dataset: DatasetContext, model: ModelContext) -> ModelRiskCheck:
    triggered = model.logging_enabled is True and (
        dataset.has_sensitive_data or dataset.has_pii
    )
    return ModelRiskCheck(
        code="model_logs_prompts",
        title="Model logs prompts with sensitive data",
        description="Model has logging enabled and dataset contains sensitive or PII fields",
        risk_level="high",
        suggested_action="warn",
        triggered=triggered,
    )


def _check_stores_user_data(dataset: DatasetContext, model: ModelContext) -> ModelRiskCheck:
    triggered = model.stores_user_data and (
        dataset.has_sensitive_data or dataset.is_high_risk_classification
    )
    return ModelRiskCheck(
        code="model_stores_user_data",
        title="Model stores user data",
        description="Data retention policy indicates storage with a sensitive dataset",
        risk_level="high",
        suggested_action="block",
        triggered=triggered,
    )


def _check_unapproved_endpoint(model: ModelContext) -> ModelRiskCheck:
    return ModelRiskCheck(
        code="unapproved_endpoint",
        title="Model endpoint not approved",
        description="Model is not on the approved model registry",
        risk_level="high",
        suggested_action="block",
        triggered=not model.is_approved,
    )


def _check_lacks_privacy_metadata(model: ModelContext) -> ModelRiskCheck:
    return ModelRiskCheck(
        code="lacks_privacy_metadata",
        title="Missing privacy metadata",
        description="Model lacks data retention and logging privacy metadata while data leaves platform",
        risk_level="medium",
        suggested_action="warn",
        triggered=model.lacks_privacy_metadata,
    )


def _check_confidential_external(dataset: DatasetContext, model: ModelContext) -> ModelRiskCheck:
    triggered = (
        dataset.is_high_risk_classification
        and model.data_leaves_platform
    )
    return ModelRiskCheck(
        code="confidential_data_external",
        title="Confidential data sent externally",
        description="Confidential or restricted data may be sent to an external model",
        risk_level="critical",
        suggested_action="block",
        triggered=triggered,
    )
