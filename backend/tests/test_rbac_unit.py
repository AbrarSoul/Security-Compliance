from uuid import uuid4

import pytest

from app.auth.rbac import AuthContext
from app.auth.security import create_access_token, decode_token
from app.core.permissions import (
    ALL_PERMISSIONS,
    EXECUTION_REQUEST,
    POLICY_MANAGE,
    REPORT_READ,
    ROLE_ADMIN,
    ROLE_AUDITOR,
    ROLE_PERMISSION_MAP,
    ROLE_USER,
    USER_MANAGE,
)
from app.models.user import User


def _fake_user() -> User:
    return User(
        id=uuid4(),
        email="rbac@test.com",
        password_hash="x",
        full_name="RBAC Test",
        is_active=True,
    )


def test_role_permission_map_covers_all_permissions_for_admin():
    assert set(ROLE_PERMISSION_MAP[ROLE_ADMIN]) == set(ALL_PERMISSIONS)


def test_user_role_permissions():
    perms = set(ROLE_PERMISSION_MAP[ROLE_USER])
    assert REPORT_READ in perms
    assert EXECUTION_REQUEST in perms
    assert USER_MANAGE not in perms
    assert POLICY_MANAGE not in perms


def test_auditor_role_permissions():
    perms = set(ROLE_PERMISSION_MAP[ROLE_AUDITOR])
    assert "report:read_all" in perms
    assert "audit:read" in perms
    assert POLICY_MANAGE not in perms
    assert EXECUTION_REQUEST not in perms


def test_auth_context_has_permission():
    user = _fake_user()
    ctx = AuthContext(
        user=user,
        roles=(ROLE_USER,),
        permissions=frozenset({REPORT_READ, EXECUTION_REQUEST}),
    )
    assert ctx.has_permission(EXECUTION_REQUEST)
    assert not ctx.has_permission(USER_MANAGE)
    assert ctx.has_role(ROLE_USER)
    assert not ctx.has_role(ROLE_ADMIN)


def test_access_token_includes_roles_and_permissions():
    user_id = uuid4()
    token = create_access_token(
        user_id,
        roles=[ROLE_USER],
        permissions=[REPORT_READ, EXECUTION_REQUEST],
    )
    payload = decode_token(token)
    assert payload["roles"] == [ROLE_USER]
    assert REPORT_READ in payload["permissions"]
    assert payload["type"] == "access"
