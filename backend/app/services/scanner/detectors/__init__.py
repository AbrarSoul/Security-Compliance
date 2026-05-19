from app.services.scanner.detectors.api_key import ApiKeyDetector
from app.services.scanner.detectors.email import EmailDetector
from app.services.scanner.detectors.password import PasswordDetector
from app.services.scanner.detectors.phone import PhoneDetector
from app.services.scanner.detectors.sensitive_field import SensitiveFieldDetector

ALL_DETECTORS = [
    EmailDetector(),
    PhoneDetector(),
    PasswordDetector(),
    ApiKeyDetector(),
    SensitiveFieldDetector(),
]

__all__ = ["ALL_DETECTORS"]
