"""Backward-compatible re-exports. Prefer app.auth.schemas."""

from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

__all__ = [
    "SignupRequest",
    "LoginRequest",
    "RefreshRequest",
    "LogoutRequest",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
]
