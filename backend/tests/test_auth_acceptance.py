"""Acceptance tests for auth endpoints."""


def test_login_success(client, admin_user):
    """Test POST /api/v1/auth/login success."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 86400
    assert "user" in data

    user = data["user"]
    assert user["email"] == "admin@example.com"
    # Display name comes from the fixture
    assert user["display_name"] in ["Test Admin", "Admin User"]  # Could be either depending on seed
    assert "internal_admin" in user["role_codes"]
    assert user["is_asp"] is False
    assert user["is_active"] is True

    # Verify correlation ID in response
    assert "X-Correlation-ID" in response.headers


def test_login_invalid_credentials(client, admin_user):
    """Test POST /api/v1/auth/login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_unknown_user(client):
    """Test POST /api/v1/auth/login with unknown user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "password"}
    )

    assert response.status_code == 401


def test_get_me_authenticated(auth_client, admin_user):
    """Test GET /api/v1/auth/me with valid token."""
    response = auth_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "admin@example.com"
    # Display name comes from the fixture
    assert data["display_name"] in ["Test Admin", "Admin User"]  # Could be either depending on seed
    assert "internal_admin" in data["role_codes"]
    assert data["is_asp"] is False


def test_get_me_unauthenticated(client):
    """Test GET /api/v1/auth/me without token."""
    response = client.get("/api/v1/auth/me")

    # HTTPBearer returns 401 when no auth header is provided
    assert response.status_code == 401
