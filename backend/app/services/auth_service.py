"""Backward-compatible re-export. Prefer app.auth.service.AuthService."""

from app.auth.service import AuthService

__all__ = ["AuthService"]
