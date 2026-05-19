"""RBAC dependencies and auth context for FastAPI routes."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import ActiveUser, bearer_scheme
from app.auth.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.rbac_service import RbacService

DbSession = Annotated[AsyncSession, Depends(get_db)]


@dataclass(frozen=True)
class AuthContext:
    user: User
    roles: tuple[str, ...]
    permissions: frozenset[str]

    def has_permission(self, code: str) -> bool:
        return code in self.permissions

    def has_any_permission(self, *codes: str) -> bool:
        return any(code in self.permissions for code in codes)

    def has_role(self, name: str) -> bool:
        return name in self.roles

    def has_any_role(self, *names: str) -> bool:
        return any(name in self.roles for name in names)


async def get_auth_context(
    user: ActiveUser,
    db: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    """
    Build auth context from JWT claims when present; otherwise load from the database.
    DB fallback supports tokens issued before RBAC and ensures fresh role data when claims are empty.
    """
    roles: list[str] = []
    permissions: list[str] = []

    if credentials is not None and credentials.scheme.lower() == "bearer":
        try:
            payload = decode_token(credentials.credentials)
            if payload.get("type") == "access":
                raw_roles = payload.get("roles")
                raw_permissions = payload.get("permissions")
                if isinstance(raw_roles, list):
                    roles = [str(r) for r in raw_roles]
                if isinstance(raw_permissions, list):
                    permissions = [str(p) for p in raw_permissions]
        except ValueError:
            pass

    if not roles or not permissions:
        rbac = await RbacService(db).get_user_rbac(user.id)
        roles = rbac.roles
        permissions = rbac.permissions

    return AuthContext(
        user=user,
        roles=tuple(roles),
        permissions=frozenset(permissions),
    )


def require_permission(*required_permissions: str):
    """Dependency factory: user must have all listed permissions."""

    async def _checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        missing = [p for p in required_permissions if p not in ctx.permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission(s): {', '.join(missing)}",
            )
        return ctx

    return _checker


def require_any_permission(*required_permissions: str):
    """Dependency factory: user must have at least one listed permission."""

    async def _checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not ctx.has_any_permission(*required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_permissions)}",
            )
        return ctx

    return _checker


def require_role(*required_roles: str):
    """Dependency factory: user must have at least one listed role."""

    async def _checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not ctx.has_any_role(*required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return ctx

    return _checker
