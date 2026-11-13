"""Shared test fixtures."""
import os
import tempfile
from pathlib import Path

# Configuration BEFORE anything imports the app
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break

_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ["RATE_LIMIT_ENABLED"] = "false"  # Disable rate limiting in tests

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import app.models.audit  # noqa: F401, E402

# Import all models to register them with Base
import app.models.auth  # noqa: F401, E402
import app.models.checklist  # noqa: F401, E402
import app.models.ingestion  # noqa: F401, E402
import app.models.mapping  # noqa: F401, E402
import app.models.storage  # noqa: F401, E402
import app.models.validation  # noqa: F401, E402
from app.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh database schema for each test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """Provide a database session for tests."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a test client with database override."""
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    from app.models.auth import Role, User, UserRole
    from app.seed import hash_password

    # Create role (check if it exists first)
    role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not role:
        role = Role(role_code="internal_admin", display_name="Internal Administrator")
        db_session.add(role)
        db_session.flush()

    # Create user with original test credentials for backward compatibility
    user = User(
        subject_id="test.admin",
        display_name="Test Admin",
        email="admin@test.com",
        hashed_password=hash_password("Test-pass-1"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Assign role
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        assigned_by_user_id=user.id,
    )
    db_session.add(user_role)
    db_session.commit()

    return user


@pytest.fixture
def auth_client(client, db_session):
    """Logged in test client through the app's own login."""
    from app.models.auth import Role, User, UserRole
    from app.seed import hash_password

    # Create role (check if it exists first)
    role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not role:
        role = Role(role_code="internal_admin", display_name="Internal Administrator")
        db_session.add(role)
        db_session.flush()

    # Create user for auth tests
    user = db_session.query(User).filter(User.email == "admin@example.com").first()
    if not user:
        user = User(
            subject_id="test.admin.auth",
            display_name="Test Admin Auth",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        # Assign role
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=user.id,
        )
        db_session.add(user_role)
        db_session.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200, response.text
    token = response.json().get("access_token")
    if token:
        client.headers["Authorization"] = f"Bearer {token}"
    return client
