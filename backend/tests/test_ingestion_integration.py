"""Integration tests for ingestion upload and lifecycle."""
from datetime import datetime, timezone
from io import BytesIO

from app.models.auth import Role, User, UserRole
from app.models.ingestion import IngestionEvent
from app.models.mapping import MappingDefinition, MappingEntry, MappingVersion
from app.models.storage import FileObject
from app.models.validation import ValidationRuleSet


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes, content_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        self.filename = filename
        self.content_type = content_type
        self.file = BytesIO(content)


def test_upload_ingestion_workflow(db_session):
    """Test complete upload workflow: file storage, ingestion creation, event logging."""
    from app.services.ingestion_service import IngestionService

    # Create user with admin role
    admin_role = Role(role_code="internal_admin", display_name="Admin")
    db_session.add(admin_role)
    db_session.flush()

    user = User(
        subject_id="test.admin",
        display_name="Test Admin",
        email="admin@test.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id, assigned_by_user_id=user.id))
    db_session.commit()

    # Create mapping definition and version
    mapping_def = MappingDefinition(
        mapping_code="TEST_MAP",
        source_entity="Excel",
        target_entity="Target",
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
        published_at_utc=datetime.now(timezone.utc),
        published_by_user_id=user.id,
    )
    db_session.add(mapping_version)
    db_session.flush()

    # Create mapping entries
    entry = MappingEntry(
        mapping_version_id=mapping_version.id,
        source_column="Test Column",
        target_field="test_field",
        target_type="string",
        is_required=True,
    )
    db_session.add(entry)
    db_session.flush()

    # Create validation rule set
    rule_set = ValidationRuleSet(
        rule_set_code="TEST_RULES",
        version_number=1,
        status="active",
        checksum_sha256="test",
        created_by_user_id=user.id,
    )
    db_session.add(rule_set)
    db_session.commit()

    # Create test file
    test_content = b"test xlsx content"
    test_file = MockUploadFile(
        filename="test_upload.xlsx",
        content=test_content,
    )

    # Upload ingestion
    service = IngestionService(db_session)
    result = service.create_ingestion(
        file=test_file,
        mapping_version_id=mapping_version.id,
        user=user,
        correlation_id="test-upload-123",
    )

    # Verify ingestion record created
    assert result["id"] > 0
    assert result["status"] == "submitted"
    assert result["source_filename"] == "test_upload.xlsx"

    # Verify file_object created with immutable flag
    file_obj = db_session.query(FileObject).filter(FileObject.id == result["raw_file_object_id"]).first()
    assert file_obj is not None
    assert file_obj.immutable_flag is True
    assert file_obj.original_filename == "test_upload.xlsx"
    assert file_obj.byte_size == len(test_content)

    # Verify ingestion_event created
    events = db_session.query(IngestionEvent).filter(IngestionEvent.ingestion_id == result["id"]).all()
    assert len(events) == 1
    assert events[0].event_type == "ingestion_uploaded"
    assert events[0].to_status == "submitted"
    assert events[0].correlation_id == "test-upload-123"


def test_ingestion_lifecycle_transitions(db_session):
    """Test ingestion status transitions through lifecycle."""
    from app.repositories.ingestion_repository import IngestionRepository

    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create mapping and rule set
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
    db_session.flush()

    # Create file object
    file_obj = FileObject(
        storage_bucket="test",
        storage_key="test.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash",
        immutable_flag=True,
        created_by_user_id=user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion
    repository = IngestionRepository(db_session)
    ingestion = repository.create_ingestion(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        source_filename="test.xlsx",
        uploaded_by_user_id=user.id,
        status="submitted",
    )

    # Verify initial status
    assert ingestion.status == "submitted"

    # Transition to validating
    updated = repository.update_ingestion_status(
        ingestion_id=ingestion.id,
        status="validating",
        validation_started_at_utc=datetime.now(timezone.utc),
    )
    assert updated.status == "validating"
    assert updated.validation_started_at_utc is not None

    # Transition to failed
    updated = repository.update_ingestion_status(
        ingestion_id=ingestion.id,
        status="failed",
        failure_detail="Test failure",
    )
    assert updated.status == "failed"
    assert updated.failure_detail == "Test failure"


def test_ingestion_events_with_correlation_id(db_session):
    """Test ingestion events are created with correlation ID for tracking."""
    from app.repositories.ingestion_repository import IngestionRepository

    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create mapping and rule set
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
    db_session.flush()

    # Create file object
    file_obj = FileObject(
        storage_bucket="test",
        storage_key="test.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash",
        immutable_flag=True,
        created_by_user_id=user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion
    repository = IngestionRepository(db_session)
    ingestion = repository.create_ingestion(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        source_filename="test.xlsx",
        uploaded_by_user_id=user.id,
    )

    # Create ingestion event with correlation ID
    correlation_id = "test-corr-xyz-789"
    event = repository.create_ingestion_event(
        ingestion_id=ingestion.id,
        event_type="ingestion_uploaded",
        from_status=None,
        to_status="submitted",
        event_message="File uploaded successfully",
        actor_user_id=user.id,
        correlation_id=correlation_id,
    )

    # Verify event created with correlation ID
    assert event.correlation_id == correlation_id
    assert event.event_type == "ingestion_uploaded"
    assert event.to_status == "submitted"
    assert event.actor_user_id == user.id
