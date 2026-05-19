from uuid import uuid4

import pytest

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing_roundtrip():
    hashed = hash_password("SecurePass123")
    assert hashed != "SecurePass123"
    assert verify_password("SecurePass123", hashed)
    assert not verify_password("WrongPass123", hashed)


def test_access_token_encode_decode():
    user_id = uuid4()
    token = create_access_token(
        user_id,
        roles=["user"],
        permissions=["file:upload", "scan:run"],
    )
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["roles"] == ["user"]
    assert "file:upload" in payload["permissions"]
    assert "exp" in payload


def test_refresh_token_type():
    token = create_refresh_token(uuid4())
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_invalid_token_raises():
    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_token("not.a.valid.token")
