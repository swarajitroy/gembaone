"""Tests for checklist execution service."""
import json

import pytest
from fastapi import HTTPException

from app.models.auth import User
from app.models.checklist import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.repositories.checklist_repository import ChecklistRepository
from app.services.checklist_execution_service import ChecklistExecutionService


def test_create_instance_from_published_version(db_session):
    """Test creating checklist instance from published template version."""
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

    # Create template and published version
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

    # Create template item
    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="test_item",
        label="Test Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    service = ChecklistExecutionService(db_session)
    instance_id = service.create_instance(
        template_version_id=version.id,
        title="Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    assert instance_id is not None

    # Verify instance created
    repo = ChecklistRepository(db_session)
    instance = repo.get_instance_by_id(instance_id)
    assert instance is not None
    assert instance.template_version_id == version.id
    assert instance.title == "Test Instance"
    assert instance.status == "draft"
    assert instance.created_by_user_id == user.id

    # Verify instance items created
    instance_items = repo.get_items_by_instance(instance_id)
    assert len(instance_items) == 1
    assert instance_items[0].item_key == "test_item"
    assert instance_items[0].label == "Test Item"


def test_create_instance_from_draft_version_fails(db_session):
    """Test that creating instance from draft version is rejected."""
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

    # Create template and draft version
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
        status="draft",
        schema_snapshot_json=json.dumps({"test": "data"}),
    )
    db_session.add(version)
    db_session.commit()

    # Attempt to create instance should fail
    service = ChecklistExecutionService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.create_instance(
            template_version_id=version.id,
            title="Test Instance",
            user=user,
            correlation_id="test-corr-123",
        )

    assert exc_info.value.status_code == 400
    assert "published" in exc_info.value.detail.lower()


def test_create_instance_nonexistent_version_fails(db_session):
    """Test that creating instance from nonexistent version is rejected."""
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

    # Attempt to create instance with invalid version ID
    service = ChecklistExecutionService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.create_instance(
            template_version_id=99999,
            title="Test Instance",
            user=user,
            correlation_id="test-corr-123",
        )

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_capture_instance_location(db_session):
    """Test capturing instance-level location."""
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

    # Create template, version, and instance
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

    service = ChecklistExecutionService(db_session)
    instance_id = service.create_instance(
        template_version_id=version.id,
        title="Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    # Capture location
    location_id = service.capture_instance_location(
        instance_id=instance_id,
        latitude=59.3293,
        longitude=18.0686,
        accuracy_meters=10.0,
        user=user,
        correlation_id="test-corr-456",
    )

    assert location_id is not None

    # Verify location created
    repo = ChecklistRepository(db_session)
    locations = repo.get_locations_by_instance(instance_id)
    assert len(locations) == 1
    assert locations[0].latitude == 59.3293
    assert locations[0].longitude == 18.0686
    assert locations[0].accuracy_meters == 10.0
    assert locations[0].checklist_instance_item_id is None  # Instance-level


def test_capture_item_location(db_session):
    """Test capturing item-level location."""
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

    # Create template, version, item, and instance
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
        item_key="test_item",
        label="Test Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="optional",
    )
    db_session.add(item)
    db_session.commit()

    service = ChecklistExecutionService(db_session)
    instance_id = service.create_instance(
        template_version_id=version.id,
        title="Test Instance",
        user=user,
        correlation_id="test-corr-123",
    )

    # Get instance item ID
    repo = ChecklistRepository(db_session)
    instance_items = repo.get_items_by_instance(instance_id)
    item_id = instance_items[0].id

    # Capture item location
    location_id = service.capture_item_location(
        instance_id=instance_id,
        item_id=item_id,
        latitude=59.3293,
        longitude=18.0686,
        accuracy_meters=5.0,
        user=user,
        correlation_id="test-corr-789",
    )

    assert location_id is not None

    # Verify location created
    locations = repo.get_locations_by_instance(instance_id)
    assert len(locations) == 1
    assert locations[0].latitude == 59.3293
    assert locations[0].longitude == 18.0686
    assert locations[0].accuracy_meters == 5.0
    assert locations[0].checklist_instance_item_id == item_id  # Item-level


def test_capture_location_invalid_instance(db_session):
    """Test that capturing location for nonexistent instance fails."""
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

    service = ChecklistExecutionService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.capture_instance_location(
            instance_id=99999,
            latitude=59.3293,
            longitude=18.0686,
            accuracy_meters=10.0,
            user=user,
            correlation_id="test-corr-999",
        )

    assert exc_info.value.status_code == 404
