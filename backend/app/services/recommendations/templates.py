from dataclasses import dataclass
from typing import Callable

from app.services.recommendations.types import ActionType, Priority


@dataclass(frozen=True)
class RecommendationTemplate:
    finding_type: str
    priority: Priority
    action_type: ActionType
    title: str
    description: str


def _col(column: str | None) -> str:
    return f"'{column}'" if column else "the affected column"


FINDING_TEMPLATES: dict[str, RecommendationTemplate] = {
    "email": RecommendationTemplate(
        finding_type="email",
        priority="medium",
        action_type="anonymize",
        title="Anonymize email addresses",
        description="Apply hashing, tokenization, or format-preserving encryption to {column}. "
        "Avoid storing raw email in non-production environments.",
    ),
    "phone": RecommendationTemplate(
        finding_type="phone",
        priority="medium",
        action_type="mask",
        title="Mask phone numbers",
        description="Mask or truncate phone values in {column} (e.g. show last 4 digits only). "
        "Remove the column if phone data is not required for the use case.",
    ),
    "password": RecommendationTemplate(
        finding_type="password",
        priority="high",
        action_type="remove_column",
        title="Remove or hash password data",
        description="Plaintext credential-like values were found in {column}. "
        "Delete this column from the dataset or replace values with salted password hashes using a vetted algorithm. "
        "Never store recoverable passwords in data files.",
    ),
    "api_key": RecommendationTemplate(
        finding_type="api_key",
        priority="high",
        action_type="rotate_secret",
        title="Rotate exposed API keys",
        description="Revoke and rotate any secrets found in {column}. "
        "Move credentials to a secrets manager and reference them at runtime instead of embedding in data files.",
    ),
    "name": RecommendationTemplate(
        finding_type="name",
        priority="low",
        action_type="anonymize",
        title="Pseudonymize name fields",
        description="Replace direct identifiers in {column} with pseudonyms or irreversible tokens. "
        "Link tokens via a separate secured mapping table if re-identification is needed.",
    ),
    "sensitive_field": RecommendationTemplate(
        finding_type="sensitive_field",
        priority="medium",
        action_type="mask",
        title="Mask sensitive fields",
        description="Apply field-level masking or redaction to {column}. "
        "Restrict access to users with a documented business need.",
    ),
}

SEVERITY_PRIORITY_OVERRIDE: dict[str, Priority] = {
    "critical": "high",
    "high": "high",
    "medium": "medium",
    "low": "low",
}

STATUS_RECOMMENDATIONS: dict[str, list[tuple[Priority, ActionType, str, str]]] = {
    "non_compliant": [
        (
            "high",
            "restrict_access",
            "Restrict dataset access",
            "This dataset is non-compliant. Limit access to authorized personnel, "
            "pause downstream sharing, and remediate findings before wider distribution.",
        ),
        (
            "high",
            "review_policy",
            "Conduct compliance review",
            "Schedule a data governance review. Document lawful basis, retention period, "
            "and whether this dataset should be stored in its current form.",
        ),
    ],
    "risky": [
        (
            "medium",
            "audit_logging",
            "Enable access auditing",
            "Enable audit logging for all access to this dataset until remediation is complete.",
        ),
    ],
}


def render_description(template: RecommendationTemplate, column_name: str | None) -> str:
    return template.description.format(column=_col(column_name))
