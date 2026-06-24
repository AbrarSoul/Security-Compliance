"""Typed structures for GAIRA framework and assessments."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GairaQuestion:
    id: str
    text: str
    step_id: str | None = None
    answer_type: str = "text"
    explanation: str | None = None
    instruction: str | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class GairaStep:
    id: str
    title: str
    instruction: str | None = None


@dataclass
class GairaModule:
    key: str
    title: str
    version: str | None
    overview: str | None
    metadata_fields: list[dict[str, str]]
    steps: list[GairaStep]
    questions: list[GairaQuestion]


@dataclass
class AssessmentComputeResult:
    risk_level: str | None = None
    recommended_module: str | None = None
    proceed_recommendation: str | None = None
    problematic_count: int = 0
    flags: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
