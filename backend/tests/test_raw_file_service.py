"""Unit tests for raw file service."""
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.ingestion import IngestionRecord
from app.models.storage import FileObject
from app.services.raw_file_service import RawFileService


def test_get_raw_file_metadata_success(db_session, admin_user):
    """Test get raw file metadata success."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
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
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Get metadata
    service = RawFileService(db_session)
    metadata = service.get_raw_file_metadata(ingestion.id, admin_user)

    assert metadata["file_object_id"] == file_obj.id
    assert metadata["original_filename"] == "test.xlsx"
    assert metadata["byte_size"] == 1024
    assert metadata["storage_bucket"] == "ingestion-raw-files"
    assert metadata["storage_key"] == "test/file.xlsx"


def test_get_raw_file_metadata_ingestion_not_found(db_session, admin_user):
    """Test get raw file metadata with nonexistent ingestion."""
    service = RawFileService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.get_raw_file_metadata(999, admin_user)

    assert exc_info.value.status_code == 404
    assert "Ingestion not found" in exc_info.value.detail


def test_get_raw_file_metadata_asp_access_denied(db_session, admin_user):
    """Test ASP user cannot access another user's raw file."""
    from app.models.auth import Role, User, UserRole

    # Create ASP user
    asp_role = Role(role_code="asp_user", display_name="ASP User")
    db_session.add(asp_role)
    db_session.flush()

    asp_user = User(
        subject_id="asp.test",
        display_name="ASP Test",
        email="asp@test.com",
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

    # Create file object and ingestion for admin
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # ASP user tries to access admin's file
    service = RawFileService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.get_raw_file_metadata(ingestion.id, asp_user)

    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


def test_get_raw_file_download_success(db_session, admin_user):
    """Test get raw file download URL success."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
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
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Get download URL
    service = RawFileService(db_session)
    result = service.get_raw_file_download(ingestion.id, admin_user)

    assert "download_url" in result
    assert "expires_at" in result
    assert result["original_filename"] == "test.xlsx"
    assert result["byte_size"] == 1024


def test_get_raw_file_download_asp_own_file(db_session, admin_user):
    """Test ASP user can download their own file."""
    from app.models.auth import Role, User, UserRole

    # Create ASP user
    asp_role = Role(role_code="asp_user", display_name="ASP User")
    db_session.add(asp_role)
    db_session.flush()

    asp_user = User(
        subject_id="asp.test",
        display_name="ASP Test",
        email="asp@test.com",
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

    # Create file object and ingestion for ASP user
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/asp_file.xlsx",
        original_filename="asp_test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=2048,
        sha256_hex="def456",
        immutable_flag=True,
        created_by_user_id=asp_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="asp_test.xlsx",
        uploaded_by_user_id=asp_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # ASP user downloads their own file
    service = RawFileService(db_session)
    result = service.get_raw_file_download(ingestion.id, asp_user)

    assert "download_url" in result
    assert result["original_filename"] == "asp_test.xlsx"
    assert result["byte_size"] == 2048
