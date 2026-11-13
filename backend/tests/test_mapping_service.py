"""Unit tests for mapping service."""
import pytest
from fastapi import HTTPException

from app.models.auth import Role, User, UserRole
from app.schemas.mappings import CreateMappingRequest, MappingEntryRequest, PublishMappingVersionRequest
from app.seed import hash_password
from app.services.mapping_service import MappingService


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    role = Role(role_code="internal_admin", display_name="Internal Administrator")
    db_session.add(role)
    db_session.flush()

    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password=hash_password("password"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        assigned_by_user_id=user.id,
    )
    db_session.add(user_role)
    db_session.commit()
    return user


def test_create_mapping_definition_success(db_session, test_user):
    """Test creating a new mapping definition."""
    service = MappingService(db_session)

    request = CreateMappingRequest(
        mapping_code="TEST-MAP-001",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
            MappingEntryRequest(
                source_column="col2",
                target_field="field2",
                target_type="number",
                is_required=False,
            ),
        ],
    )

    result = service.create_mapping_definition(request, test_user.id)

    assert result.mapping_code == "TEST-MAP-001"
    assert result.source_entity == "Test Source"
    assert result.target_entity == "TestTarget"
    assert result.status == "active"
    assert result.created_by_user_id == test_user.id
    assert result.current_version is not None
    assert result.current_version.version_number == 1
    assert result.current_version.version_label == "v1.0"
    assert result.current_version.status == "active"
    assert len(result.current_version.entries) == 2


def test_create_mapping_duplicate_code_rejected(db_session, test_user):
    """Test that duplicate mapping codes are rejected."""
    service = MappingService(db_session)

    request = CreateMappingRequest(
        mapping_code="TEST-MAP-001",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )

    # Create first mapping
    service.create_mapping_definition(request, test_user.id)

    # Try to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        service.create_mapping_definition(request, test_user.id)

    assert exc_info.value.status_code == 400
    assert "already exists" in str(exc_info.value.detail)


def test_create_mapping_duplicate_source_columns_rejected(db_session, test_user):
    """Test that duplicate source columns are rejected."""
    service = MappingService(db_session)

    request = CreateMappingRequest(
        mapping_code="TEST-MAP-002",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
            MappingEntryRequest(
                source_column="col1",  # Duplicate
                target_field="field2",
                target_type="string",
                is_required=False,
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_mapping_definition(request, test_user.id)

    assert exc_info.value.status_code == 400
    assert "Duplicate source columns" in str(exc_info.value.detail)


def test_create_mapping_empty_entries_rejected(db_session, test_user):
    """Test that mappings without entries are rejected."""
    service = MappingService(db_session)

    request = CreateMappingRequest(
        mapping_code="TEST-MAP-003",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_mapping_definition(request, test_user.id)

    assert exc_info.value.status_code == 400
    assert "At least one mapping entry is required" in str(exc_info.value.detail)


def test_create_mapping_invalid_target_type_rejected(db_session, test_user):
    """Test that invalid target types are rejected."""
    service = MappingService(db_session)

    request = CreateMappingRequest(
        mapping_code="TEST-MAP-004",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="invalid_type",  # Invalid
                is_required=True,
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_mapping_definition(request, test_user.id)

    assert exc_info.value.status_code == 400
    assert "Invalid target type" in str(exc_info.value.detail)


def test_publish_mapping_version_success(db_session, test_user):
    """Test publishing a new mapping version."""
    service = MappingService(db_session)

    # Create initial mapping
    create_request = CreateMappingRequest(
        mapping_code="TEST-MAP-005",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )
    initial = service.create_mapping_definition(create_request, test_user.id)

    # Publish new version
    publish_request = PublishMappingVersionRequest(
        version_label="v2.0",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
            MappingEntryRequest(
                source_column="col2",
                target_field="field2",
                target_type="number",
                is_required=False,
            ),
        ],
    )

    result = service.publish_mapping_version(initial.id, publish_request, test_user.id)

    assert result.version_number == 2
    assert result.version_label == "v2.0"
    assert result.status == "active"
    assert len(result.entries) == 2

    # Check that previous version is superseded
    from app.repositories.mapping_repository import MappingRepository

    repo = MappingRepository(db_session)
    previous_version = repo.get_version_by_id(initial.current_version.id)
    assert previous_version.status == "superseded"


def test_publish_mapping_version_marks_previous_superseded(db_session, test_user):
    """Test that publishing v3 marks v2 as superseded."""
    service = MappingService(db_session)

    # Create initial mapping
    create_request = CreateMappingRequest(
        mapping_code="TEST-MAP-006",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )
    initial = service.create_mapping_definition(create_request, test_user.id)
    v1_id = initial.current_version.id

    # Publish v2
    publish_v2 = PublishMappingVersionRequest(
        version_label="v2.0",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )
    v2_result = service.publish_mapping_version(initial.id, publish_v2, test_user.id)
    v2_id = v2_result.id

    # Publish v3
    publish_v3 = PublishMappingVersionRequest(
        version_label="v3.0",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )
    v3_result = service.publish_mapping_version(initial.id, publish_v3, test_user.id)

    # Verify v3 is active
    assert v3_result.version_number == 3
    assert v3_result.status == "active"

    # Verify v2 is superseded
    from app.repositories.mapping_repository import MappingRepository

    repo = MappingRepository(db_session)
    v2_check = repo.get_version_by_id(v2_id)
    assert v2_check.status == "superseded"

    # Verify v1 remains superseded
    v1_check = repo.get_version_by_id(v1_id)
    assert v1_check.status == "superseded"


def test_list_mappings_returns_all_with_active_versions(db_session, test_user):
    """Test listing all mappings with their active versions."""
    service = MappingService(db_session)

    # Create two mappings
    for i in range(1, 3):
        request = CreateMappingRequest(
            mapping_code=f"TEST-MAP-00{i}",
            source_entity=f"Test Source {i}",
            target_entity=f"TestTarget{i}",
            entries=[
                MappingEntryRequest(
                    source_column="col1",
                    target_field="field1",
                    target_type="string",
                    is_required=True,
                ),
            ],
        )
        service.create_mapping_definition(request, test_user.id)

    result = service.list_mappings()

    assert result.total >= 2
    assert len(result.items) >= 2

    # Verify each mapping has its active version
    for mapping in result.items:
        if mapping.mapping_code.startswith("TEST-MAP-"):
            assert mapping.current_version is not None
            assert mapping.current_version.status == "active"


def test_resolve_active_mapping_success(db_session, test_user):
    """Test resolving active mapping version by entity code."""
    service = MappingService(db_session)

    # Create mapping
    request = CreateMappingRequest(
        mapping_code="TEST-MAP-007",
        source_entity="Test Source",
        target_entity="TestTarget",
        entries=[
            MappingEntryRequest(
                source_column="col1",
                target_field="field1",
                target_type="string",
                is_required=True,
            ),
        ],
    )
    service.create_mapping_definition(request, test_user.id)

    # Resolve active mapping
    result = service.resolve_active_mapping("TEST-MAP-007")

    assert result is not None
    assert result.status == "active"
    assert result.version_number == 1


def test_resolve_active_mapping_not_found(db_session, test_user):
    """Test resolving active mapping for non-existent code returns None."""
    service = MappingService(db_session)

    result = service.resolve_active_mapping("NON-EXISTENT")

    assert result is None
