"""Unit tests for NIST violation vs alignment-gap classification."""

from app.services.nist_ai_rmf.finding_classifier import classify_finding_kind, has_active_breach


def test_unapproved_external_models_is_violation():
    assert has_active_breach("no_unapproved_external_models", {"unapproved": 2, "external_models": 3})
    assert not has_active_breach("no_unapproved_external_models", {"unapproved": 0})
    assert (
        classify_finding_kind(
            "not_met",
            "partial",
            "no_unapproved_external_models",
            {"unapproved": 1},
        )
        == "violation"
    )


def test_empty_org_rules_are_alignment_gap_not_violation():
    assert (
        classify_finding_kind("not_met", "partial", "org_has_enabled_rules", {"enabled_rules": 0})
        == "alignment_gap"
    )


def test_active_apps_without_gaira_is_violation():
    assert has_active_breach("gaira_risk_assessed", {"total": 3, "assessed": 1})
    assert (
        classify_finding_kind(
            "partial",
            "partial",
            "gaira_risk_assessed",
            {"total": 3, "assessed": 1},
        )
        == "violation"
    )


def test_no_inventory_is_alignment_gap():
    assert (
        classify_finding_kind("not_met", "partial", "gaira_risk_assessed", {"total": 0, "assessed": 0})
        == "alignment_gap"
    )


def test_not_assessed_and_out_of_scope():
    assert classify_finding_kind("not_assessed", "partial", None, {}) == "unchecked"
    assert classify_finding_kind("not_applicable", "none", None, {}) == "out_of_scope"
