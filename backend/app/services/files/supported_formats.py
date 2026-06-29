"""Supported dataset upload formats shared across validation, metadata, and scanning."""

ALLOWED_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
    ".md",
    ".pdf",
    ".docx",
    ".xlsx",
}

SUPPORTED_FILE_TYPES = [
    "CSV",
    "TSV",
    "JSON",
    "JSONL",
    "NDJSON",
    "TXT",
    "XML",
    "YAML",
    "YML",
    "LOG",
    "MD",
    "PDF",
    "DOCX",
    "XLSX",
]

ALLOWED_EXTENSIONS_NO_DOT = frozenset(ext.lstrip(".") for ext in ALLOWED_EXTENSIONS)

DEFAULT_ALLOWED_EXTENSIONS = ",".join(sorted(ALLOWED_EXTENSIONS_NO_DOT))

TEXT_LIKE_EXTENSIONS = frozenset({"txt", "log", "md"})
DOCUMENT_EXTENSIONS = frozenset({"pdf", "docx"})
SPREADSHEET_EXTENSIONS = frozenset({"xlsx"})
JSON_LINE_EXTENSIONS = frozenset({"jsonl", "ndjson"})
YAML_EXTENSIONS = frozenset({"yaml", "yml"})

DELIMITED_DELIMITERS: dict[str, str] = {"csv": ",", "tsv": "\t"}

ALLOWED_CONTENT_TYPES: dict[str, set[str]] = {
    "csv": {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel"},
    "tsv": {"text/tab-separated-values", "text/plain", "application/octet-stream"},
    "json": {"application/json", "text/json", "text/plain"},
    "jsonl": {
        "application/jsonl",
        "application/x-ndjson",
        "application/json",
        "text/plain",
        "application/octet-stream",
    },
    "ndjson": {
        "application/x-ndjson",
        "application/jsonl",
        "application/json",
        "text/plain",
        "application/octet-stream",
    },
    "txt": {"text/plain", "application/octet-stream"},
    "xml": {"application/xml", "text/xml", "application/octet-stream", "text/plain"},
    "yaml": {"application/x-yaml", "text/yaml", "text/plain", "application/octet-stream"},
    "yml": {"application/x-yaml", "text/yaml", "text/plain", "application/octet-stream"},
    "log": {"text/plain", "application/octet-stream"},
    "md": {"text/markdown", "text/plain", "application/octet-stream"},
    "pdf": {"application/pdf", "application/octet-stream"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    },
}
