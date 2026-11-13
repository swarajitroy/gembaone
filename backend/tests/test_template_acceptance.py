"""Acceptance tests for template endpoints."""


def test_create_template(auth_client):
    """Test POST /api/v1/checklist-templates."""
    response = auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-001",
            "name": "Acceptance Test Template",
            "description": "Test template for acceptance testing",
            "items": [
                {
                    "item_key": "field1",
                    "label": "Field 1",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": True,
                }
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["template_code"] == "ACC-001"
    assert data["name"] == "Acceptance Test Template"
    assert data["status"] == "active"
    assert data["current_version_id"] is not None


def test_create_template_with_conditional_items(auth_client):
    """Test creating template with conditional items."""
    response = auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-002",
            "name": "Conditional Template",
            "description": "Template with conditional items",
            "items": [
                {
                    "item_key": "equipment_type",
                    "label": "Equipment Type",
                    "item_type": "single_select",
                    "display_order": 1,
                    "is_required": True,
                    "options": {"choices": ["Radio Unit", "Base Station"]},
                },
                {
                    "item_key": "radio_frequency",
                    "label": "Radio Frequency",
                    "item_type": "number",
                    "display_order": 2,
                    "is_required": True,
                    "condition": {
                        "source_item_key": "equipment_type",
                        "operator": "equals",
                        "expected_value": "Radio Unit",
                    },
                }
            ]
        }
    )

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_create_template_invalid_conditional_order(auth_client):
    """Test creating template with invalid conditional item order."""
    response = auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-003",
            "name": "Invalid Conditional Template",
            "description": "Template with invalid conditional order",
            "items": [
                {
                    "item_key": "dependent",
                    "label": "Dependent Field",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": False,
                    "condition": {
                        "source_item_key": "source",
                        "operator": "equals",
                        "expected_value": "yes",
                    },
                },
                {
                    "item_key": "source",
                    "label": "Source Field",
                    "item_type": "select",
                    "display_order": 2,
                    "is_required": True,
                },
            ]
        }
    )

    assert response.status_code == 400
    assert "must appear after" in response.json()["detail"].lower()


def test_list_templates(auth_client):
    """Test GET /api/v1/checklist-templates."""
    # Create a template first
    auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-004",
            "name": "List Test Template",
            "description": "Template for list test",
            "items": [
                {
                    "item_key": "field1",
                    "label": "Field 1",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": True,
                }
            ]
        }
    )

    # List templates
    response = auth_client.get("/api/v1/checklist-templates")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(t["template_code"] == "ACC-004" for t in data["items"])


def test_publish_version(auth_client):
    """Test POST /api/v1/checklist-templates/{id}/versions."""
    # Create template first
    create_response = auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-005",
            "name": "Version Test Template",
            "description": "Template for version test",
            "items": [
                {
                    "item_key": "field1",
                    "label": "Field 1",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": True,
                }
            ]
        }
    )
    template_id = create_response.json()["id"]

    # Publish new version
    response = auth_client.post(
        f"/api/v1/checklist-templates/{template_id}/versions",
        json={
            "version_label": "v2.0",
            "items": [
                {
                    "item_key": "field1",
                    "label": "Field 1 Updated",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": True,
                },
                {
                    "item_key": "field2",
                    "label": "Field 2",
                    "item_type": "number",
                    "display_order": 2,
                    "is_required": False,
                },
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["version_number"] == 2
    assert data["version_label"] == "v2.0"
    assert data["status"] == "published"
    assert len(data["items"]) == 2


def test_retire_template(auth_client):
    """Test POST /api/v1/checklist-templates/{id}/retire."""
    # Create template first
    create_response = auth_client.post(
        "/api/v1/checklist-templates",
        json={
            "template_code": "ACC-006",
            "name": "Retire Test Template",
            "description": "Template for retire test",
            "items": [
                {
                    "item_key": "field1",
                    "label": "Field 1",
                    "item_type": "text",
                    "display_order": 1,
                    "is_required": True,
                }
            ]
        }
    )
    template_id = create_response.json()["id"]

    # Retire template
    response = auth_client.post(f"/api/v1/checklist-templates/{template_id}/retire")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "retired"


def test_template_unauthenticated(client):
    """Test template endpoints without authentication."""
    response = client.get("/api/v1/checklist-templates")

    # HTTPBearer returns 401 when no auth header is provided
    assert response.status_code == 401
