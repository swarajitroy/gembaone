"""Unit tests for answer service (conditional visibility evaluation)."""
import json

from app.models.checklist import (
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistTemplateVersion,
)
from app.services.checklist_execution_service import ChecklistExecutionService


def test_visibility_no_condition(db_session, admin_user):
    """Test visibility evaluation for item with no condition (baseline)."""
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

    # Create item without condition
    item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="test_item",
        label="Test Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(item)
    db_session.commit()

    # Evaluate visibility
    service = ChecklistExecutionService(db_session)
    visibility_trace = service._evaluate_visibility(instance.id, [item])

    # Item with no condition should be visible and required
    assert visibility_trace["test_item"]["visible"] is True
    assert visibility_trace["test_item"]["required"] is True
    assert visibility_trace["test_item"]["has_condition"] is False


def test_visibility_satisfied_equality(db_session, admin_user):
    """Test visibility evaluation when equality condition is satisfied."""
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

    # Create source item and conditional item
    source_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="equipment_type",
        label="Equipment Type",
        item_type="select",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(source_item)

    conditional_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=2,
        item_key="frequency",
        label="Frequency",
        item_type="number",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=json.dumps({
            "source_item_key": "equipment_type",
            "operator": "equals",
            "expected_value": "Radio Unit"
        }),
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Add answer that satisfies condition
    from app.repositories.answer_repository import AnswerRepository
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=source_item.id,
        value_type="text",
        value_text="Radio Unit",
        value_number=None,
        value_boolean=None,
        value_date=None,
        value_json=None,
        answered_by_user_id=admin_user.id,
    )

    # Evaluate visibility
    service = ChecklistExecutionService(db_session)
    visibility_trace = service._evaluate_visibility(instance.id, [source_item, conditional_item])

    # Source item should be visible
    assert visibility_trace["equipment_type"]["visible"] is True
    assert visibility_trace["equipment_type"]["required"] is True

    # Conditional item should be visible (condition satisfied)
    assert visibility_trace["frequency"]["visible"] is True
    assert visibility_trace["frequency"]["required"] is True
    assert visibility_trace["frequency"]["has_condition"] is True


def test_visibility_unsatisfied_equality(db_session, admin_user):
    """Test visibility evaluation when equality condition is NOT satisfied."""
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

    # Create source item and conditional item
    source_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="equipment_type",
        label="Equipment Type",
        item_type="select",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(source_item)

    conditional_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=2,
        item_key="frequency",
        label="Frequency",
        item_type="number",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=json.dumps({
            "source_item_key": "equipment_type",
            "operator": "equals",
            "expected_value": "Radio Unit"
        }),
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Add answer that does NOT satisfy condition
    from app.repositories.answer_repository import AnswerRepository
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=source_item.id,
        value_type="text",
        value_text="Base Station",  # Different from "Radio Unit"
        value_number=None,
        value_boolean=None,
        value_date=None,
        value_json=None,
        answered_by_user_id=admin_user.id,
    )

    # Evaluate visibility
    service = ChecklistExecutionService(db_session)
    visibility_trace = service._evaluate_visibility(instance.id, [source_item, conditional_item])

    # Source item should be visible
    assert visibility_trace["equipment_type"]["visible"] is True
    assert visibility_trace["equipment_type"]["required"] is True

    # Conditional item should be hidden (condition not satisfied)
    assert visibility_trace["frequency"]["visible"] is False
    # When hidden, item is not required
    assert visibility_trace["frequency"]["required"] is False
    assert visibility_trace["frequency"]["has_condition"] is True


def test_visibility_numeric_threshold(db_session, admin_user):
    """Test visibility evaluation with numeric greater_than condition."""
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

    # Create source item and conditional item
    source_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="temperature",
        label="Temperature",
        item_type="number",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(source_item)

    conditional_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=2,
        item_key="cooling_required",
        label="Cooling Required",
        item_type="boolean",
        display_order=2,
        is_required=False,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=json.dumps({
            "source_item_key": "temperature",
            "operator": "greater_than",
            "expected_value": "30"
        }),
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Add answer that satisfies numeric condition
    from app.repositories.answer_repository import AnswerRepository
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=source_item.id,
        value_type="number",
        value_text=None,
        value_number=35.5,  # Greater than 30
        value_boolean=None,
        value_date=None,
        value_json=None,
        answered_by_user_id=admin_user.id,
    )

    # Evaluate visibility
    service = ChecklistExecutionService(db_session)
    visibility_trace = service._evaluate_visibility(instance.id, [source_item, conditional_item])

    # Conditional item should be visible (35.5 > 30)
    assert visibility_trace["cooling_required"]["visible"] is True
    assert visibility_trace["cooling_required"]["has_condition"] is True


def test_visibility_hidden_item_bypass(db_session, admin_user):
    """Test that hidden items are not required for submission."""
    # This test verifies that when an item is hidden by conditional logic,
    # it is marked as not required even if originally configured as required

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

    # Create conditional item that is originally required
    source_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=1,
        item_key="has_feature",
        label="Has Feature",
        item_type="boolean",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(source_item)

    conditional_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=2,
        item_key="feature_details",
        label="Feature Details",
        item_type="text",
        display_order=2,
        is_required=True,  # Originally required
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=json.dumps({
            "source_item_key": "has_feature",
            "operator": "equals",
            "expected_value": "True"
        }),
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Add answer that hides the conditional item
    from app.repositories.answer_repository import AnswerRepository
    answer_repo = AnswerRepository(db_session)
    answer_repo.upsert_answer(
        checklist_instance_item_id=source_item.id,
        value_type="boolean",
        value_text=None,
        value_number=None,
        value_boolean=False,  # Does not equal True
        value_date=None,
        value_json=None,
        answered_by_user_id=admin_user.id,
    )

    # Evaluate visibility
    service = ChecklistExecutionService(db_session)
    visibility_trace = service._evaluate_visibility(instance.id, [source_item, conditional_item])

    # Conditional item should be hidden AND not required
    assert visibility_trace["feature_details"]["visible"] is False
    assert visibility_trace["feature_details"]["required"] is False  # Override original required=True
    assert visibility_trace["feature_details"]["has_condition"] is True
