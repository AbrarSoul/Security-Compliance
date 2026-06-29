"""Backward-compatible re-exports; validation lives in file_validation.py."""

from app.services.files.file_validation import (
    ValidatedUpload,
    raise_unsupported_file_type,
    sanitize_filename,
    unsupported_file_type_response,
    validate_content_type,
    validate_file_magic,
    validate_upload,
)
from app.services.files.supported_formats import ALLOWED_EXTENSIONS, SUPPORTED_FILE_TYPES

__all__ = [
    "ALLOWED_EXTENSIONS",
    "SUPPORTED_FILE_TYPES",
    "ValidatedUpload",
    "raise_unsupported_file_type",
    "sanitize_filename",
    "unsupported_file_type_response",
    "validate_content_type",
    "validate_file_magic",
    "validate_upload",
]
