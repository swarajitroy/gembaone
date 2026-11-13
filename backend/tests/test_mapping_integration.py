"""Integration tests for mapping CRUD and version flows."""
from app.models.auth import Role, User, UserRole
from app.models.mapping import MappingDefinition, MappingEntry, MappingVersion
from app.seed import hash_password


def test_mapping_crud_full_flow(db_session):
    """Test complete mapping CRUD workflow."""
    # Create user
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

    # Create mapping definition
    mapping = MappingDefinition(
        mapping_code="INT-TEST-001",
        source_entity="Integration Test Source",
        target_entity="IntegrationTarget",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(mapping)
    db_session.flush()

    # Create version
    version = MappingVersion(
        mapping_definition_id=mapping.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_by_user_id=user.id,
    )
    db_session.add(version)
    db_session.flush()

    # Create entries
    entry1 = MappingEntry(
        mapping_version_id=version.id,
        source_column="source_col1",
        target_field="target_field1",
        target_type="string",
        is_required=True,
    )
    entry2 = MappingEntry(
        mapping_version_id=version.id,
        source_column="source_col2",
        target_field="target_field2",
        target_type="number",
        is_required=False,
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()

    # Verify creation
    retrieved_mapping = (
        db_session.query(MappingDefinition).filter(MappingDefinition.mapping_code == "INT-TEST-001").first()
    )
    assert retrieved_mapping is not None
    assert retrieved_mapping.source_entity == "Integration Test Source"

    retrieved_version = (
        db_session.query(MappingVersion)
        .filter(MappingVersion.mapping_definition_id == mapping.id)
        .first()
    )
    assert retrieved_version is not None
    assert retrieved_version.version_number == 1

    retrieved_entries = (
        db_session.query(MappingEntry)
        .filter(MappingEntry.mapping_version_id == version.id)
        .all()
    )
    assert len(retrieved_entries) == 2


def test_mapping_version_supersede_flow(db_session):
    """Test mapping version supersede workflow."""
    # Create user
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

    # Create mapping definition
    mapping = MappingDefinition(
        mapping_code="INT-TEST-002",
        source_entity="Integration Test Source",
        target_entity="IntegrationTarget",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(mapping)
    db_session.flush()

    # Create v1
    version_v1 = MappingVersion(
        mapping_definition_id=mapping.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_by_user_id=user.id,
    )
    db_session.add(version_v1)
    db_session.flush()

    # Create v2
    version_v2 = MappingVersion(
        mapping_definition_id=mapping.id,
        version_number=2,
        version_label="v2.0",
        status="active",
        published_by_user_id=user.id,
    )
    db_session.add(version_v2)
    db_session.flush()

    # Mark v1 as superseded
    version_v1.status = "superseded"
    db_session.commit()

    # Verify v1 is superseded
    v1_check = db_session.query(MappingVersion).filter(MappingVersion.id == version_v1.id).first()
    assert v1_check.status == "superseded"

    # Verify v2 is active
    v2_check = db_session.query(MappingVersion).filter(MappingVersion.id == version_v2.id).first()
    assert v2_check.status == "active"

    # Verify only one active version exists
    active_versions = (
        db_session.query(MappingVersion)
        .filter(
            MappingVersion.mapping_definition_id == mapping.id,
            MappingVersion.status == "active",
        )
        .all()
    )
    assert len(active_versions) == 1
    assert active_versions[0].version_number == 2


def test_mapping_required_field_validation(db_session):
    """Test validation of required target fields."""
    # Create user
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

    # Create mapping definition
    mapping = MappingDefinition(
        mapping_code="INT-TEST-003",
        source_entity="Integration Test Source",
        target_entity="IntegrationTarget",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(mapping)
    db_session.flush()

    # Create version
    version = MappingVersion(
        mapping_definition_id=mapping.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_by_user_id=user.id,
    )
    db_session.add(version)
    db_session.flush()

    # Create entries with mix of required and optional
    entry1 = MappingEntry(
        mapping_version_id=version.id,
        source_column="source_col1",
        target_field="required_field1",
        target_type="string",
        is_required=True,
    )
    entry2 = MappingEntry(
        mapping_version_id=version.id,
        source_column="source_col2",
        target_field="required_field2",
        target_type="number",
        is_required=True,
    )
    entry3 = MappingEntry(
        mapping_version_id=version.id,
        source_column="source_col3",
        target_field="optional_field1",
        target_type="string",
        is_required=False,
    )
    db_session.add_all([entry1, entry2, entry3])
    db_session.commit()

    # Verify required fields can be identified
    required_entries = (
        db_session.query(MappingEntry)
        .filter(
            MappingEntry.mapping_version_id == version.id,
            MappingEntry.is_required == True,  # noqa: E712
        )
        .all()
    )
    assert len(required_entries) == 2
    required_fields = {entry.target_field for entry in required_entries}
    assert required_fields == {"required_field1", "required_field2"}
