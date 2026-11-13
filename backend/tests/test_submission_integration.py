"""Integration tests for checklist submission workflow."""
import json

from app.models.auth import User
from app.models.checklist import (
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.repositories.answer_repository import AnswerRepository
from app.repositories.checklist_repository import ChecklistRepository
from app.services.checklist_execution_service import ChecklistExecutionService


def test_submission_workflow_complete(db_session):
    """Test complete submission workflow from draft to submitted."""
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

    # Create service
    service = ChecklistExecutionService(db_session)

    # Step 1: Create instance
    instance_id = service.create_instance(
        template_version_id=version.id,
        title="Integration Test",
        user=user,
        correlation_id="corr-int-001",
    )

    # Verify instance is in draft
    repo = ChecklistRepository(db_session)
    instance = repo.get_instance_by_id(instance_id)
    assert instance.status == "draft"

    # Step 2: Add answers
    items = repo.get_items_by_instance(instance_id)
    item = items[0]

    answers = [{"item_id": item.id, "value_type": "text", "value_text": "Integration answer"}]
    service.upsert_answers(instance_id, answers, user, "corr-int-002")

    # Verify answer saved
    answer_repo = AnswerRepository(db_session)
    saved_answers = answer_repo.get_answers_by_instance(instance_id)
    assert len(saved_answers) == 1
    assert saved_answers[0].value_text == "Integration answer"

    # Step 3: Submit checklist
    result = service.submit_checklist(instance_id, user, "corr-int-003")

    # Verify submission result
    assert result["status"] == "submitted"
    assert result["submitted_by"] == user.id
    assert result["validation_issues"] == []

    # Verify instance updated
    db_session.refresh(instance)
    assert instance.status == "submitted"
    assert instance.submitted_by_user_id == user.id
    assert instance.submitted_at_utc is not None

    # Verify audit log
    from app.models.audit import AuditLog
    logs = db_session.query(AuditLog).all()
    submission_logs = [log for log in logs if log.event_type == "checklist_submitted"]
    assert len(submission_logs) > 0


def test_submission_validation_with_conditional_items(db_session):
    """Test submission validation handles conditional items correctly."""
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

    # Create two items - one visible, one conditionally hidden
    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="trigger",
        label="Trigger",
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
        item_key="conditional",
        label="Conditional",
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
        title="Conditional Test",
        status="draft",
        template_snapshot_json=json.dumps({}),
        visibility_trace_json=json.dumps({
            "trigger": {"visible": True, "required": True, "has_condition": False},
            "conditional": {"visible": False, "required": False, "has_condition": True}
        }),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.flush()

    # Create instance items
    trigger_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item1.id,
        item_key="trigger",
        label="Trigger",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(trigger_item)
    db_session.flush()

    conditional_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item2.id,
        item_key="conditional",
        label="Conditional",
        item_type="text",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Add answer only for trigger (conditional is hidden)
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=trigger_item.id,
        value_type="text",
        value_text="Trigger value",
        value_number=None,
        value_boolean=None,
        value_date=None,
        value_json=None,
        answered_by_user_id=user.id,
    )

    # Submit - should succeed because conditional item is hidden
    service = ChecklistExecutionService(db_session)
    result = service.submit_checklist(instance.id, user, "corr-cond-001")

    assert result["status"] == "submitted"
    assert result["validation_issues"] == []

    # Verify instance submitted
    db_session.refresh(instance)
    assert instance.status == "submitted"


def test_submission_correlation_id_in_audit(db_session):
    """Test that submission creates audit event with correlation ID."""
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

    # Create instance
    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Audit Test",
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
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=instance_item.id,
        value_type="text",
        value_text="Test answer",
        value_number=None,
        value_boolean=None,
        value_date=None,
        value_json=None,
        answered_by_user_id=user.id,
    )

    # Submit with specific correlation ID
    service = ChecklistExecutionService(db_session)
    correlation_id = "corr-audit-test-123"
    result = service.submit_checklist(instance.id, user, correlation_id)

    assert result["status"] == "submitted"

    # Verify audit log contains correlation ID
    from app.models.audit import AuditLog
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.event_type == "checklist_submitted",
        AuditLog.entity_id == str(instance.id)
    ).all()

    assert len(audit_logs) == 1
    assert audit_logs[0].correlation_id == correlation_id
    assert audit_logs[0].actor_user_id == user.id
