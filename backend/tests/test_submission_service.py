"""Unit tests for checklist submission service."""
import json

import pytest
from fastapi import HTTPException

from app.models.auth import User
from app.models.checklist import (
    ChecklistAnswer,
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.services.checklist_execution_service import ChecklistExecutionService


def test_submit_checklist_success(db_session):
    """Test successful checklist submission."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create template items
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
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "field1": {"visible": True, "required": True, "has_condition": False}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance item
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
    from datetime import datetime, timezone
    answer = ChecklistAnswer(
        checklist_instance_item_id=instance_item.id,
        value_type="text",
        value_text="Test answer",
        answered_by_user_id=user.id,
        answered_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(answer)
    db_session.commit()

    # Submit checklist
    service = ChecklistExecutionService(db_session)
    result = service.submit_checklist(instance.id, user, "corr-123")

    assert result["status"] == "submitted"
    assert result["submitted_by"] == user.id
    assert result["submitted_at"] is not None
    assert result["validation_issues"] == []

    # Verify instance status
    db_session.refresh(instance)
    assert instance.status == "submitted"
    assert instance.submitted_by_user_id == user.id
    assert instance.submitted_at_utc is not None


def test_submit_checklist_missing_required_answer(db_session):
    """Test submission blocked when required visible item is unanswered."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create template item
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="field1",
        label="Required Field",
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
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "field1": {"visible": True, "required": True, "has_condition": False}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance item
    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="field1",
        label="Required Field",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(instance_item)
    db_session.commit()

    # NO answer added - should block submission

    # Submit checklist
    service = ChecklistExecutionService(db_session)
    result = service.submit_checklist(instance.id, user, "corr-123")

    assert result["status"] == "draft"
    assert result["submitted_by"] is None
    assert result["submitted_at"] is None
    assert len(result["validation_issues"]) == 1
    assert result["validation_issues"][0]["code"] == "required_answer_missing"
    assert result["validation_issues"][0]["severity"] == "error"
    assert "Required Field" in result["validation_issues"][0]["message"]

    # Verify instance still in draft
    db_session.refresh(instance)
    assert instance.status == "draft"


def test_submit_checklist_missing_required_evidence(db_session):
    """Test submission blocked when required evidence is missing."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create template item with evidence required
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="photo_field",
        label="Photo Field",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(item1)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "photo_field": {"visible": True, "required": False, "has_condition": False}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance item
    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="photo_field",
        label="Photo Field",
        item_type="file",
        display_order=1,
        is_required=False,
        evidence_required=True,
        location_mode="none",
    )
    db_session.add(instance_item)
    db_session.commit()

    # NO attachment added - should block submission

    # Submit checklist
    service = ChecklistExecutionService(db_session)
    result = service.submit_checklist(instance.id, user, "corr-123")

    assert result["status"] == "draft"
    assert result["submitted_by"] is None
    assert result["submitted_at"] is None
    assert len(result["validation_issues"]) == 1
    assert result["validation_issues"][0]["code"] == "required_evidence_missing"
    assert result["validation_issues"][0]["severity"] == "error"
    assert "Photo Field" in result["validation_issues"][0]["message"]

    # Verify instance still in draft
    db_session.refresh(instance)
    assert instance.status == "draft"


def test_submit_checklist_hidden_items_bypass(db_session):
    """Test submission succeeds when hidden items are unanswered."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create template items - one visible, one hidden
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="visible_field",
        label="Visible Field",
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
        item_key="hidden_field",
        label="Hidden Field",
        item_type="text",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item2)
    db_session.flush()

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "visible_field": {"visible": True, "required": True, "has_condition": False},
            "hidden_field": {"visible": False, "required": False, "has_condition": True}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance items
    visible_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="visible_field",
        label="Visible Field",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(visible_item)
    db_session.flush()

    hidden_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item2.id,
        item_key="hidden_field",
        label="Hidden Field",
        item_type="text",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(hidden_item)
    db_session.flush()

    # Add answer ONLY for visible item
    from datetime import datetime, timezone
    answer = ChecklistAnswer(
        checklist_instance_item_id=visible_item.id,
        value_type="text",
        value_text="Visible answer",
        answered_by_user_id=user.id,
        answered_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(answer)
    db_session.commit()

    # Submit checklist - should succeed even though hidden_field is unanswered
    service = ChecklistExecutionService(db_session)
    result = service.submit_checklist(instance.id, user, "corr-123")

    assert result["status"] == "submitted"
    assert result["submitted_by"] == user.id
    assert result["validation_issues"] == []

    # Verify instance status
    db_session.refresh(instance)
    assert instance.status == "submitted"


def test_submit_checklist_already_submitted(db_session):
    """Test submission fails when checklist already submitted."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create instance already submitted
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="submitted",  # Already submitted
        template_snapshot_json=json.dumps({}),
        created_by_user_id=user.id,
        submitted_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.commit()

    # Try to submit again
    service = ChecklistExecutionService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.submit_checklist(instance.id, user, "corr-123")

    assert exc_info.value.status_code == 409
    assert "Only draft checklists can be submitted" in exc_info.value.detail


def test_upsert_answers_readonly_after_submission(db_session):
    """Test that answers cannot be modified after submission (FR-008)."""
    # Create user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create template and version
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
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

    # Create template item
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

    # Create instance already submitted
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="submitted",  # Already submitted
        template_snapshot_json=json.dumps({}),
        created_by_user_id=user.id,
        submitted_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance item
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

    # Try to upsert answer
    service = ChecklistExecutionService(db_session)
    answers = [{"item_id": instance_item.id, "value_type": "text", "value_text": "New answer"}]

    with pytest.raises(HTTPException) as exc_info:
        service.upsert_answers(instance.id, answers, user, "corr-123")

    assert exc_info.value.status_code == 409
    assert "read-only" in exc_info.value.detail.lower()
