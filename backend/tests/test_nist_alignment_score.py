"""Tests for NIST alignment score calculation."""

from app.services.nist_ai_rmf.alignment_score import compute_alignment_score


def test_score_uses_met_and_partial_only_not_72():
    # 10 met, 5 partial, 40 not_met — denominator is 15, not 55 or 72
    score, detail = compute_alignment_score(met=10, partial=5, not_met=40, violations=0)
    # (10 + 2.5) / 15 * 100 = 83.3
    assert score == 83.3
    assert detail["progress_total"] == 15
    assert detail["evaluated_total"] == 55


def test_not_met_does_not_lower_base_score():
    score_with_gaps, _ = compute_alignment_score(met=10, partial=5, not_met=40, violations=0)
    score_without_gaps, _ = compute_alignment_score(met=10, partial=5, not_met=0, violations=0)
    assert score_with_gaps == score_without_gaps == 83.3


def test_no_progress_yields_zero_base():
    score, detail = compute_alignment_score(met=0, partial=0, not_met=30, violations=0)
    assert score == 0.0
    assert detail["base_score"] == 0.0


def test_violations_deduct_from_evaluated_pool():
    score, detail = compute_alignment_score(met=10, partial=10, not_met=10, violations=2)
    # base = (10 + 5) / 20 * 100 = 75.0
    # deduction = 2 * (100/30) = 6.7
    assert detail["base_score"] == 75.0
    assert detail["violation_deduction"] == 6.7
    assert score == 68.3


def test_score_never_negative():
    score, _ = compute_alignment_score(met=1, partial=0, not_met=5, violations=10)
    assert score == 0.0
