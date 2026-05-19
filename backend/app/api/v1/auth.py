"""Backward-compatible re-export. Prefer app.auth.router."""

from app.auth.router import router

__all__ = ["router"]
