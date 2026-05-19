from app.services.outputs.detectors.confidential import ConfidentialDetector
from app.services.outputs.detectors.harmful import HarmfulContentDetector
from app.services.outputs.detectors.leakage import LeakageDetector

ALL_OUTPUT_DETECTORS = (
    LeakageDetector(),
    ConfidentialDetector(),
    HarmfulContentDetector(),
)
