"""GAIRA assessment scoring and recommendations."""

from __future__ import annotations

from typing import Any

from app.services.gaira.types import AssessmentComputeResult

YES_VALUES = {"yes", "true", "1", 1, True}
LIGHT_ROUTING_QUESTION_IDS = {
    "3.01",
    "3.02",
    "3.03",
    "3.04",
    "3.05",
    "3.06",
    "3.07",
    "3.08",
}


def _answer_value(answers: dict[str, Any], question_id: str) -> Any:
    entry = answers.get(question_id)
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def _is_yes(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value).strip().lower() in YES_VALUES


def _question_ids_for_step(questions: list[dict[str, Any]], step_id: str) -> list[str]:
    return [q["id"] for q in questions if q.get("step_id") == step_id]


def compute_ai_risk_levels(
    answers: dict[str, Any], questions: list[dict[str, Any]]
) -> AssessmentComputeResult:
    step1_ids = _question_ids_for_step(questions, "1")
    step2_ids = _question_ids_for_step(questions, "2")
    step3_ids = _question_ids_for_step(questions, "3")

    insignificant_hits = [qid for qid in step1_ids if _is_yes(_answer_value(answers, qid))]
    high_hits = [qid for qid in step2_ids if _is_yes(_answer_value(answers, qid))]
    medium_hits = [qid for qid in step3_ids if _is_yes(_answer_value(answers, qid))]

    if insignificant_hits:
        level = "insignificant"
        recommendation = "AI risks are likely insignificant; a full GAIRA assessment may not be required."
    elif high_hits:
        level = "high"
        recommendation = "Use GAIRA Comprehensive and complete EU AI Act checks before deployment."
    elif medium_hits:
        level = "medium"
        recommendation = "Use GAIRA Light; escalate to Comprehensive if additional risks emerge."
    else:
        level = "low"
        recommendation = "GAIRA Light is likely sufficient for this application."

    return AssessmentComputeResult(
        risk_level=level,
        recommended_module="gaira_comprehensive" if level == "high" else "gaira_light",
        proceed_recommendation=recommendation,
        details={
            "insignificant_hits": insignificant_hits,
            "high_hits": high_hits,
            "medium_hits": medium_hits,
        },
    )


def compute_gaira_light_routing(answers: dict[str, Any]) -> AssessmentComputeResult:
    hits = [qid for qid in LIGHT_ROUTING_QUESTION_IDS if _is_yes(_answer_value(answers, qid))]
    if hits:
        return AssessmentComputeResult(
            recommended_module="gaira_comprehensive",
            proceed_recommendation=(
                "One or more high-risk indicators were answered Yes. "
                "GAIRA Comprehensive is recommended."
            ),
            flags=["routing_comprehensive"],
            details={"routing_hits": hits},
        )
    return AssessmentComputeResult(
        recommended_module="gaira_light",
        proceed_recommendation="No high-risk routing indicators detected; GAIRA Light appears sufficient.",
        flags=["routing_light"],
        details={"routing_hits": []},
    )


def compute_gaira_light_step4(answers: dict[str, Any]) -> AssessmentComputeResult:
    problematic: list[str] = []
    pending_second_line: list[str] = []

    for qid, entry in answers.items():
        if not qid.startswith("4."):
            continue
        if not isinstance(entry, dict):
            continue
        if entry.get("flagged"):
            problematic.append(qid)
            if not entry.get("second_line_reviewer"):
                pending_second_line.append(qid)

    recommendation = "All Step 4 controls appear acceptable."
    if problematic:
        recommendation = (
            f"{len(problematic)} Step 4 answer(s) are flagged as problematic. "
            "Second-line review is required before proceeding."
        )

    return AssessmentComputeResult(
        problematic_count=len(problematic),
        proceed_recommendation=recommendation,
        flags=["second_line_required"] if pending_second_line else [],
        details={
            "problematic_questions": problematic,
            "pending_second_line": pending_second_line,
        },
    )


def compute_assessment(
    assessment_type: str,
    answers: dict[str, Any],
    questions: list[dict[str, Any]],
) -> AssessmentComputeResult:
    if assessment_type == "ai_risk_levels":
        return compute_ai_risk_levels(answers, questions)
    if assessment_type == "gaira_light":
        routing = compute_gaira_light_routing(answers)
        step4 = compute_gaira_light_step4(answers)
        return AssessmentComputeResult(
            recommended_module=routing.recommended_module,
            proceed_recommendation=routing.proceed_recommendation,
            problematic_count=step4.problematic_count,
            flags=routing.flags + step4.flags,
            details={
                "routing": routing.details,
                "step4": step4.details,
            },
        )
    return AssessmentComputeResult()


def normalize_risk_level(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower().replace("_", " ")
    mapping = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "very high": "very_high",
        "very_high": "very_high",
        "insignificant": "insignificant",
    }
    return mapping.get(normalized, normalized.replace(" ", "_"))
