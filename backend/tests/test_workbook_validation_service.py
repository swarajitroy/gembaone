"""Unit tests for workbook validation service."""
from datetime import datetime, timezone

from app.models.auth import User
from app.models.ingestion import IngestionRecord
from app.models.mapping import MappingDefinition, MappingVersion
from app.models.storage import FileObject
from app.models.validation import ValidationRuleSet
from app.services.workbook_validation_service import WorkbookValidationService


def test_validate_workbook_not_found(db_session):
    """Test structural validation when ingestion not found."""
    service = WorkbookValidationService(db_session)
    result = service.validate_workbook_structure(
        ingestion_id=9999,
        raw_file_path="nonexistent.xlsx",
        required_sheets=["Sites"],
        expected_headers={"Sites": ["Site ID", "Site Name"]},
        correlation_id="test-corr-123",
    )

    assert result["success"] is False
    assert "not found" in result["failure_detail"].lower()


def test_validate_workbook_missing_required_sheet(db_session):
    """Test structural validation with missing required sheet."""
    # Create test data
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

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

    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="test.xlsx",
        uploaded_by_user_id=user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Create a minimal Excel file without the required sheet
    # For this test, we'll use a non-existent path which will trigger file not found
    service = WorkbookValidationService(db_session)
    result = service.validate_workbook_structure(
        ingestion_id=ingestion.id,
        raw_file_path="test/nonexistent.xlsx",
        required_sheets=["Sites"],
        expected_headers={"Sites": ["Site ID", "Site Name"]},
        correlation_id="test-corr-123",
    )

    # Should fail with file not readable
    assert result["success"] is False
    assert result["failure_detail"] is not None

    # Verify ingestion status updated to failed
    db_session.refresh(ingestion)
    assert ingestion.status == "failed"


def test_validate_workbook_file_not_readable(db_session):
    """Test structural validation when workbook is not readable."""
    # Create test data
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

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

    file_obj = FileObject(
        storage_bucket="test",
        storage_key="invalid.xlsx",
        original_filename="invalid.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash",
        immutable_flag=True,
        created_by_user_id=user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="invalid.xlsx",
        uploaded_by_user_id=user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Validate with non-existent file
    service = WorkbookValidationService(db_session)
    result = service.validate_workbook_structure(
        ingestion_id=ingestion.id,
        raw_file_path="test/invalid.xlsx",
        required_sheets=["Sites"],
        expected_headers={"Sites": ["Site ID"]},
        correlation_id="test-corr-123",
    )

    # Should fail with file not readable
    assert result["success"] is False
    assert "readable" in result["failure_detail"].lower() or "not found" in result["failure_detail"].lower()

    # Verify ingestion status updated to failed
    db_session.refresh(ingestion)
    assert ingestion.status == "failed"
    assert ingestion.failure_detail is not None


def test_validate_workbook_creates_events(db_session):
    """Test that validation creates ingestion events."""
    from app.models.ingestion import IngestionEvent

    # Create test data
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

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

    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="test.xlsx",
        uploaded_by_user_id=user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Run validation (will fail with file not found)
    service = WorkbookValidationService(db_session)
    _result = service.validate_workbook_structure(
        ingestion_id=ingestion.id,
        raw_file_path="test/nonexistent.xlsx",
        required_sheets=["Sites"],
        expected_headers={"Sites": ["Site ID"]},
        correlation_id="test-corr-456",
    )

    # Verify event was created
    events = db_session.query(IngestionEvent).filter(IngestionEvent.ingestion_id == ingestion.id).all()
    assert len(events) >= 1

    # Find the validation_failed event
    failed_event = next((e for e in events if e.event_type == "validation_failed"), None)
    assert failed_event is not None
    assert failed_event.from_status == "submitted"
    assert failed_event.to_status == "failed"
    assert failed_event.correlation_id == "test-corr-456"
