from app.services.prompts.detectors.confidential import ConfidentialDetector
from app.services.prompts.detectors.credentials import CredentialDetector
from app.services.prompts.detectors.financial import FinancialDetector
from app.services.prompts.detectors.healthcare import HealthcareDetector
from app.services.prompts.detectors.pii import PiiDetector
from app.services.prompts.detectors.security_threats import SecurityThreatDetector

ALL_PROMPT_DETECTORS = (
    CredentialDetector(),
    PiiDetector(),
    FinancialDetector(),
    HealthcareDetector(),
    ConfidentialDetector(),
    SecurityThreatDetector(),
)
