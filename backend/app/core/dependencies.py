"""Backward-compatible re-exports. Prefer app.auth.dependencies."""

from app.auth.dependencies import (
    ActiveUser,
    CurrentUser,
    get_current_active_user,
    get_current_user,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "CurrentUser",
    "ActiveUser",
]
