"""Integration tests for template CRUD and version flows."""

from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion
from app.schemas.checklist_templates import ChecklistItemRequest, ItemConditionRequest
from app.services.checklist_template_service import ChecklistTemplateService


def test_template_version_flow(db_session, admin_user):
    """Test complete template versioning flow."""
    service = ChecklistTemplateService(db_session)

    # Create initial template
    items_v1 = [
        ChecklistItemRequest(
            item_key="field1",
            label="Field 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    template, version1 = service.create_template(
        template_code="INT-001",
        name="Integration Test Template",
        description="Test template for versioning",
        items=items_v1,
        user=admin_user,
        correlation_id="test-corr",
    )

    assert template.template_code == "INT-001"
    assert version1.version_number == 1
    assert version1.version_label == "v1.0"
    assert version1.status == "published"
    assert template.current_version_id == version1.id

    # Publish version 2
    items_v2 = [
        ChecklistItemRequest(
            item_key="field1",
            label="Field 1 Updated",
            item_type="text",
            display_order=1,
            is_required=True,
        ),
        ChecklistItemRequest(
            item_key="field2",
            label="Field 2",
            item_type="number",
            display_order=2,
            is_required=False,
        ),
    ]

    version2 = service.publish_version(
        template_id=template.id,
        version_label="v2.0",
        items=items_v2,
        user=admin_user,
        correlation_id="test-corr",
    )

    assert version2.version_number == 2
    assert version2.version_label == "v2.0"
    assert version2.status == "published"

    # Verify template updated
    db_session.refresh(template)
    assert template.current_version_id == version2.id

    # Verify version 1 still exists
    v1_check = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.id == version1.id
    ).first()
    assert v1_check is not None
    assert v1_check.version_number == 1


def test_template_retirement(db_session, admin_user):
    """Test template retirement."""
    service = ChecklistTemplateService(db_session)

    # Create template
    items = [
        ChecklistItemRequest(
            item_key="field1",
            label="Field 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    template, version = service.create_template(
        template_code="INT-002",
        name="Test Template",
        description="Test",
        items=items,
        user=admin_user,
        correlation_id="test-corr",
    )

    assert template.status == "active"

    # Retire template
    retired = service.retire_template(
        template_id=template.id,
        user=admin_user,
        correlation_id="test-corr",
    )

    assert retired.status == "retired"

    # Verify in database
    db_check = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.id == template.id
    ).first()
    assert db_check.status == "retired"


def test_conditional_item_creation(db_session, admin_user):
    """Test creating template with conditional items."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="equipment_type",
            label="Equipment Type",
            item_type="select",
            display_order=1,
            is_required=True,
            options={"choices": ["Type A", "Type B"]},
        ),
        ChecklistItemRequest(
            item_key="extra_field",
            label="Extra Field",
            item_type="text",
            display_order=2,
            is_required=False,
            condition=ItemConditionRequest(
                source_item_key="equipment_type",
                operator="equals",
                expected_value="Type A",
            ),
        ),
    ]

    template, version = service.create_template(
        template_code="INT-003",
        name="Conditional Template",
        description="Test conditional items",
        items=items,
        user=admin_user,
        correlation_id="test-corr",
    )

    # Get items from database
    db_items = service.repository.get_items_by_version(version.id)
    assert len(db_items) == 2

    # Check conditional item has condition
    extra_field_item = [i for i in db_items if i.item_key == "extra_field"][0]
    condition = service.repository.get_condition_by_item(extra_field_item.id)

    assert condition is not None
    assert condition.source_item_key == "equipment_type"
    assert condition.operator == "equals"
    assert condition.expected_value == "Type A"
