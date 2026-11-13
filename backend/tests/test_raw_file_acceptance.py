"""Acceptance tests for raw file download - FR-019."""
from datetime import datetime, timezone

from app.models.auth import Role, User, UserRole
from app.models.ingestion import IngestionRecord
from app.models.storage import FileObject


def test_fr019_raw_file_immutable_linkage(client, db_session, admin_user, auth_client):
    """FR-019: The uploaded file is retained outside mutable business record fields."""
    # Create file object with immutable flag
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/immutable.xlsx",
        original_filename="immutable.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="immutable_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion linking to immutable file
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="immutable.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Verify immutable flag is set
    assert file_obj.immutable_flag is True

    # Get raw file download
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/raw-file")
    assert response.status_code == 200

    data = response.json()
    assert data["original_filename"] == "immutable.xlsx"


def test_fr019_stable_reference(client, db_session, admin_user, auth_client):
    """FR-019: The ingestion record stores a stable reference to the original upload."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/stable.xlsx",
        original_filename="stable.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=2048,
        sha256_hex="stable_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    original_file_id = file_obj.id

    # Create ingestion with stable reference
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="stable.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Verify stable reference
    assert ingestion.raw_file_object_id == original_file_id

    # Get raw file metadata
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/raw-file")
    assert response.status_code == 200


def test_fr019_authorized_metadata_access(client, db_session, admin_user, auth_client):
    """FR-019: Authorized users can retrieve or inspect raw file metadata when permitted."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/metadata.xlsx",
        original_filename="metadata.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=3072,
        sha256_hex="metadata_abc",
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
        source_filename="metadata.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Admin user can access metadata
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/raw-file")
    assert response.status_code == 200

    data = response.json()
    assert "download_url" in data
    assert "expires_at" in data
    assert data["original_filename"] == "metadata.xlsx"
    assert data["byte_size"] == 3072


def test_fr019_asp_permission_restriction(client, db_session, admin_user):
    """FR-019: ASP users can only access their own raw files."""
    # Create ASP user
    asp_role = db_session.query(Role).filter(Role.role_code == "asp_user").first()
    if not asp_role:
        asp_role = Role(role_code="asp_user", display_name="ASP User")
        db_session.add(asp_role)
        db_session.flush()

    asp_user = User(
        subject_id="asp.permission",
        display_name="ASP Permission",
        email="asp_permission@test.com",
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

    # Create admin's file object
    admin_file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/admin_permission.xlsx",
        original_filename="admin_permission.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="admin_permission_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(admin_file_obj)
    db_session.flush()

    # Create admin's ingestion
    admin_ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=admin_file_obj.id,
        status="submitted",
        source_filename="admin_permission.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(admin_ingestion)
    db_session.commit()

    # Test permission check at service level
    import pytest
    from fastapi import HTTPException

    from app.services.raw_file_service import RawFileService

    raw_file_service = RawFileService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        raw_file_service.get_raw_file_metadata(admin_ingestion.id, asp_user)

    assert exc_info.value.status_code == 403
