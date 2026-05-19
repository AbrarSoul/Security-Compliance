from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    priority: str
    title: str
    description: str
    action_type: str
    finding_type: str | None
    column_name: str | None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime


class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    total: int
