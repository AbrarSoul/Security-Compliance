"""Example protected routes demonstrating JWT authentication."""

from fastapi import APIRouter

from app.auth.dependencies import ActiveUser
from app.auth.schemas import MessageResponse, UserResponse

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/profile", response_model=UserResponse)
async def protected_profile(user: ActiveUser):
    """Protected route — requires valid JWT access token."""
    return UserResponse.model_validate(user)


@router.get("/status", response_model=MessageResponse)
async def protected_status(user: ActiveUser):
    """Another protected route example."""
    return MessageResponse(message=f"Authenticated as {user.email}")
