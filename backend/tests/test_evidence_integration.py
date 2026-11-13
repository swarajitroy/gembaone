"""Integration tests for evidence attachment upload."""
import io
import json

from app.models.auth import Role, User, UserRole
from app.models.checklist import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.seed import hash_password


def test_attachment_upload_flow(client, db_session):
    """Test complete attachment upload flow."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.uploader",
        display_name="Test Uploader",
        email="test.uploader@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.uploader@example.com", "password": "test123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create template with file item
    template = ChecklistTemplate(
        template_code="ATTACH_TEST",
        name="Attachment Test",
        description="Test",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.flush()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="photo",
        label="Photo",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get item ID
    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    item_id = detail_response.json()["items"][0]["id"]

    # Upload attachment
    file_content = b"fake jpeg content for testing"
    upload_response = client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("test_photo.jpg", io.BytesIO(file_content), "image/jpeg")},
        data={"item_id": str(item_id)}
    )

    assert upload_response.status_code == 200
    attachment_data = upload_response.json()

    assert attachment_data["id"] is not None
    assert attachment_data["file_object_id"] is not None
    assert attachment_data["original_filename"] == "test_photo.jpg"
    assert attachment_data["content_type"] == "image/jpeg"
    assert attachment_data["byte_size"] == len(file_content)
    assert attachment_data["uploaded_by_user_id"] == user.id


def test_attachment_file_type_validation(client, db_session):
    """Test that only allowed file types can be uploaded."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.uploader2",
        display_name="Test Uploader 2",
        email="test.uploader2@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.uploader2@example.com", "password": "test123"}
    )
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create template
    template = ChecklistTemplate(
        template_code="TYPE_VALID_TEST",
        name="Type Validation Test",
        description="Test",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.flush()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="photo",
        label="Photo",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    item_id = detail_response.json()["items"][0]["id"]

    # Try to upload .exe file (should fail)
    file_content = b"fake exe content"
    upload_response = client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("malware.exe", io.BytesIO(file_content), "application/x-msdownload")},
        data={"item_id": str(item_id)}
    )

    assert upload_response.status_code == 400
    assert "not allowed" in upload_response.json()["detail"]


def test_attachment_size_validation(client, db_session):
    """Test that files exceeding size limit are rejected."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.uploader3",
        display_name="Test Uploader 3",
        email="test.uploader3@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.uploader3@example.com", "password": "test123"}
    )
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create template
    template = ChecklistTemplate(
        template_code="SIZE_VALID_TEST",
        name="Size Validation Test",
        description="Test",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.flush()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="photo",
        label="Photo",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    item_id = detail_response.json()["items"][0]["id"]

    # Try to upload 26MB file (exceeds 25MB limit, should fail)
    large_content = b"x" * (26 * 1024 * 1024)
    upload_response = client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")},
        data={"item_id": str(item_id)}
    )

    assert upload_response.status_code == 400
    assert "exceeds maximum" in upload_response.json()["detail"]
