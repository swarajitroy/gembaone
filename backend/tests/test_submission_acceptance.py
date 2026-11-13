"""Acceptance tests for checklist submission feature (FR-008, FR-009)."""
import json
from datetime import datetime, timezone

from app.models.auth import User
from app.models.checklist import (
    ChecklistAnswer,
    ChecklistAttachment,
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.models.storage import FileObject


def test_fr008_submission_validates_required_visible_items(auth_client, db_session):
    """FR-008 acceptance: Submission validates required visible items and required evidence."""
    # Get user
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Create template and version
    template = ChecklistTemplate(
        template_code="FR008_TPL",
        name="FR-008 Template",
        description="FR-008 Test description",
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

    # Create required item with evidence required
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="required_field",
        label="Required Field",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item1)
    db_session.flush()

    item2 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="photo_field",
        label="Photo Field",
        item_type="file",
        display_order=2,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(item2)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="FR-008 Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "required_field": {"visible": True, "required": True, "has_condition": False},
            "photo_field": {"visible": True, "required": False, "has_condition": False}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance items
    required_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="required_field",
        label="Required Field",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(required_item)
    db_session.flush()

    photo_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item2.id,
        item_key="photo_field",
        label="Photo Field",
        item_type="file",
        display_order=2,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(photo_item)
    db_session.commit()

    # Attempt submission without required answer and evidence
    response = auth_client.post(f"/api/v1/checklists/{instance.id}/submit")
    assert response.status_code == 400
    data = response.json()
    assert "validation_issues" in data["detail"]
    issues = data["detail"]["validation_issues"]
    assert len(issues) == 2  # Missing required answer and evidence

    # Add required answer
    auth_client.put(
        f"/api/v1/checklists/{instance.id}/answers",
        json={"answers": [{"item_id": required_item.id, "value_type": "text", "value_text": "Answer"}]}
    )

    # Still missing evidence
    response = auth_client.post(f"/api/v1/checklists/{instance.id}/submit")
    assert response.status_code == 400
    data = response.json()
    issues = data["detail"]["validation_issues"]
    assert len(issues) == 1
    assert "attachment" in issues[0]["message"].lower()

    # Add required evidence
    file_obj = FileObject(
        storage_bucket="test",
        storage_key="test.jpg",
        original_filename="test.jpg",
        content_type="image/jpeg",
        byte_size=1024,
        sha256_hex="abcdef",
        immutable_flag=True,
        created_by_user_id=user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    attachment = ChecklistAttachment(
        checklist_instance_id=instance.id,
        checklist_instance_item_id=photo_item.id,
        file_object_id=file_obj.id,
        uploaded_by_user_id=user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(attachment)
    db_session.commit()

    # Now submission should succeed
    response = auth_client.post(f"/api/v1/checklists/{instance.id}/submit")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "submitted"
    assert data["validation_issues"] == []


def test_fr008_submitted_instances_readonly(auth_client, db_session):
    """FR-008 acceptance: Submitted instances become read-only except through authorized follow-up actions."""
    # Get user
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Create template and version
    template = ChecklistTemplate(
        template_code="FR008_RO_TPL",
        name="FR-008 ReadOnly Template",
        description="FR-008 ReadOnly test description",
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

    # Create item
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item1)
    db_session.flush()

    # Create instance and submit it
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="FR-008 ReadOnly Test",
        status="submitted",
        template_snapshot_json=json.dumps({}),
        created_by_user_id=user.id,
        submitted_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(instance_item)
    db_session.commit()

    # Attempt to update answers after submission
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/answers",
        json={"answers": [{"item_id": instance_item.id, "value_type": "text", "value_text": "New answer"}]}
    )
    assert response.status_code == 409
    assert "read-only" in response.json()["detail"].lower()


def test_fr008_submission_records_identity_and_timestamp(auth_client, db_session):
    """FR-008 acceptance: Submission records submitter identity and timestamp."""
    # Get user
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Create template and version
    template = ChecklistTemplate(
        template_code="FR008_ID_TPL",
        name="FR-008 Identity Template",
        description="FR-008 Identity test description",
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

    # Create item
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item1)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="FR-008 Identity Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "field1": {"visible": True, "required": True, "has_condition": False}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(instance_item)
    db_session.flush()

    # Add answer
    answer = ChecklistAnswer(
        checklist_instance_item_id=instance_item.id,
        value_type="text",
        value_text="Test",
        answered_by_user_id=user.id,
        answered_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(answer)
    db_session.commit()

    # Submit
    response = auth_client.post(f"/api/v1/checklists/{instance.id}/submit")
    assert response.status_code == 200
    data = response.json()

    assert data["submitted_by"] == user.id
    assert data["submitted_at"] is not None

    # Verify in database
    db_session.refresh(instance)
    assert instance.submitted_by_user_id == user.id
    assert instance.submitted_at_utc is not None


def test_fr009_review_submitted_checklist(auth_client, db_session):
    """FR-009 acceptance: Reviewers can open a submitted checklist and view all answered items."""
    # Get user
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    # Create template and version
    template = ChecklistTemplate(
        template_code="FR009_TPL",
        name="FR-009 Template",
        description="FR-009 test description",
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

    # Create item
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item1)
    db_session.flush()

    # Create submitted instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="FR-009 Review Test",
        status="submitted",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "field1": {"visible": True, "required": True, "has_condition": False}
        }),
        created_by_user_id=user.id,
        submitted_by_user_id=user.id,
        submitted_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(instance)
    db_session.flush()

    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="field1",
        label="Field 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(instance_item)
    db_session.flush()

    # Add answer
    answer = ChecklistAnswer(
        checklist_instance_item_id=instance_item.id,
        value_type="text",
        value_text="Review answer",
        answered_by_user_id=user.id,
        answered_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(answer)
    db_session.commit()

    # Review - retrieve checklist detail
    response = auth_client.get(f"/api/v1/checklists/{instance.id}")
    assert response.status_code == 200
    data = response.json()

    # Verify submitted status and metadata visible
    assert data["instance"]["status"] == "submitted"
    assert data["instance"]["submitted_by_user_id"] == user.id
    assert data["instance"]["submitted_at_utc"] is not None

    # Verify items visible
    assert len(data["items"]) == 1
    assert data["items"][0]["item_key"] == "field1"

    # Verify template version metadata visible
    assert data["template_version"]["version_label"] == "v1.0"
    assert data["template_version"]["status"] == "published"
