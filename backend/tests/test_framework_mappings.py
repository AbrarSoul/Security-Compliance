"""Unit tests for framework gap mappings."""

from app.services.compliance.framework_mappings import (
    FRAMEWORK_GAIRA,
    FRAMEWORK_INTERNAL_GUARDRAILS,
    FRAMEWORK_NIST_AI_RMF,
    aggregate_by_framework,
    attach_framework_refs_to_metadata,
    framework_refs_for_gap_type,
    resolve_framework_refs,
)
from app.services.gaps.constants import (
    GAP_MISSING_GAIRA_ASSESSMENT,
    GAP_MISSING_ENCRYPTION,
    GAP_WEAK_RBAC,
)


def test_framework_refs_for_encryption():
    refs = framework_refs_for_gap_type(GAP_MISSING_ENCRYPTION)
    frameworks = {r["framework"] for r in refs}
    assert FRAMEWORK_NIST_AI_RMF in frameworks
    assert FRAMEWORK_INTERNAL_GUARDRAILS in frameworks


def test_attach_framework_refs_to_metadata():
    meta = attach_framework_refs_to_metadata(GAP_WEAK_RBAC, {})
    assert "framework_refs" in meta
    assert any(r["control_id"] == "GOVERN-2.1" for r in meta["framework_refs"])


def test_attach_preserves_existing_refs():
    existing = [{"framework": FRAMEWORK_GAIRA, "control_id": "CUSTOM"}]
    meta = attach_framework_refs_to_metadata(GAP_MISSING_GAIRA_ASSESSMENT, {"framework_refs": existing})
    assert meta["framework_refs"] == existing


def test_resolve_framework_refs_from_legacy_nist():
    class _Gap:
        gap_type = GAP_MISSING_GAIRA_ASSESSMENT
        metadata_json = {"nist_refs": ["MAP-5.1"]}

    refs = resolve_framework_refs(_Gap())  # type: ignore[arg-type]
    assert refs == [{"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-5.1"}]


def test_aggregate_by_framework():
    class _Gap:
        def __init__(self, gap_type: str):
            self.gap_type = gap_type
            self.metadata_json = None

    gaps = [_Gap(GAP_MISSING_ENCRYPTION), _Gap(GAP_MISSING_GAIRA_ASSESSMENT)]
    counts = aggregate_by_framework(gaps)  # type: ignore[arg-type]
    assert counts[FRAMEWORK_NIST_AI_RMF] >= 2
    assert counts[FRAMEWORK_GAIRA] == 1
    assert counts[FRAMEWORK_INTERNAL_GUARDRAILS] == 1
