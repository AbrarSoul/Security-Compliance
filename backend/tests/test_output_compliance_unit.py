"""Unit tests for output compliance scanning."""

import pytest

from app.services.outputs.constants import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_WARN,
    MASK_API_KEY,
    MASK_EMAIL,
    MASK_PASSWORD,
)
from app.services.outputs.engine import OutputScanningEngine


@pytest.fixture
def engine() -> OutputScanningEngine:
    return OutputScanningEngine()


def test_clean_output_allowed(engine: OutputScanningEngine):
    outcome = engine.scan("Here is a summary of secure coding best practices.")
    assert outcome.decision == DECISION_ALLOW
    assert outcome.can_display is True


def test_api_key_leakage_blocked(engine: OutputScanningEngine):
    output = "Your key is aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    outcome = engine.scan(output)
    assert outcome.decision == DECISION_BLOCK
    assert outcome.can_display is False
    assert outcome.redacted_output == ""
    assert MASK_API_KEY in outcome.masked_output
    assert any(f.finding_type == "api_key_leakage" for f in outcome.findings)


def test_password_leakage_blocked(engine: OutputScanningEngine):
    outcome = engine.scan("The admin password=SuperSecret123! for the server.")
    assert outcome.decision == DECISION_BLOCK
    assert MASK_PASSWORD in outcome.masked_output


def test_email_leakage_warns(engine: OutputScanningEngine):
    outcome = engine.scan("Contact support at user@company.com for help.")
    assert outcome.decision in {DECISION_WARN, DECISION_BLOCK}
    assert MASK_EMAIL in outcome.masked_output


def test_ssn_leakage_blocked(engine: OutputScanningEngine):
    outcome = engine.scan("Employee SSN on file: 123-45-6789.")
    assert outcome.decision == DECISION_BLOCK


def test_harmful_content_blocked(engine: OutputScanningEngine):
    outcome = engine.scan("Here are steps to make a bomb at home.")
    assert outcome.decision == DECISION_BLOCK
    assert any(f.finding_type == "harmful_content" for f in outcome.findings)


def test_confidential_business_warns(engine: OutputScanningEngine):
    outcome = engine.scan("CONFIDENTIAL: unreleased earnings and merger plan details.")
    assert outcome.decision == DECISION_WARN
    assert outcome.can_display is True
