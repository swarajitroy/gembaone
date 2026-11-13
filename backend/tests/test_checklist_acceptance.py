"""Acceptance tests for checklist endpoints."""
import json


def test_create_checklist_instance(auth_client, db_session):
    """Test POST /api/v1/checklists endpoint."""
    from app.models.auth import User
    from app.models.checklist import (
        ChecklistTemplate,
        ChecklistTemplateItem,
        ChecklistTemplateVersion,
    )

    # Create template for testing
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    template = ChecklistTemplate(
        template_code="TEST_CREATE",
        name="Test Create Template",
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
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create checklist instance
    response = auth_client.post(
        "/api/v1/checklists",
        json={
            "template_version_id": version.id,
            "title": "Test Checklist Instance"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["template_version_id"] == version.id
    assert data["title"] == "Test Checklist Instance"
    assert data["status"] == "draft"
    assert "created_at_utc" in data
    assert "id" in data


def test_get_checklist_detail(auth_client, db_session):
    """Test GET /api/v1/checklists/{id} endpoint."""
    from app.models.auth import User
    from app.models.checklist import (
        ChecklistInstance,
        ChecklistInstanceItem,
        ChecklistTemplate,
        ChecklistTemplateItem,
        ChecklistTemplateVersion,
    )

    # Create template and instance for testing
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    template = ChecklistTemplate(
        template_code="TEST_GET",
        name="Test Get Template",
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
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({"test": "snapshot"}),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.commit()

    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item.id,
        item_key="test_item",
        label="Test Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        condition_snapshot_json=None,
    )
    db_session.add(instance_item)
    db_session.commit()

    # Retrieve checklist detail
    response = auth_client.get(f"/api/v1/checklists/{instance.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify instance
    assert data["instance"]["id"] == instance.id
    assert data["instance"]["title"] == "Test Instance"
    assert data["instance"]["status"] == "draft"

    # Verify items
    assert len(data["items"]) == 1
    assert data["items"][0]["item_key"] == "test_item"
    assert data["items"][0]["label"] == "Test Item"

    # Verify template version metadata
    assert data["template_version"]["id"] == version.id
    assert data["template_version"]["version_number"] == 1

    # Verify locations (should be empty)
    assert len(data["locations"]) == 0


def test_capture_instance_location(auth_client, db_session):
    """Test PUT /api/v1/checklists/{id}/location endpoint."""
    from app.models.auth import User
    from app.models.checklist import (
        ChecklistInstance,
        ChecklistTemplate,
        ChecklistTemplateVersion,
    )

    # Create instance for testing
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    template = ChecklistTemplate(
        template_code="TEST_LOC",
        name="Test Location Template",
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

    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({"test": "snapshot"}),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.commit()

    # Capture location
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/location",
        json={
            "latitude": 59.3293,
            "longitude": 18.0686,
            "accuracy_meters": 10.0
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 59.3293
    assert data["longitude"] == 18.0686
    assert data["accuracy_meters"] == 10.0
    assert data["checklist_instance_id"] == instance.id
    assert data["checklist_instance_item_id"] is None


def test_capture_item_location(auth_client, db_session):
    """Test PUT /api/v1/checklists/{id}/items/{itemId}/location endpoint."""
    from app.models.auth import User
    from app.models.checklist import (
        ChecklistInstance,
        ChecklistInstanceItem,
        ChecklistTemplate,
        ChecklistTemplateItem,
        ChecklistTemplateVersion,
    )

    # Create instance with item for testing
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    template = ChecklistTemplate(
        template_code="TEST_ITEM_LOC",
        name="Test Item Location Template",
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

    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({"test": "snapshot"}),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.commit()

    instance_item = ChecklistInstanceItem(
        checklist_instance_id=instance.id,
        template_item_id=item.id,
        item_key="test_item",
        label="Test Item",
        item_type="text",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="optional",
        condition_snapshot_json=None,
    )
    db_session.add(instance_item)
    db_session.commit()

    # Capture item location
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/items/{instance_item.id}/location",
        json={
            "latitude": 59.3320,
            "longitude": 18.0700,
            "accuracy_meters": 5.0
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 59.3320
    assert data["longitude"] == 18.0700
    assert data["accuracy_meters"] == 5.0
    assert data["checklist_instance_id"] == instance.id
    assert data["checklist_instance_item_id"] == instance_item.id


def test_location_validation_rejects_invalid_coordinates(auth_client, db_session):
    """Test that invalid latitude/longitude values are rejected with 400."""
    from app.models.auth import User
    from app.models.checklist import (
        ChecklistInstance,
        ChecklistTemplate,
        ChecklistTemplateVersion,
    )

    # Create instance for testing
    user = db_session.query(User).filter(User.email == "admin@example.com").first()

    template = ChecklistTemplate(
        template_code="TEST_INVALID",
        name="Test Invalid Template",
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

    instance = ChecklistInstance(
        template_version_id=version.id,
        title="Test Instance",
        status="draft",
        template_snapshot_json=json.dumps({"test": "snapshot"}),
        created_by_user_id=user.id,
    )
    db_session.add(instance)
    db_session.commit()

    # Test invalid latitude (> 90)
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/location",
        json={
            "latitude": 95.0,
            "longitude": 18.0686,
            "accuracy_meters": 10.0
        }
    )
    assert response.status_code == 422  # Pydantic validation error

    # Test invalid latitude (< -90)
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/location",
        json={
            "latitude": -95.0,
            "longitude": 18.0686,
            "accuracy_meters": 10.0
        }
    )
    assert response.status_code == 422

    # Test invalid longitude (> 180)
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/location",
        json={
            "latitude": 59.3293,
            "longitude": 185.0,
            "accuracy_meters": 10.0
        }
    )
    assert response.status_code == 422

    # Test invalid longitude (< -180)
    response = auth_client.put(
        f"/api/v1/checklists/{instance.id}/location",
        json={
            "latitude": 59.3293,
            "longitude": -185.0,
            "accuracy_meters": 10.0
        }
    )
    assert response.status_code == 422
