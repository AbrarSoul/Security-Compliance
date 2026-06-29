"""Deterministic rule matching against extracted file content."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.services.files.analysis.types import AnalysisFinding
from app.services.files.extraction.types import ExtractedContent

_RULES_PATH = Path(__file__).with_name("rules.yaml")
_HIGH_RISK_SEVERITIES = frozenset({"critical", "high"})


class FileRuleMatcher:
    """Match editable YAML rules against normalized extraction output."""

    def __init__(self, rules: list[dict[str, Any]] | None = None):
        self._rules = rules if rules is not None else self.load_rules()

    @staticmethod
    def load_rules(path: Path | None = None) -> list[dict[str, Any]]:
        rules_file = path or _RULES_PATH
        with rules_file.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return list(data.get("rules", []))

    def reload_rules(self, path: Path | None = None) -> None:
        self._rules = self.load_rules(path)

    @property
    def rules(self) -> list[dict[str, Any]]:
        return self._rules

    def evaluate(self, extracted: ExtractedContent) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        for rule in self._rules:
            applies_to = rule.get("applies_to") or []
            if applies_to and extracted.file_type not in applies_to:
                continue
            matched, evidence, explanation = self._match_rule(rule, extracted)
            findings.append(
                AnalysisFinding(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    category=rule.get("category", "general"),
                    severity=rule.get("severity", "medium"),
                    matched=matched,
                    required=bool(rule.get("required", False)),
                    rule_kind=rule.get("rule_kind", "requirement"),
                    message=self._result_message(rule, matched),
                    evidence=evidence,
                    explanation=explanation,
                )
            )
        return findings

    def _result_message(self, rule: dict[str, Any], matched: bool) -> str:
        if matched:
            return f"Rule '{rule['name']}' matched"
        if rule.get("required"):
            return f"Required rule '{rule['name']}' not satisfied — compliance gap"
        return f"Optional rule '{rule['name']}' not matched"

    def _match_rule(
        self, rule: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        match_spec = rule.get("match") or {}
        match_type = match_spec.get("type", "")

        if match_type == "data_quality_finding":
            return self._match_data_quality_finding(match_spec, extracted)
        if match_type == "row_count":
            return self._match_row_count(match_spec, extracted)
        if match_type == "column_name_pattern":
            return self._match_column_pattern(match_spec, extracted)
        if match_type == "keyword":
            return self._match_keywords(match_spec, extracted)
        if match_type == "log_level":
            return self._match_log_level(match_spec, extracted)
        if match_type == "log_finding":
            return self._match_log_finding(match_spec, extracted)
        if match_type == "structure_count":
            return self._match_structure_count(match_spec, extracted)
        if match_type == "text_block_count":
            return self._match_text_block_count(match_spec, extracted)
        if match_type == "regex":
            return self._match_regex(match_spec, extracted)

        return False, {}, f"Unknown match type '{match_type}' — rule could not be evaluated"

    def _all_text(self, extracted: ExtractedContent) -> str:
        parts = [block.get("text", "") for block in extracted.text_blocks]
        for table in extracted.tables:
            for row in table.get("rows", []):
                parts.extend(str(cell) for cell in row)
            parts.extend(str(h) for h in table.get("headers", []))
        return "\n".join(parts)

    def _match_data_quality_finding(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        if not extracted.data_quality:
            return False, {}, "No data quality analysis available for this file type"
        target = spec.get("finding_type")
        dq_findings = extracted.data_quality.get("findings", [])
        hits = [f for f in dq_findings if f.get("type") == target]
        if hits:
            columns = [h.get("column") for h in hits if h.get("column")]
            explanation_parts = [h.get("message", "") for h in hits if h.get("message")]
            explanation = "; ".join(explanation_parts) if explanation_parts else (
                f"Data quality check found {len(hits)} '{target}' issue(s)"
            )
            return True, {"findings": hits[:10], "columns_affected": columns}, explanation
        return False, {"checked_findings": len(dq_findings)}, f"No '{target}' data quality issues detected"

    def _match_row_count(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        count = 0
        if extracted.data_quality:
            count = int(extracted.data_quality.get("row_count", 0))
        elif extracted.records:
            count = len(extracted.records)
        operator = spec.get("operator", "gt")
        threshold = int(spec.get("value", 0))
        matched = self._compare(count, operator, threshold)
        evidence = {"row_count": count, "threshold": threshold, "operator": operator}
        explanation = f"Dataset has {count} row(s); rule requires count {operator} {threshold}"
        return matched, evidence, explanation

    def _compare(self, value: int, operator: str, threshold: int) -> bool:
        if operator == "gt":
            return value > threshold
        if operator == "gte":
            return value >= threshold
        if operator == "lt":
            return value < threshold
        if operator == "lte":
            return value <= threshold
        if operator == "eq":
            return value == threshold
        return False

    def _match_column_pattern(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        pattern = re.compile(spec.get("pattern", ""))
        columns: list[str] = []
        if extracted.data_quality:
            columns = [c["name"] for c in extracted.data_quality.get("columns", [])]
        if not columns and extracted.structure.get("headings"):
            headings = extracted.structure["headings"]
            if headings and isinstance(headings[0], dict):
                columns = [h.get("text", "") for h in headings]
            else:
                columns = [str(h) for h in headings]
        if not columns and extracted.records:
            columns = list(extracted.records[0].keys())

        matched_cols = [c for c in columns if pattern.search(c)]
        if matched_cols:
            return (
                True,
                {"columns": matched_cols},
                f"Column name pattern matched: {', '.join(matched_cols)}",
            )
        return (
            False,
            {"columns_checked": columns},
            "No column names matched the required pattern" if columns else "No columns detected to check",
        )

    def _match_keywords(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        terms = spec.get("terms") or []
        min_matches = int(spec.get("min_matches", 1))
        text = self._all_text(extracted).lower()
        if not text.strip():
            return False, {}, "No extractable text found — cannot search for keywords"

        hits: list[dict[str, str]] = []
        for term in terms:
            idx = text.find(term.lower())
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(text), idx + len(term) + 40)
                hits.append({"term": term, "snippet": text[start:end].strip()})

        matched = len(hits) >= min_matches
        if matched:
            found_terms = ", ".join(h["term"] for h in hits)
            explanation = f"Document mentions required topic(s): {found_terms}"
        else:
            examples = ", ".join(f'"{t}"' for t in terms[:4])
            if len(terms) > 4:
                examples += ", …"
            explanation = (
                "Required policy content is missing from this document. "
                f"None of the expected phrases were found (e.g. {examples})."
            )
        return matched, {"keyword_hits": hits[:10], "expected_terms": terms}, explanation

    def _match_log_level(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        level = (spec.get("level") or "").upper()
        counts = (extracted.metadata or {}).get("level_counts", {})
        count = counts.get(level, 0)
        if count > 0:
            snippets = [
                b for b in extracted.text_blocks
                if b.get("level") == level
            ][:5]
            return (
                True,
                {"count": count, "snippets": [s.get("text", "")[:200] for s in snippets]},
                f"Found {count} log entries at {level} level",
            )
        return False, {"level_counts": counts}, f"No {level} log entries detected"

    def _match_log_finding(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        target = spec.get("finding_type")
        log_findings = (extracted.metadata or {}).get("log_findings", [])
        hits = [f for f in log_findings if f.get("type") == target]
        if hits:
            return True, {"findings": hits[:5]}, f"Log analysis detected {len(hits)} '{target}' event(s)"
        return False, {}, f"No '{target}' events found in log file"

    def _match_structure_count(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        field = spec.get("field", "")
        structure = extracted.structure or {}
        items = structure.get(field, [])
        if field == "code_blocks":
            items = structure.get("code_blocks", [])
        count = len(items)
        operator = spec.get("operator", "gte")
        threshold = int(spec.get("value", 1))
        matched = self._compare(count, operator, threshold)
        return (
            matched,
            {"count": count, "field": field},
            f"Structure field '{field}' count is {count} (required {operator} {threshold})",
        )

    def _match_text_block_count(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        count = len(extracted.text_blocks)
        operator = spec.get("operator", "gte")
        threshold = int(spec.get("value", 1))
        matched = self._compare(count, operator, threshold)
        explanation = (
            f"Extracted {count} text block(s); rule requires count {operator} {threshold}"
        )
        if count == 0:
            explanation += " — PDF may be image-only or encrypted"
        return matched, {"text_block_count": count}, explanation

    def _match_regex(
        self, spec: dict[str, Any], extracted: ExtractedContent
    ) -> tuple[bool, dict[str, Any], str]:
        pattern = re.compile(spec.get("pattern", ""))
        min_matches = int(spec.get("min_matches", 1))
        hits: list[dict[str, Any]] = []

        for block in extracted.text_blocks:
            text = block.get("text", "")
            for match in pattern.finditer(text):
                hits.append({
                    "match": match.group(0)[:100],
                    "snippet": text[max(0, match.start() - 30): match.end() + 30],
                    "line": block.get("line"),
                    "page": block.get("page"),
                    "paragraph_index": block.get("paragraph_index"),
                })
                if len(hits) >= 10:
                    break

        matched = len(hits) >= min_matches
        explanation = (
            f"Regex matched {len(hits)} time(s) in text blocks"
            if matched
            else "Regex did not match in extracted text — pattern may be absent or text not extractable"
        )
        return matched, {"matches": hits[:10]}, explanation
