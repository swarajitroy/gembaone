"""Unit tests for ingestion service."""
from datetime import datetime, timezone
from io import BytesIO

import pytest
from fastapi import HTTPException
from sqlalchemy import func

from app.models.auth import User
from app.services.ingestion_service import IngestionService


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes, content_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        self.filename = filename
        self.content_type = content_type
        self.file = BytesIO(content)


def test_create_ingestion_success(db_session, auth_client):
    """Test successful ingestion creation."""
    # Create test file content
    test_content = b"test file content"
    test_file = MockUploadFile(
        filename="test.xlsx",
        content=test_content,
    )

    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create mapping version and validation rule set (simplified)
    from app.models.mapping import MappingDefinition, MappingVersion
    from app.models.validation import ValidationRuleSet

    mapping_def = MappingDefinition(
        mapping_code="TEST_MAP",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        created_at_utc=db_session.query(func.now()).scalar(),
    )
    db_session.add(mapping_version)
    db_session.flush()

    rule_set = ValidationRuleSet(
        rule_set_code="TEST_RULES",
        version_number=1,
        status="active",
        checksum_sha256="test",
        created_by_user_id=user.id,
    )
    db_session.add(rule_set)
    db_session.commit()

    # Create ingestion
    service = IngestionService(db_session)
    result = service.create_ingestion(
        file=test_file,
        mapping_version_id=mapping_version.id,
        user=user,
        correlation_id="test-corr-123",
    )

    # Verify
    assert result["id"] > 0
    assert result["status"] == "submitted"
    assert result["uploaded_by"] == user.id
    assert result["source_filename"] == "test.xlsx"
    assert result["raw_file_object_id"] > 0


def test_create_ingestion_invalid_extension(db_session):
    """Test ingestion creation with invalid file extension."""
    # Create test file with wrong extension
    test_content = b"test file content"
    test_file = MockUploadFile(
        filename="test.txt",
        content=test_content,
    )

    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create ingestion should fail
    service = IngestionService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.create_ingestion(
            file=test_file,
            mapping_version_id=1,
            user=user,
            correlation_id="test-corr-123",
        )

    assert exc_info.value.status_code == 400
    assert "xlsx" in exc_info.value.detail.lower()


def test_create_ingestion_file_too_large(db_session):
    """Test ingestion creation with file exceeding size limit."""
    # Create large test file (26 MB)
    test_content = b"x" * (26 * 1024 * 1024)
    test_file = MockUploadFile(
        filename="large.xlsx",
        content=test_content,
    )

    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create ingestion should fail
    service = IngestionService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.create_ingestion(
            file=test_file,
            mapping_version_id=1,
            user=user,
            correlation_id="test-corr-123",
        )

    assert exc_info.value.status_code == 400
    assert "size" in exc_info.value.detail.lower()


def test_list_ingestions_asp_visibility(db_session):
    """Test list ingestions with ASP visibility scoping."""
    from app.models.auth import Role, UserRole
    from app.models.ingestion import IngestionRecord
    from app.models.mapping import MappingDefinition, MappingVersion
    from app.models.storage import FileObject
    from app.models.validation import ValidationRuleSet

    # Create users
    admin_user = User(
        subject_id="admin",
        display_name="Admin",
        email="admin@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(admin_user)
    db_session.flush()

    asp_user = User(
        subject_id="asp",
        display_name="ASP",
        email="asp@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(asp_user)
    db_session.flush()

    # Create roles
    admin_role = Role(role_code="internal_admin", display_name="Admin")
    asp_role = Role(role_code="asp_user", display_name="ASP")
    db_session.add_all([admin_role, asp_role])
    db_session.flush()

    # Assign roles
    db_session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id, assigned_by_user_id=admin_user.id))
    db_session.add(UserRole(user_id=asp_user.id, role_id=asp_role.id, assigned_by_user_id=admin_user.id))
    db_session.commit()

    # Create mapping and rule set
    mapping_def = MappingDefinition(
        mapping_code="TEST_MAP",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="published",
    )
    db_session.add(mapping_version)
    db_session.flush()

    rule_set = ValidationRuleSet(
        rule_set_code="TEST_RULES",
        version_number=1,
        status="active",
        checksum_sha256="test",
        created_by_user_id=admin_user.id,
    )
    db_session.add(rule_set)
    db_session.flush()

    # Create file objects
    file1 = FileObject(
        storage_bucket="test",
        storage_key="file1",
        original_filename="file1.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash1",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    file2 = FileObject(
        storage_bucket="test",
        storage_key="file2",
        original_filename="file2.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash2",
        immutable_flag=True,
        created_by_user_id=asp_user.id,
    )
    db_session.add_all([file1, file2])
    db_session.flush()

    # Create ingestions
    ing1 = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file1.id,
        status="submitted",
        source_filename="file1.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    ing2 = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file2.id,
        status="submitted",
        source_filename="file2.xlsx",
        uploaded_by_user_id=asp_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add_all([ing1, ing2])
    db_session.commit()

    # Test: admin can see all
    service = IngestionService(db_session)
    admin_results = service.list_ingestions(user=admin_user)
    assert len(admin_results) == 2

    # Test: ASP can only see own
    asp_results = service.list_ingestions(user=asp_user)
    assert len(asp_results) == 1
    assert asp_results[0]["uploaded_by"] == asp_user.id


def test_get_ingestion_asp_denied(db_session):
    """Test get ingestion with ASP user denied access to other user's ingestion."""
    from app.models.auth import Role, UserRole
    from app.models.ingestion import IngestionRecord
    from app.models.mapping import MappingDefinition, MappingVersion
    from app.models.storage import FileObject
    from app.models.validation import ValidationRuleSet

    # Create users
    admin_user = User(
        subject_id="admin",
        display_name="Admin",
        email="admin@example.com",
        hashed_password="hash",
        is_active=True,
    )
    asp_user = User(
        subject_id="asp",
        display_name="ASP",
        email="asp@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add_all([admin_user, asp_user])
    db_session.flush()

    # Create roles
    admin_role = Role(role_code="internal_admin", display_name="Admin")
    asp_role = Role(role_code="asp_user", display_name="ASP")
    db_session.add_all([admin_role, asp_role])
    db_session.flush()

    # Assign roles
    db_session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id, assigned_by_user_id=admin_user.id))
    db_session.add(UserRole(user_id=asp_user.id, role_id=asp_role.id, assigned_by_user_id=admin_user.id))
    db_session.commit()

    # Create mapping and rule set
    mapping_def = MappingDefinition(
        mapping_code="TEST_MAP",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="published",
    )
    db_session.add(mapping_version)
    db_session.flush()

    rule_set = ValidationRuleSet(
        rule_set_code="TEST_RULES",
        version_number=1,
        status="active",
        checksum_sha256="test",
        created_by_user_id=admin_user.id,
    )
    db_session.add(rule_set)
    db_session.flush()

    # Create file object
    file_obj = FileObject(
        storage_bucket="test",
        storage_key="file1",
        original_filename="file1.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash1",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion by admin
    ing = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="file1.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ing)
    db_session.commit()

    # Test: ASP cannot access admin's ingestion
    service = IngestionService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.get_ingestion(ingestion_id=ing.id, user=asp_user)

    assert exc_info.value.status_code == 403
