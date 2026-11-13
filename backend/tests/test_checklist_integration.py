"""Integration tests for checklist execution."""
import json

from app.models.auth import User
from app.models.checklist import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.repositories.checklist_repository import ChecklistRepository
from app.services.checklist_execution_service import ChecklistExecutionService
from app.services.checklist_review_service import ChecklistReviewService


def test_create_instance_and_retrieve_detail(db_session):
    """Test creating instance and retrieving full detail."""
    # Create test user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create template with items
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.commit()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({"test": "data"}),
    )
    db_session.add(version)
    db_session.commit()

    item1 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="item_1",
        label="Item 1",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    item2 = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="item_2",
        label="Item 2",
        item_type="number",
        display_order=2,
        is_required=False,
        evidence_required=True,
        location_mode="optional",
    )
    db_session.add_all([item1, item2])
    db_session.commit()

    # Create instance
    exec_service = ChecklistExecutionService(db_session)
    instance_id = exec_service.create_instance(
        template_version_id=version.id,
        title="Integration Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    # Retrieve detail
    review_service = ChecklistReviewService(db_session)
    detail = review_service.get_checklist_detail(instance_id)

    # Verify response structure
    assert detail.instance.id == instance_id
    assert detail.instance.template_version_id == version.id
    assert detail.instance.title == "Integration Test Instance"
    assert detail.instance.status == "draft"
    assert detail.instance.created_by_user_id == user.id

    # Verify items
    assert len(detail.items) == 2
    assert detail.items[0].item_key == "item_1"
    assert detail.items[0].label == "Item 1"
    assert detail.items[1].item_key == "item_2"
    assert detail.items[1].label == "Item 2"

    # Verify template metadata
    assert detail.template_version.id == version.id
    assert detail.template_version.version_number == 1
    assert detail.template_version.version_label == "v1.0"

    # No locations yet
    assert len(detail.locations) == 0


def test_location_validation(db_session):
    """Test location coordinate validation."""
    # Create test user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create template and instance
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.commit()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({"test": "data"}),
    )
    db_session.add(version)
    db_session.commit()

    exec_service = ChecklistExecutionService(db_session)
    instance_id = exec_service.create_instance(
        template_version_id=version.id,
        title="Location Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    # Test valid latitude/longitude
    location_id = exec_service.capture_instance_location(
        instance_id=instance_id,
        latitude=59.3293,
        longitude=18.0686,
        accuracy_meters=10.0,
        user=user,
        correlation_id="test-corr-456",
    )
    assert location_id is not None

    # Verify location stored correctly
    repo = ChecklistRepository(db_session)
    locations = repo.get_locations_by_instance(instance_id)
    assert len(locations) == 1
    assert locations[0].latitude == 59.3293
    assert locations[0].longitude == 18.0686


def test_full_checklist_workflow(db_session):
    """Test complete workflow: create instance, add locations, retrieve detail."""
    # Create test user
    user = User(
        subject_id="test.user",
        display_name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create template with location-aware item
    template = ChecklistTemplate(
        template_code="TEST_TPL",
        name="Test Template",
        description="Test description",
        status="active",
        created_by_user_id=user.id,
    )
    db_session.add(template)
    db_session.commit()

    version = ChecklistTemplateVersion(
        template_id=template.id,
        version_number=1,
        version_label="v1.0",
        status="published",
        schema_snapshot_json=json.dumps({"test": "data"}),
    )
    db_session.add(version)
    db_session.commit()

    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="location_item",
        label="Location Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="required",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    exec_service = ChecklistExecutionService(db_session)
    instance_id = exec_service.create_instance(
        template_version_id=version.id,
        title="Workflow Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    # Add instance-level location
    exec_service.capture_instance_location(
        instance_id=instance_id,
        latitude=59.3293,
        longitude=18.0686,
        accuracy_meters=10.0,
        user=user,
        correlation_id="test-corr-456",
    )

    # Add item-level location
    repo = ChecklistRepository(db_session)
    instance_items = repo.get_items_by_instance(instance_id)
    item_id = instance_items[0].id

    exec_service.capture_item_location(
        instance_id=instance_id,
        item_id=item_id,
        latitude=59.3320,
        longitude=18.0700,
        accuracy_meters=5.0,
        user=user,
        correlation_id="test-corr-789",
    )

    # Retrieve full detail
    review_service = ChecklistReviewService(db_session)
    detail = review_service.get_checklist_detail(instance_id)

    # Verify complete structure
    assert detail.instance.id == instance_id
    assert len(detail.items) == 1
    assert detail.items[0].location_mode == "required"

    # Verify both locations present
    assert len(detail.locations) == 2

    # Find instance-level location
    instance_locs = [loc for loc in detail.locations if loc.checklist_instance_item_id is None]
    assert len(instance_locs) == 1
    assert instance_locs[0].latitude == 59.3293
    assert instance_locs[0].longitude == 18.0686

    # Find item-level location
    item_locs = [loc for loc in detail.locations if loc.checklist_instance_item_id is not None]
    assert len(item_locs) == 1
    assert item_locs[0].latitude == 59.3320
    assert item_locs[0].longitude == 18.0700
