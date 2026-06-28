from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PendingUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    approval_status: str
    created_at: datetime


class PendingUserListResponse(BaseModel):
    items: list[PendingUserResponse]
    total: int
    limit: int
    offset: int


class ApproveUserRequest(BaseModel):
    role: str = Field(description="Role to assign: admin, user, or auditor")


class UserActionResponse(BaseModel):
    message: str
    user_id: UUID
