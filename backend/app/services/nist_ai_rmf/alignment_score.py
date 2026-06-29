"""Alignment score from met/partial progress; violations deduct from evaluated pool."""

from __future__ import annotations


def compute_alignment_score(
    met: int,
    partial: int,
    not_met: int,
    violations: int,
) -> tuple[float, dict[str, float | int]]:
    """Score over met + partial progress only (not the full 72-item catalog).

    Base: (met + 0.5 * partial) / (met + partial) * 100  when met + partial > 0
    Deduction: violations * (100 / evaluated_total) where
    evaluated_total = met + partial + not_met (auto-checked controls only).
  """
    progress_total = met + partial
    evaluated_total = met + partial + not_met

    if progress_total == 0:
        base_score = 0.0
    else:
        base_score = (met + partial * 0.5) / progress_total * 100

    if violations > 0 and evaluated_total > 0:
        violation_deduction = violations * (100.0 / evaluated_total)
    else:
        violation_deduction = 0.0

    final_score = max(0.0, round(base_score - violation_deduction, 1))

    return final_score, {
        "evaluated_total": evaluated_total,
        "progress_total": progress_total,
        "base_score": round(base_score, 1),
        "violation_deduction": round(violation_deduction, 1),
    }
