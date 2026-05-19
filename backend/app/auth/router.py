from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import ActiveUser
from app.auth.rbac import AuthContext, get_auth_context
from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserMeResponse,
    UserResponse,
)
from app.auth.service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, auth: AuthService = Depends(get_auth_service)):
    """Register a new user and return JWT tokens."""
    return await auth.signup(body)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    """Authenticate with email/password and return JWT tokens."""
    return await auth.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, auth: AuthService = Depends(get_auth_service)):
    """Exchange a valid refresh token for a new token pair."""
    return await auth.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    user: ActiveUser,
    auth: AuthService = Depends(get_auth_service),
):
    """Revoke the refresh token (requires Bearer access token)."""
    await auth.logout(body.refresh_token, user.id)


@router.get("/me", response_model=UserMeResponse)
async def get_me(ctx: AuthContext = Depends(get_auth_context)):
    """Return the authenticated user with roles and permissions."""
    return UserMeResponse(
        **UserResponse.model_validate(ctx.user).model_dump(),
        roles=list(ctx.roles),
        permissions=sorted(ctx.permissions),
    )
