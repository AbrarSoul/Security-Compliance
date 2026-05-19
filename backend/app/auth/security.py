import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def _build_expiry(minutes: int | None = None, days: int | None = None) -> int:
    delta = timedelta(minutes=minutes or 0, days=days or 0)
    return int((datetime.now(UTC) + delta).timestamp())


def create_access_token(
    subject: UUID | str,
    *,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": _build_expiry(minutes=settings.jwt_access_token_expire_minutes),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    if roles is not None:
        payload["roles"] = roles
    if permissions is not None:
        payload["permissions"] = permissions
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: UUID | str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "exp": _build_expiry(days=settings.jwt_refresh_token_expire_days),
        "iat": int(now.timestamp()),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
