"""Authentication module: signup, login, JWT, protected routes."""

from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.router import router

__all__ = ["router", "get_current_user", "get_current_active_user"]
