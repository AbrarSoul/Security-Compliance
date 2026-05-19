from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    row_count: int | None
    column_count: int | None
    data_schema: list[dict[str, Any]] | dict[str, Any] | None = Field(
        validation_alias="schema_json", serialization_alias="schema"
    )
    preview: list | dict | str | None = Field(
        validation_alias="preview_json", serialization_alias="preview"
    )
    extra: dict[str, Any] | None = Field(
        validation_alias="extra_json", serialization_alias="extra"
    )
    analyzed_at: datetime


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    file_type: str
    content_type: str | None
    size_bytes: int
    checksum_sha256: str | None
    status: str
    created_at: datetime
    metadata: FileMetadataResponse | None = None


class FileListResponse(BaseModel):
    items: list[FileResponse]
    total: int
    limit: int
    offset: int


class FileUploadResponse(BaseModel):
    message: str = "File uploaded successfully"
    file: FileResponse
