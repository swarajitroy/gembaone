"""Tests for checklist template service."""
import pytest
from fastapi import HTTPException

from app.schemas.checklist_templates import ChecklistItemRequest, ItemConditionRequest
from app.services.checklist_template_service import ChecklistTemplateService


def test_create_template_success(db_session, admin_user):
    """Test successful template creation."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="item1",
            label="Item 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    template, version = service.create_template(
        template_code="TEST-001",
        name="Test Template",
        description="Test description",
        items=items,
        user=admin_user,
        correlation_id="test-corr-id",
    )

    assert template.template_code == "TEST-001"
    assert template.name == "Test Template"
    assert template.status == "active"
    assert version.version_number == 1
    assert version.status == "published"


def test_create_template_duplicate_code(db_session, admin_user):
    """Test creating template with duplicate code."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="item1",
            label="Item 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    # Create first template
    service.create_template(
        template_code="TEST-002",
        name="Test Template",
        description="Test description",
        items=items,
        user=admin_user,
        correlation_id="test-corr-id",
    )

    # Try to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        service.create_template(
            template_code="TEST-002",
            name="Another Template",
            description="Another description",
            items=items,
            user=admin_user,
            correlation_id="test-corr-id",
        )

    assert exc_info.value.status_code == 400
    assert "already exists" in str(exc_info.value.detail)


def test_validate_conditional_items_success(db_session):
    """Test conditional item validation success."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="source",
            label="Source",
            item_type="select",
            display_order=1,
            is_required=True,
        ),
        ChecklistItemRequest(
            item_key="dependent",
            label="Dependent",
            item_type="text",
            display_order=2,
            is_required=False,
            condition=ItemConditionRequest(
                source_item_key="source",
                operator="equals",
                expected_value="yes",
            ),
        ),
    ]

    # Should not raise
    service.validate_conditional_items(items)


def test_validate_conditional_items_unknown_source(db_session):
    """Test conditional item validation with unknown source."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="dependent",
            label="Dependent",
            item_type="text",
            display_order=1,
            is_required=False,
            condition=ItemConditionRequest(
                source_item_key="unknown",
                operator="equals",
                expected_value="yes",
            ),
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        service.validate_conditional_items(items)

    assert exc_info.value.status_code == 400
    assert "unknown source" in str(exc_info.value.detail).lower()


def test_validate_conditional_items_wrong_order(db_session):
    """Test conditional item validation with wrong display order."""
    service = ChecklistTemplateService(db_session)

    items = [
        ChecklistItemRequest(
            item_key="dependent",
            label="Dependent",
            item_type="text",
            display_order=1,
            is_required=False,
            condition=ItemConditionRequest(
                source_item_key="source",
                operator="equals",
                expected_value="yes",
            ),
        ),
        ChecklistItemRequest(
            item_key="source",
            label="Source",
            item_type="select",
            display_order=2,
            is_required=True,
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        service.validate_conditional_items(items)

    assert exc_info.value.status_code == 400
    assert "must appear after" in str(exc_info.value.detail).lower()


def test_list_templates(db_session, admin_user):
    """Test listing templates."""
    service = ChecklistTemplateService(db_session)

    # Create a template
    items = [
        ChecklistItemRequest(
            item_key="item1",
            label="Item 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    service.create_template(
        template_code="TEST-003",
        name="Test Template",
        description="Test description",
        items=items,
        user=admin_user,
        correlation_id="test-corr-id",
    )

    # List templates
    templates, total = service.list_templates(offset=0, limit=10)

    assert total >= 1
    assert any(t.template_code == "TEST-003" for t in templates)


def test_retire_template(db_session, admin_user):
    """Test retiring template."""
    service = ChecklistTemplateService(db_session)

    # Create a template
    items = [
        ChecklistItemRequest(
            item_key="item1",
            label="Item 1",
            item_type="text",
            display_order=1,
            is_required=True,
        )
    ]

    template, _ = service.create_template(
        template_code="TEST-004",
        name="Test Template",
        description="Test description",
        items=items,
        user=admin_user,
        correlation_id="test-corr-id",
    )

    # Retire template
    retired = service.retire_template(
        template_id=template.id,
        user=admin_user,
        correlation_id="test-corr-id",
    )

    assert retired.status == "retired"
