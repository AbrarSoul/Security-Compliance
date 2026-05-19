import json
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "csv": {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel"},
    "json": {"application/json", "text/json", "text/plain"},
    "txt": {"text/plain", "application/octet-stream"},
}

_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9._\- ]")


@dataclass
class ValidatedUpload:
    extension: str
    file_type: str
    sanitized_name: str
    content: bytes


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    cleaned = _FILENAME_SAFE.sub("_", base).strip("._ ")
    return cleaned[:255] or "upload"


def _extension_from_name(filename: str) -> str | None:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix if suffix in settings.allowed_extensions_set else None


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

    sample = content[:8192]

    if extension == "json":
        try:
            stripped = sample.decode("utf-8").lstrip()
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON file content",
            ) from exc
        if not stripped or stripped[0] not in "{[":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON file content",
            )
        return

    if extension in ("csv", "txt"):
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            try:
                sample.decode("latin-1")
            except UnicodeDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be valid UTF-8 or Latin-1 text",
                ) from exc


async def validate_upload(file: UploadFile) -> ValidatedUpload:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    extension = _extension_from_name(file.filename)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allowed extensions: {', '.join(sorted(settings.allowed_extensions_set))}",
        )

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
