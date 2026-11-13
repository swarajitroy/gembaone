"""Unit tests for evidence service."""
import hashlib
import io
import json

import pytest

from app.models.checklist import (
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistTemplateVersion,
)
from app.services.evidence_service import EvidenceService


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, file: io.BytesIO, content_type: str):
        self.filename = filename
        self.file = file
        self.content_type = content_type


def test_upload_attachment_success(db_session, admin_user):
    """Test successful file upload."""
    # Create template version
    version = ChecklistTemplateVersion(
        template_id=1,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=admin_user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create item
    item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="test_item",
        label="Test Item",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(item)
    db_session.commit()

    # Create mock upload file
    file_content = b"fake jpeg content"
    file = MockUploadFile(
        filename="test.jpg",
        file=io.BytesIO(file_content),
        content_type="image/jpeg"
    )

    # Upload attachment
    service = EvidenceService(db_session)
    result = service.upload_attachment(
        checklist_instance_id=instance.id,
        checklist_instance_item_id=item.id,
        file=file,
        user=admin_user,
    )

    # Verify result
    assert result["id"] is not None
    assert result["file_object_id"] is not None
    assert result["original_filename"] == "test.jpg"
    assert result["content_type"] == "image/jpeg"
    assert result["byte_size"] == len(file_content)
    assert result["sha256_hex"] == hashlib.sha256(file_content).hexdigest()
    assert result["uploaded_by_user_id"] == admin_user.id


def test_upload_attachment_invalid_file_type(db_session, admin_user):
    """Test upload with disallowed file type."""
    # Create template version
    version = ChecklistTemplateVersion(
        template_id=1,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=admin_user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create item
    item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="test_item",
        label="Test Item",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(item)
    db_session.commit()

    # Create mock upload file with disallowed type
    file = MockUploadFile(
        filename="malware.exe",
        file=io.BytesIO(b"fake exe content"),
        content_type="application/x-msdownload"
    )

    # Upload should fail with 400
    service = EvidenceService(db_session)
    with pytest.raises(Exception) as exc_info:
        service.upload_attachment(
            checklist_instance_id=instance.id,
            checklist_instance_item_id=item.id,
            file=file,
            user=admin_user,
        )

    assert exc_info.value.status_code == 400
    assert "not allowed" in str(exc_info.value.detail)


def test_upload_attachment_exceeds_size_limit(db_session, admin_user):
    """Test upload exceeding size limit."""
    # Create template version
    version = ChecklistTemplateVersion(
        template_id=1,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=admin_user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create item
    item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="test_item",
        label="Test Item",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(item)
    db_session.commit()

    # Create mock upload file exceeding 25MB
    large_content = b"x" * (26 * 1024 * 1024)  # 26MB
    file = MockUploadFile(
        filename="large.jpg",
        file=io.BytesIO(large_content),
        content_type="image/jpeg"
    )

    # Upload should fail with 400
    service = EvidenceService(db_session)
    with pytest.raises(Exception) as exc_info:
        service.upload_attachment(
            checklist_instance_id=instance.id,
            checklist_instance_item_id=item.id,
            file=file,
            user=admin_user,
        )

    assert exc_info.value.status_code == 400
    assert "exceeds maximum" in str(exc_info.value.detail)


def test_upload_attachment_item_not_found(db_session, admin_user):
    """Test upload with non-existent item."""
    # Create template version
    version = ChecklistTemplateVersion(
        template_id=1,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=admin_user.id,
    )
    db_session.add(instance)
    db_session.commit()

    # Create mock upload file
    file = MockUploadFile(
        filename="test.jpg",
        file=io.BytesIO(b"fake jpeg content"),
        content_type="image/jpeg"
    )

    # Upload should fail with 404 (item not found)
    service = EvidenceService(db_session)
    with pytest.raises(Exception) as exc_info:
        service.upload_attachment(
            checklist_instance_id=instance.id,
            checklist_instance_item_id=99999,  # Non-existent
            file=file,
            user=admin_user,
        )

    assert exc_info.value.status_code == 404


def test_sha256_checksum_recorded(db_session, admin_user):
    """Test that SHA256 checksum is correctly computed and recorded."""
    # Create template version
    version = ChecklistTemplateVersion(
        template_id=1,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({}),
    )
    db_session.add(version)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=admin_user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create item
    item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="test_item",
        label="Test Item",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(item)
    db_session.commit()

    # Create mock upload file with known content
    file_content = b"test content for checksum"
    expected_sha256 = hashlib.sha256(file_content).hexdigest()

    file = MockUploadFile(
        filename="test.jpg",
        file=io.BytesIO(file_content),
        content_type="image/jpeg"
    )

    # Upload attachment
    service = EvidenceService(db_session)
    result = service.upload_attachment(
        checklist_instance_id=instance.id,
        checklist_instance_item_id=item.id,
        file=file,
        user=admin_user,
    )

    # Verify SHA256 matches expected
    assert result["sha256_hex"] == expected_sha256

    # Verify file_object record has correct checksum
    from app.models.storage import FileObject
    file_obj = db_session.query(FileObject).filter(FileObject.id == result["file_object_id"]).first()
    assert file_obj is not None
    assert file_obj.sha256_hex == expected_sha256
