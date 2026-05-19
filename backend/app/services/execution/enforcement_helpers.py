"""Build blocking/warning reason lists from validation outcome."""

from typing import Any

from app.services.execution.pre_execution_validator import PreExecutionValidationOutcome


def reasons_from_outcome(outcome: PreExecutionValidationOutcome) -> tuple[list[str], list[str], list[str]]:
    blocking: list[str] = []
    warning: list[str] = []

    if outcome.decision == "block":
        blocking.append(outcome.explanation)
        for rule in outcome.triggered_rules:
            if rule.get("action") == "block":
                blocking.append(rule.get("reason", rule.get("rule_name", "Rule violation")))
        for violation in outcome.policy_violations:
            if violation.action == "block":
                blocking.append(violation.reason)
        for risk in outcome.model_risks:
            if risk.get("suggested_action") == "block":
                blocking.append(risk.get("description", risk.get("title", "Model risk")))
    elif outcome.decision == "warn":
        warning.append(outcome.explanation)
        for rule in outcome.triggered_rules:
            if rule.get("action") == "warn":
                warning.append(rule.get("reason", rule.get("rule_name", "Rule warning")))
        for violation in outcome.policy_violations:
            if violation.action == "warn":
                warning.append(violation.reason)
        for risk in outcome.model_risks:
            if risk.get("suggested_action") == "warn":
                warning.append(risk.get("description", risk.get("title", "Model risk")))

    blocking = list(dict.fromkeys(r for r in blocking if r))
    warning = list(dict.fromkeys(r for r in warning if r))
    return blocking, warning, outcome.recommendations


def reasons_from_summary(summary: dict[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    if not summary:
        return [], [], []
    decision = summary.get("decision", "allow")
    blocking: list[str] = []
    warning: list[str] = []
    explanation = summary.get("explanation")

    if decision == "block":
        if explanation:
            blocking.append(explanation)
        for rule in summary.get("triggered_rules", []):
            if rule.get("action") == "block":
                blocking.append(rule.get("reason", ""))
        for pv in summary.get("policy_violations", []):
            if pv.get("action") == "block":
                blocking.append(pv.get("reason", ""))
        for risk in summary.get("model_risks", []):
            if risk.get("suggested_action") == "block":
                blocking.append(risk.get("description", ""))
    elif decision == "warn":
        if explanation:
            warning.append(explanation)
        for rule in summary.get("triggered_rules", []):
            if rule.get("action") == "warn":
                warning.append(rule.get("reason", ""))
        for pv in summary.get("policy_violations", []):
            if pv.get("action") == "warn":
                warning.append(pv.get("reason", ""))
        for risk in summary.get("model_risks", []):
            if risk.get("suggested_action") == "warn":
                warning.append(risk.get("description", ""))

    recs = summary.get("recommendations", [])
    return (
        list(dict.fromkeys(r for r in blocking if r)),
        list(dict.fromkeys(r for r in warning if r)),
        recs,
    )
