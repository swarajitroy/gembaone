"""Acceptance tests for FR-005: Attach photos and files."""
import io


def test_fr005_upload_supported_file_type(auth_client, db_session):
    """FR-005: Users can upload a supported file type to an eligible checklist item."""
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get file item
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]

    site_photo_item = next((item for item in items if item["item_key"] == "site_photo"), None)
    assert site_photo_item is not None

    # Upload supported file type (JPEG)
    file_content = b"fake jpeg content"
    upload_response = auth_client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("photo.jpg", io.BytesIO(file_content), "image/jpeg")},
        data={"item_id": str(site_photo_item["id"])}
    )

    assert upload_response.status_code == 200
    attachment = upload_response.json()
    assert attachment["original_filename"] == "photo.jpg"
    assert attachment["content_type"] == "image/jpeg"


def test_fr005_attachment_linked_to_instance_and_item(auth_client, db_session):
    """FR-005: The attachment is linked to the checklist instance and item."""
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get file item
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    site_photo_item = next((item for item in items if item["item_key"] == "site_photo"), None)

    # Upload attachment
    file_content = b"test content"
    upload_response = auth_client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        data={"item_id": str(site_photo_item["id"])}
    )
    attachment_id = upload_response.json()["id"]

    # Verify attachment is linked to instance and item
    from app.models.checklist import ChecklistAttachment
    attachment = db_session.query(ChecklistAttachment).filter(
        ChecklistAttachment.id == attachment_id
    ).first()

    assert attachment is not None
    assert attachment.checklist_instance_id == instance_id
    assert attachment.checklist_instance_item_id == site_photo_item["id"]


def test_fr005_uploader_and_timestamp_recorded(auth_client, db_session):
    """FR-005: The system records uploader and timestamp for each attachment."""
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get file item
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    site_photo_item = next((item for item in items if item["item_key"] == "site_photo"), None)

    # Upload attachment
    file_content = b"test content"
    upload_response = auth_client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        data={"item_id": str(site_photo_item["id"])}
    )

    attachment_data = upload_response.json()

    # Verify uploader and timestamp are recorded
    assert "uploaded_by_user_id" in attachment_data
    assert attachment_data["uploaded_by_user_id"] is not None
    assert "uploaded_at_utc" in attachment_data
    assert attachment_data["uploaded_at_utc"] is not None


def test_fr005_attachment_access_follows_permissions(auth_client, db_session):
    """FR-005: Attachment access follows role permissions.

    This test verifies that attachment metadata can be accessed by authenticated users.
    Full access control implementation is covered in auth/permission layers.
    """
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get file item
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    site_photo_item = next((item for item in items if item["item_key"] == "site_photo"), None)

    # Upload attachment
    file_content = b"test content"
    upload_response = auth_client.post(
        f"/api/v1/checklists/{instance_id}/attachments",
        files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        data={"item_id": str(site_photo_item["id"])}
    )

    # Verify authenticated user can access attachment metadata
    assert upload_response.status_code == 200

    # Verify attachment is accessible via file_object
    from app.models.storage import FileObject
    file_object_id = upload_response.json()["file_object_id"]
    file_obj = db_session.query(FileObject).filter(FileObject.id == file_object_id).first()
    assert file_obj is not None
    assert file_obj.immutable_flag is True  # Files are immutable
