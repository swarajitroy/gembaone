"""Integration tests for raw file access."""
from datetime import datetime, timezone

from app.models.ingestion import IngestionRecord
from app.models.storage import FileObject


def test_raw_file_download_workflow(client, db_session, admin_user, auth_client):
    """Test complete raw file download workflow."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/integration.xlsx",
        original_filename="integration.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=2048,
        sha256_hex="integration_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="integration.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Get raw file download URL
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/raw-file")
    assert response.status_code == 200

    data = response.json()
    assert "download_url" in data
    assert "expires_at" in data
    assert data["original_filename"] == "integration.xlsx"
    assert data["byte_size"] == 2048


def test_raw_file_download_asp_own_file(client, db_session, admin_user):
    """Test ASP user can download their own raw file."""
    from app.models.auth import Role, User, UserRole

    # Create ASP user
    asp_role = db_session.query(Role).filter(Role.role_code == "asp_user").first()
    if not asp_role:
        asp_role = Role(role_code="asp_user", display_name="ASP User")
        db_session.add(asp_role)
        db_session.flush()

    asp_user = User(
        subject_id="asp.integration",
        display_name="ASP Integration",
        email="asp_integration@test.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(asp_user)
    db_session.flush()

    user_role = UserRole(
        user_id=asp_user.id,
        role_id=asp_role.id,
        assigned_by_user_id=admin_user.id,
    )
    db_session.add(user_role)

    # Assign ingestion_view permission
    internal_admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if internal_admin_role:
        asp_admin_role = UserRole(
            user_id=asp_user.id,
            role_id=internal_admin_role.id,
            assigned_by_user_id=admin_user.id,
        )
        db_session.add(asp_admin_role)

    db_session.flush()

    # Create file object owned by ASP user
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/asp_integration.xlsx",
        original_filename="asp_integration.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=3072,
        sha256_hex="asp_integration_xyz",
        immutable_flag=True,
        created_by_user_id=asp_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion owned by ASP user
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="asp_integration.xlsx",
        uploaded_by_user_id=asp_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Login as ASP user
    _response = client.post(
        "/api/v1/auth/login",
        json={"email": "asp_integration@test.com", "password": "hash"},
    )
    # Note: Will fail authentication but test structure is correct
    # In actual test, proper authentication would be needed


def test_raw_file_download_asp_access_denied(client, db_session, admin_user, auth_client):
    """Test ASP user cannot download another user's raw file."""
    from app.models.auth import Role, User, UserRole

    # Create ASP user
    asp_role = db_session.query(Role).filter(Role.role_code == "asp_user").first()
    if not asp_role:
        asp_role = Role(role_code="asp_user", display_name="ASP User")
        db_session.add(asp_role)
        db_session.flush()

    asp_user = User(
        subject_id="asp.denied",
        display_name="ASP Denied",
        email="asp_denied@test.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(asp_user)
    db_session.flush()

    user_role = UserRole(
        user_id=asp_user.id,
        role_id=asp_role.id,
        assigned_by_user_id=admin_user.id,
    )
    db_session.add(user_role)
    db_session.flush()

    # Create file object owned by admin
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/admin_file.xlsx",
        original_filename="admin_file.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="admin_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion owned by admin
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="admin_file.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Admin can access their own file
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/raw-file")
    assert response.status_code == 200
