"""Extract plain-text, log, and markdown files."""

from __future__ import annotations

import re

from app.services.files.extraction.types import ExtractedContent
from app.services.files.extraction.utils import decode_text

LOG_LEVEL_PATTERN = re.compile(r"\b(ERROR|WARNING|WARN|INFO|DEBUG)\b", re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(
    r"\b\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}"
    r"|\b\d{2}[-/]\d{2}[-/]\d{4}\s+\d{2}:\d{2}:\d{2}"
    r"|\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)
STACK_TRACE_PATTERN = re.compile(r"(Traceback \(most recent call last\)|at \w+\.\w+\()")
FAILED_REQUEST_PATTERN = re.compile(
    r"\b(failed request|request failed|HTTP/\d\.\d\"\s+[45]\d{2})\b",
    re.IGNORECASE,
)
AUTH_FAILURE_PATTERN = re.compile(
    r"\b(auth(entication)? failed|invalid credentials|login failed|unauthorized)\b",
    re.IGNORECASE,
)
TIMEOUT_PATTERN = re.compile(r"\b(timeout|timed out|deadline exceeded)\b", re.IGNORECASE)

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
BULLET_PATTERN = re.compile(r"^[\-\*\+]\s+.+$", re.MULTILINE)
NUMBERED_LIST_PATTERN = re.compile(r"^\d+\.\s+.+$", re.MULTILINE)
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MD_TABLE_PATTERN = re.compile(r"^\|.+\|$", re.MULTILINE)


def extract_txt(content: bytes) -> ExtractedContent:
    text = decode_text(content)
    lines = text.splitlines()
    text_blocks = [
        {"text": line, "line": idx}
        for idx, line in enumerate(lines, start=1)
        if line.strip()
    ]
    return ExtractedContent(
        file_type="txt",
        text_blocks=text_blocks,
        metadata={"line_count": len(lines), "char_count": len(text)},
        structure={"headings": [], "sections": [], "pages": [], "sheets": []},
    )


def extract_log(content: bytes) -> ExtractedContent:
    text = decode_text(content)
    lines = text.splitlines()
    text_blocks: list[dict] = []
    level_counts: dict[str, int] = {}
    timestamps: list[str] = []
    findings: list[dict] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        block: dict = {"text": stripped, "line": idx}
        level_match = LOG_LEVEL_PATTERN.search(stripped)
        if level_match:
            level = level_match.group(1).upper()
            if level == "WARN":
                level = "WARNING"
            block["level"] = level
            level_counts[level] = level_counts.get(level, 0) + 1
        ts_match = TIMESTAMP_PATTERN.search(stripped)
        if ts_match:
            block["timestamp"] = ts_match.group(0)
            timestamps.append(ts_match.group(0))
        text_blocks.append(block)

        if STACK_TRACE_PATTERN.search(stripped):
            findings.append({
                "type": "stack_trace",
                "severity": "high",
                "line": idx,
                "evidence": {"snippet": stripped[:200]},
            })
        if FAILED_REQUEST_PATTERN.search(stripped):
            findings.append({
                "type": "failed_request",
                "severity": "high",
                "line": idx,
                "evidence": {"snippet": stripped[:200]},
            })
        if AUTH_FAILURE_PATTERN.search(stripped):
            findings.append({
                "type": "authentication_failure",
                "severity": "critical",
                "line": idx,
                "evidence": {"snippet": stripped[:200]},
            })
        if TIMEOUT_PATTERN.search(stripped):
            findings.append({
                "type": "timeout_error",
                "severity": "high",
                "line": idx,
                "evidence": {"snippet": stripped[:200]},
            })

    for level in ("ERROR", "WARNING", "INFO", "DEBUG"):
        count = level_counts.get(level, 0)
        if count > 0:
            findings.append({
                "type": f"log_{level.lower()}",
                "severity": "high" if level == "ERROR" else "medium" if level == "WARNING" else "low",
                "message": f"Detected {count} {level} log entries",
                "evidence": {"count": count, "level": level},
            })

    return ExtractedContent(
        file_type="log",
        text_blocks=text_blocks,
        metadata={
            "line_count": len(lines),
            "level_counts": level_counts,
            "timestamp_count": len(timestamps),
            "log_findings": findings,
        },
        structure={"headings": [], "sections": [], "pages": [], "sheets": []},
        data_quality={"findings": findings},
    )


def extract_markdown(content: bytes) -> ExtractedContent:
    text = decode_text(content)
    headings = [
        {"level": len(m.group(1)), "text": m.group(2).strip(), "line": text[: m.start()].count("\n") + 1}
        for m in HEADING_PATTERN.finditer(text)
    ]
    bullets = [{"text": m.group(0).strip(), "line": text[: m.start()].count("\n") + 1} for m in BULLET_PATTERN.finditer(text)]
    numbered = [
        {"text": m.group(0).strip(), "line": text[: m.start()].count("\n") + 1}
        for m in NUMBERED_LIST_PATTERN.finditer(text)
    ]
    code_blocks = [
        {"text": m.group(0)[:300], "line": text[: m.start()].count("\n") + 1}
        for m in CODE_BLOCK_PATTERN.finditer(text)
    ]
    links = [
        {"label": m.group(1), "url": m.group(2), "line": text[: m.start()].count("\n") + 1}
        for m in LINK_PATTERN.finditer(text)
    ]
    tables = [
        {"text": m.group(0), "line": text[: m.start()].count("\n") + 1}
        for m in MD_TABLE_PATTERN.finditer(text)
    ]

    sections = [h["text"] for h in headings]
    text_blocks = [
        {"text": line, "line": idx}
        for idx, line in enumerate(text.splitlines(), start=1)
        if line.strip()
    ]

    return ExtractedContent(
        file_type="md",
        text_blocks=text_blocks,
        tables=[{"name": f"table_{i}", "markdown": t["text"], "line": t["line"]} for i, t in enumerate(tables)],
        metadata={
            "heading_count": len(headings),
            "bullet_count": len(bullets),
            "numbered_list_count": len(numbered),
            "code_block_count": len(code_blocks),
            "link_count": len(links),
            "table_count": len(tables),
        },
        structure={
            "headings": headings,
            "sections": sections,
            "pages": [],
            "sheets": [],
            "bullet_lists": bullets[:50],
            "numbered_lists": numbered[:50],
            "code_blocks": code_blocks[:20],
            "links": links[:50],
        },
    )
