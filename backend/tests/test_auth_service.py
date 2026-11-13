"""Tests for auth service."""
import os

import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService


def test_create_access_token(db_session):
    """Test access token creation."""
    auth_service = AuthService(db_session)

    token = auth_service.create_access_token(1, "test@example.com")

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token(db_session):
    """Test token decoding."""
    auth_service = AuthService(db_session)

    token = auth_service.create_access_token(1, "test@example.com")
    payload = auth_service.decode_token(token)

    assert payload["sub"] == "1"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_decode_invalid_token(db_session):
    """Test decoding invalid token."""
    auth_service = AuthService(db_session)

    payload = auth_service.decode_token("invalid-token")

    assert payload == {}


def test_rate_limiting(db_session):
    """Test rate limiting when enabled."""
    auth_service = AuthService(db_session)

    # Temporarily enable rate limiting for this test
    old_value = os.environ.get("RATE_LIMIT_ENABLED")
    os.environ["RATE_LIMIT_ENABLED"] = "true"

    try:
        # First 5 attempts should succeed
        for i in range(5):
            result = auth_service.check_rate_limit("test-rate-limit@example.com")
            assert result is True

        # 6th attempt should fail
        result = auth_service.check_rate_limit("test-rate-limit@example.com")
        assert result is False
    finally:
        # Restore original value
        if old_value:
            os.environ["RATE_LIMIT_ENABLED"] = old_value
        else:
            os.environ.pop("RATE_LIMIT_ENABLED", None)


def test_login_success(db_session, admin_user):
    """Test successful login."""
    auth_service = AuthService(db_session)

    access_token, refresh_token, user = auth_service.login(
        username="admin@test.com",
        password="Test-pass-1",
        client_metadata=None,
        correlation_id="test-corr-id",
    )

    assert access_token is not None
    assert refresh_token is not None
    assert user.id == admin_user.id
    assert user.email == "admin@test.com"


def test_login_invalid_credentials(db_session, admin_user):
    """Test login with invalid credentials."""
    auth_service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.login(
            username="admin@test.com",
            password="wrong-password",
            client_metadata=None,
            correlation_id="test-corr-id",
        )

    assert exc_info.value.status_code == 401
    assert "Invalid credentials" in str(exc_info.value.detail)


def test_login_unknown_user(db_session):
    """Test login with unknown user."""
    auth_service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.login(
            username="unknown@example.com",
            password="password",
            client_metadata=None,
            correlation_id="test-corr-id",
        )

    assert exc_info.value.status_code == 401


def test_get_user_from_token(db_session, admin_user):
    """Test getting user from token."""
    auth_service = AuthService(db_session)

    token = auth_service.create_access_token(admin_user.id, admin_user.email)
    user = auth_service.get_user_from_token(token)

    assert user is not None
    assert user.id == admin_user.id
    assert user.email == admin_user.email


def test_get_user_from_invalid_token(db_session):
    """Test getting user from invalid token."""
    auth_service = AuthService(db_session)

    user = auth_service.get_user_from_token("invalid-token")

    assert user is None
