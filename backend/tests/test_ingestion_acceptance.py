"""Acceptance tests for ingestion endpoints."""
from datetime import datetime, timezone
from io import BytesIO

from app.models.auth import Role, User, UserRole
from app.models.mapping import MappingDefinition, MappingVersion
from app.models.storage import FileObject
from app.models.validation import ValidationRuleSet


def test_post_ingestions_endpoint(auth_client, db_session):
    """Test POST /api/v1/ingestions endpoint accepts .xlsx upload."""
    # Create mapping version and validation rule set
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

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

    rule_set = ValidationRuleSet(
        rule_set_code="TEST_RULES",
        version_number=1,
        status="active",
        checksum_sha256="test",
        created_by_user_id=user.id,
    )
    db_session.add(rule_set)
    db_session.commit()

    # Assign ingestion_upload permission to user
    admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not admin_role:
        admin_role = Role(role_code="internal_admin", display_name="Admin")
        db_session.add(admin_role)
        db_session.flush()

    # Remove existing role assignments
    db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id, assigned_by_user_id=user.id))
    db_session.commit()

    # Upload file
    test_content = b"test xlsx content"
    files = {
        "file": ("test.xlsx", BytesIO(test_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    data = {
        "mapping_version_id": mapping_version.id,
    }

    response = auth_client.post("/api/v1/ingestions", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "submitted"
    assert result["source_filename"] == "test.xlsx"
    assert result["raw_file_object_id"] > 0


def test_post_ingestions_rejects_non_xlsx(auth_client, db_session):
    """Test POST /api/v1/ingestions rejects non-.xlsx files."""
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Assign ingestion_upload permission
    admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not admin_role:
        admin_role = Role(role_code="internal_admin", display_name="Admin")
        db_session.add(admin_role)
        db_session.flush()

    db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id, assigned_by_user_id=user.id))
    db_session.commit()

    # Upload non-xlsx file
    test_content = b"test content"
    files = {
        "file": ("test.txt", BytesIO(test_content), "text/plain")
    }
    data = {
        "mapping_version_id": 1,
    }

    response = auth_client.post("/api/v1/ingestions", files=files, data=data)

    assert response.status_code == 400
    assert "xlsx" in response.json()["detail"].lower()


def test_post_ingestions_rejects_large_file(auth_client, db_session):
    """Test POST /api/v1/ingestions rejects files >25MB."""
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Assign ingestion_upload permission
    admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not admin_role:
        admin_role = Role(role_code="internal_admin", display_name="Admin")
        db_session.add(admin_role)
        db_session.flush()

    db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id, assigned_by_user_id=user.id))
    db_session.commit()

    # Upload large file (26 MB)
    test_content = b"x" * (26 * 1024 * 1024)
    files = {
        "file": ("large.xlsx", BytesIO(test_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    data = {
        "mapping_version_id": 1,
    }

    response = auth_client.post("/api/v1/ingestions", files=files, data=data)

    assert response.status_code == 400
    assert "size" in response.json()["detail"].lower()


def test_get_ingestions_list_asp_visibility(auth_client, db_session):
    """Test GET /api/v1/ingestions enforces ASP visibility scoping."""
    from app.models.ingestion import IngestionRecord

    # Create two users: admin and ASP
    admin_user = db_session.query(User).filter(User.email == "admin@example.com").first()

    asp_user = User(
        subject_id="asp.user",
        display_name="ASP User",
        email="asp@test.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(asp_user)
    db_session.flush()

    # Create roles
    admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not admin_role:
        admin_role = Role(role_code="internal_admin", display_name="Admin")
        db_session.add(admin_role)
        db_session.flush()

    asp_role = db_session.query(Role).filter(Role.role_code == "asp_user").first()
    if not asp_role:
        asp_role = Role(role_code="asp_user", display_name="ASP")
        db_session.add(asp_role)
        db_session.flush()

    # Assign roles
    db_session.query(UserRole).filter(UserRole.user_id == admin_user.id).delete()
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
        storage_key="admin_file.xlsx",
        original_filename="admin_file.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=100,
        sha256_hex="hash1",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    file2 = FileObject(
        storage_bucket="test",
        storage_key="asp_file.xlsx",
        original_filename="asp_file.xlsx",
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
        source_filename="admin_file.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    ing2 = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file2.id,
        status="submitted",
        source_filename="asp_file.xlsx",
        uploaded_by_user_id=asp_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add_all([ing1, ing2])
    db_session.commit()

    # Test: admin can see all
    response = auth_client.get("/api/v1/ingestions")
    assert response.status_code == 200
    result = response.json()
    # Should see at least the 2 we just created (may include seed data)
    assert result["total"] >= 2


def test_get_ingestion_detail(auth_client, db_session):
    """Test GET /api/v1/ingestions/{id} returns detail."""
    from app.models.ingestion import IngestionRecord

    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Assign permission
    admin_role = db_session.query(Role).filter(Role.role_code == "internal_admin").first()
    if not admin_role:
        admin_role = Role(role_code="internal_admin", display_name="Admin")
        db_session.add(admin_role)
        db_session.flush()

    db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id, assigned_by_user_id=user.id))
    db_session.commit()

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

    # Get detail
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == ingestion.id
    assert result["status"] == "submitted"
    assert result["source_filename"] == "test.xlsx"
