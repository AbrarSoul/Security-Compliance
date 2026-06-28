import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import SignupPendingResponse, SignupRequest, TokenResponse, UserResponse
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.core.config import get_settings
from app.core.user_approval import APPROVAL_APPROVED, APPROVAL_PENDING, APPROVAL_REJECTED
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.rbac_service import RbacService

settings = get_settings()


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _login_blocked_detail(user: User) -> str | None:
    if user.approval_status == APPROVAL_PENDING:
        return "Account pending admin approval"
    if user.approval_status == APPROVAL_REJECTED:
        return "Registration was rejected by an administrator"
    if not user.is_active:
        return "Account is inactive"
    if user.approval_status != APPROVAL_APPROVED:
        return "Account is not approved"
    return None


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit = AuditService(db)

    async def signup(self, data: SignupRequest) -> SignupPendingResponse:
        if await self.users.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = await self.users.create(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=False,
            approval_status=APPROVAL_PENDING,
        )
        await self.audit.log(
            AuditAction.AUTH_SIGNUP,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            severity=audit_severity.INFO,
            status="pending",
            metadata={"email": user.email, "approval_status": APPROVAL_PENDING},
        )
        return SignupPendingResponse(
            message=(
                "Registration submitted. An administrator must approve your account "
                "before you can sign in."
            ),
            approval_status=APPROVAL_PENDING,
            email=user.email,
        )

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.authenticate(email, password)
        if user is None:
            await self.audit.log(
                AuditAction.AUTH_LOGIN_FAILED,
                user_id=None,
                resource_type="user",
                severity=audit_severity.MEDIUM,
                status="failure",
                metadata={"email": email.lower()},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        blocked = _login_blocked_detail(user)
        if blocked:
            await self.audit.log(
                AuditAction.AUTH_LOGIN_FAILED,
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                severity=audit_severity.MEDIUM,
                status="failure",
                metadata={
                    "email": user.email,
                    "reason": user.approval_status,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=blocked,
            )
        await self.audit.log(
            AuditAction.AUTH_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={"email": user.email},
        )
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        token_hash = _hash_refresh_token(refresh_token)
        stored = await self.refresh_tokens.get_by_hash(token_hash)

        if not self.refresh_tokens.is_valid(stored):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked or expired",
            )

        user = await self.users.get_by_id(stored.user_id)  # type: ignore[union-attr]
        blocked = None if user is None else _login_blocked_detail(user)
        if blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=blocked,
            )

        await self.refresh_tokens.revoke(stored)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str, user_id: UUID) -> None:
        token_hash = _hash_refresh_token(refresh_token)
        stored = await self.refresh_tokens.get_by_hash_for_user(token_hash, user_id)
        if stored and stored.revoked_at is None:
            await self.refresh_tokens.revoke(stored)
        await self.audit.log(
            AuditAction.AUTH_LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            severity=audit_severity.INFO,
            status="success",
        )

    async def _issue_tokens(self, user: User) -> TokenResponse:
        rbac = await RbacService(self.db).get_user_rbac(user.id)
        access_token = create_access_token(
            user.id,
            roles=rbac.roles,
            permissions=rbac.permissions,
        )
        refresh_token = create_refresh_token(user.id)
        expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)

        await self.refresh_tokens.create(
            user_id=user.id,
            token_hash=_hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        )
