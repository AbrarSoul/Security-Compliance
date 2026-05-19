"""Map prompt/output scan finding types to rule-engine detected_types."""

from app.services.outputs.constants import (
    FINDING_API_KEY as OUT_API,
    FINDING_CONFIDENTIAL as OUT_CONF,
    FINDING_CREDIT_CARD as OUT_CC,
    FINDING_EMAIL as OUT_EMAIL,
    FINDING_FINANCIAL as OUT_FIN,
    FINDING_HEALTHCARE as OUT_HEALTH,
    FINDING_PASSWORD as OUT_PWD,
    FINDING_PHONE as OUT_PHONE,
    FINDING_SSN as OUT_SSN,
)
from app.services.prompts.constants import (
    FINDING_API_KEY as PR_API,
    FINDING_CONFIDENTIAL as PR_CONF,
    FINDING_CREDIT_CARD as PR_CC,
    FINDING_EMAIL as PR_EMAIL,
    FINDING_FINANCIAL as PR_FIN,
    FINDING_HEALTHCARE as PR_HEALTH,
    FINDING_PASSWORD as PR_PWD,
    FINDING_PHONE as PR_PHONE,
    FINDING_SSN as PR_SSN,
)

_FINDING_MAP: dict[str, str] = {
    PR_API: "api_key",
    OUT_API: "api_key",
    PR_PWD: "password",
    OUT_PWD: "password",
    PR_EMAIL: "email",
    OUT_EMAIL: "email",
    PR_PHONE: "phone",
    OUT_PHONE: "phone",
    PR_SSN: "ssn",
    OUT_SSN: "ssn",
    PR_CC: "credit_card",
    OUT_CC: "credit_card",
    PR_FIN: "sensitive_field",
    OUT_FIN: "sensitive_field",
    PR_HEALTH: "sensitive_field",
    OUT_HEALTH: "sensitive_field",
    PR_CONF: "sensitive_field",
    OUT_CONF: "sensitive_field",
    "pii_leakage": "email",
    "bank_account_leakage": "sensitive_field",
    "financial_data_leakage": "sensitive_field",
    "confidential_data_leakage": "sensitive_field",
    "sensitive_business_info": "sensitive_field",
    "harmful_content": "sensitive_field",
    "toxic_content": "sensitive_field",
    "prompt_injection": "sensitive_field",
    "jailbreak": "sensitive_field",
}


def findings_to_detected_types(finding_types: list[str]) -> set[str]:
    detected: set[str] = set()
    for ft in finding_types:
        mapped = _FINDING_MAP.get(ft)
        if mapped:
            detected.add(mapped)
        else:
            detected.add(ft.replace("_leakage", ""))
    return detected
