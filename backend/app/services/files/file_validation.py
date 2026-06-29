"""Central file validation: allowed extensions, MIME checks, and rejection responses."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.services.files.supported_formats import (
    ALLOWED_EXTENSIONS,
    ALLOWED_EXTENSIONS_NO_DOT,
    ALLOWED_CONTENT_TYPES,
    DELIMITED_DELIMITERS,
    DOCUMENT_EXTENSIONS,
    JSON_LINE_EXTENSIONS,
    SUPPORTED_FILE_TYPES,
    TEXT_LIKE_EXTENSIONS,
    YAML_EXTENSIONS,
)
from app.services.files.document_text import extract_docx_text, extract_pdf_text
from app.services.files.excel_io import validate_xlsx_content

settings = get_settings()

_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9._\- ]")


@dataclass
class ValidatedUpload:
    extension: str
    file_type: str
    sanitized_name: str
    content: bytes


def unsupported_file_type_response() -> dict:
    return {
        "error": "Unsupported file type",
        "supported_file_types": SUPPORTED_FILE_TYPES,
    }


def raise_unsupported_file_type() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=unsupported_file_type_response(),
    )


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    cleaned = _FILENAME_SAFE.sub("_", base).strip("._ ")
    return cleaned[:255] or "upload"


def extension_from_name(filename: str) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return None
    return suffix.lstrip(".")


def _decode_text_sample(content: bytes) -> str:
    sample = content[:8192]
    try:
        return sample.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return sample.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be valid UTF-8 or Latin-1 text",
            ) from exc


def validate_content_type(extension: str, content_type: str | None) -> None:
    if not content_type:
        return
    allowed = ALLOWED_CONTENT_TYPES.get(extension, set())
    base_type = content_type.split(";")[0].strip().lower()
    if base_type not in allowed and base_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content type '{content_type}' not allowed for .{extension} files",
        )


def validate_file_magic(extension: str, content: bytes) -> None:
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    if extension == "json":
        stripped = _decode_text_sample(content).lstrip()
        if not stripped or stripped[0] not in "{[":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON file content",
            )
        return

    if extension in JSON_LINE_EXTENSIONS:
        text = _decode_text_sample(content)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped[0] not in "{[":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON Lines file content",
                )
            try:
                json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON Lines file content",
                ) from exc
        return

    if extension in DELIMITED_DELIMITERS or extension in TEXT_LIKE_EXTENSIONS:
        _decode_text_sample(content)
        return

    if extension == "xml":
        text = _decode_text_sample(content).lstrip()
        if not text.startswith("<"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid XML file content",
            )
        try:
            ET.fromstring(content[:65536])
        except ET.ParseError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid XML file content",
            ) from exc
        return

    if extension in YAML_EXTENSIONS:
        text = _decode_text_sample(content).lstrip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YAML file content",
            )
        try:
            yaml.safe_load(content.decode("utf-8", errors="replace"))
        except yaml.YAMLError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YAML file content",
            ) from exc
        return

    if extension == "pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file content",
            )
        extract_pdf_text(content)
        return

    if extension == "docx":
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Word document content",
            )
        extract_docx_text(content)
        return

    if extension == "xlsx":
        validate_xlsx_content(content)
        return


async def validate_upload(file: UploadFile) -> ValidatedUpload:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    extension = extension_from_name(file.filename)
    if extension is None:
        raise_unsupported_file_type()

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    validate_content_type(extension, file.content_type)
    validate_file_magic(extension, content)

    return ValidatedUpload(
        extension=extension,
        file_type=extension,
        sanitized_name=sanitize_filename(file.filename),
        content=content,
    )
