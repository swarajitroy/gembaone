"""Smoke tests to verify basic application functionality."""


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Ericsson GembaONE Platform"
    assert data["status"] == "running"


def test_database_connection(db_session):
    """Test database connection works."""
    from app.models.auth import Role

    # Create and query a simple record
    role = Role(role_code="test_role", display_name="Test Role")
    db_session.add(role)
    db_session.commit()

    queried_role = db_session.query(Role).filter(Role.role_code == "test_role").first()
    assert queried_role is not None
    assert queried_role.display_name == "Test Role"


def test_admin_user_creation(admin_user, db_session):
    """Test admin user fixture creates user correctly."""
    from app.models.auth import Role, User, UserRole

    user = db_session.query(User).filter(User.email == "admin@test.com").first()
    assert user is not None
    assert user.display_name == "Test Admin"
    assert user.is_active is True

    # Check role assignment through query
    user_roles = db_session.query(UserRole).filter(UserRole.user_id == user.id).all()
    assert len(user_roles) == 1

    role = db_session.query(Role).filter(Role.id == user_roles[0].role_id).first()
    assert role.role_code == "internal_admin"


def test_seed_data_idempotent(db_session):
    """Test seed data runs idempotently."""
    from app.models.auth import Role, User
    from app.seed import seed_data

    # Run seed data twice
    seed_data(db_session)
    first_user_count = db_session.query(User).count()
    first_role_count = db_session.query(Role).count()

    seed_data(db_session)
    second_user_count = db_session.query(User).count()
    second_role_count = db_session.query(Role).count()

    # Counts should be the same
    assert first_user_count == second_user_count
    assert first_role_count == second_role_count

    # Verify expected data exists
    assert db_session.query(Role).filter(Role.role_code == "internal_admin").first() is not None
    assert db_session.query(User).filter(User.email == "admin@example.com").first() is not None
