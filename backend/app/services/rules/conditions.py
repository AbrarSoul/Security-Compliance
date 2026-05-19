"""Structured JSON condition evaluation for compliance rules."""

from typing import Any

from app.services.rules.types import RuleEvaluationContext

COMPOUND_KEYS = frozenset({"all", "any", "not"})


class ConditionEvaluationError(ValueError):
    pass


def evaluate_condition(condition: dict[str, Any] | None, ctx: RuleEvaluationContext) -> bool:
    if not condition:
        return False

    if "all" in condition:
        parts = condition["all"]
        if not isinstance(parts, list) or not parts:
            return False
        return all(evaluate_condition(part, ctx) for part in parts)

    if "any" in condition:
        parts = condition["any"]
        if not isinstance(parts, list) or not parts:
            return False
        return any(evaluate_condition(part, ctx) for part in parts)

    if "not" in condition:
        inner = condition["not"]
        if isinstance(inner, dict):
            return not evaluate_condition(inner, ctx)
        return False

    return _evaluate_leaf(condition, ctx)


def _evaluate_leaf(condition: dict[str, Any], ctx: RuleEvaluationContext) -> bool:
    field = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    if not field or not operator:
        raise ConditionEvaluationError("Leaf conditions require 'field' and 'operator'")

    actual = ctx.get_field(str(field))
    op = str(operator).lower()

    if op == "contains":
        return _contains(actual, expected)
    if op == "not_contains":
        return not _contains(actual, expected)
    if op in ("equals", "eq"):
        return _equals(actual, expected)
    if op in ("not_equals", "neq"):
        return not _equals(actual, expected)
    if op == "in":
        if not isinstance(expected, (list, tuple, set)):
            return False
        return _equals(actual, expected) or (
            isinstance(actual, str) and actual in expected
        )
    if op == "not_in":
        if not isinstance(expected, (list, tuple, set)):
            return True
        return actual not in expected
    if op == "exists":
        return actual is not None and actual != "" and actual != set()
    if op in ("gte", "ge"):
        return _compare_numeric(actual, expected) is not None and _compare_numeric(
            actual, expected
        ) >= 0
    if op in ("lte", "le"):
        return _compare_numeric(actual, expected) is not None and _compare_numeric(
            actual, expected
        ) <= 0
    if op == "gt":
        cmp = _compare_numeric(actual, expected)
        return cmp is not None and cmp > 0
    if op == "lt":
        cmp = _compare_numeric(actual, expected)
        return cmp is not None and cmp < 0

    raise ConditionEvaluationError(f"Unsupported operator: {operator}")


def _contains(actual: Any, expected: Any) -> bool:
    if actual is None:
        return False
    if isinstance(actual, (set, list, tuple, frozenset)):
        if isinstance(expected, (list, tuple, set)):
            return bool(set(expected) & set(actual))
        return expected in actual
    if isinstance(actual, str) and isinstance(expected, str):
        return expected.lower() in actual.lower()
    return _equals(actual, expected)


def _equals(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return bool(actual) is bool(expected)
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.lower() == expected.lower()
    return actual == expected


def _compare_numeric(actual: Any, expected: Any) -> int | None:
    try:
        left = float(actual)
        right = float(expected)
    except (TypeError, ValueError):
        return None
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
