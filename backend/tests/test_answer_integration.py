"""Integration tests for answer upsert with visibility re-evaluation."""
import json

from app.models.auth import Role, User, UserRole
from app.models.checklist import (
    ChecklistItemCondition,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.seed import hash_password


def test_answer_upsert_with_visibility_reevaluation(client, db_session):
    """Test complete answer upsert flow with conditional visibility re-evaluation."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.engineer",
        display_name="Test Engineer",
        email="test.engineer@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.engineer@example.com", "password": "test123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create template with conditional logic
    template = ChecklistTemplate(
        template_code="TEST_TEMPLATE",
        name="Test Template",
        description="Test",
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

    # Create source item
    source_item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="access_status",
        label="Access Status",
        item_type="select",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
        options_json=json.dumps({"choices": ["Clear", "Obstructed"]}),
    )
    db_session.add(source_item)
    db_session.flush()

    # Create conditional item
    conditional_item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="obstruction_notes",
        label="Obstruction Notes",
        item_type="text",
        display_order=2,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(conditional_item)
    db_session.flush()

    # Create condition
    condition = ChecklistItemCondition(
        template_item_id=conditional_item.id,
        source_item_key="access_status",
        operator="equals",
        expected_value="Obstructed",
    )
    db_session.add(condition)
    db_session.commit()

    # Create checklist instance
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id, "title": "Test Instance"}
    )
    assert create_response.status_code == 200
    instance_id = create_response.json()["id"]

    # Get instance items
    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    assert detail_response.status_code == 200
    items = detail_response.json()["items"]

    source_item_id = next(item["id"] for item in items if item["item_key"] == "access_status")
    _conditional_item_id = next(item["id"] for item in items if item["item_key"] == "obstruction_notes")

    # Answer source item with "Obstructed" (should make conditional item visible)
    answer_response = client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [
                {
                    "item_id": source_item_id,
                    "value_type": "text",
                    "value_text": "Obstructed"
                }
            ]
        }
    )
    assert answer_response.status_code == 200

    # Verify visibility trace
    response_data = answer_response.json()
    assert response_data["visibility_trace_json"] is not None

    visibility_trace = json.loads(response_data["visibility_trace_json"])
    assert visibility_trace["access_status"]["visible"] is True
    assert visibility_trace["obstruction_notes"]["visible"] is True
    assert visibility_trace["obstruction_notes"]["required"] is True

    # Change answer to "Clear" (should hide conditional item)
    answer_response2 = client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [
                {
                    "item_id": source_item_id,
                    "value_type": "text",
                    "value_text": "Clear"
                }
            ]
        }
    )
    assert answer_response2.status_code == 200

    # Verify conditional item is now hidden
    visibility_trace2 = json.loads(answer_response2.json()["visibility_trace_json"])
    assert visibility_trace2["obstruction_notes"]["visible"] is False
    assert visibility_trace2["obstruction_notes"]["required"] is False


def test_answer_type_validation(client, db_session):
    """Test that answer values must match declared type."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.engineer2",
        display_name="Test Engineer 2",
        email="test.engineer2@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.engineer2@example.com", "password": "test123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create simple template
    template = ChecklistTemplate(
        template_code="TYPE_TEST",
        name="Type Test Template",
        description="Test",
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

    item = ChecklistTemplateItem(
        template_version_id=version.id,
        item_key="test_number",
        label="Test Number",
        item_type="number",
        display_order=1,
        is_required=True,
        evidence_required=False,
        location_mode="none",
    )
    db_session.add(item)
    db_session.commit()

    # Create instance
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    assert create_response.status_code == 200
    instance_id = create_response.json()["id"]

    # Get item ID
    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    item_id = items[0]["id"]

    # Try to submit answer with wrong type (number answer requires value_number)
    answer_response = client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [
                {
                    "item_id": item_id,
                    "value_type": "number",
                    "value_text": "123"  # Wrong: should be value_number
                }
            ]
        }
    )
    assert answer_response.status_code == 400
    assert "requires value_number" in answer_response.json()["detail"]


def test_answer_upsert_updates_existing(client, db_session):
    """Test that upsert updates existing answer instead of creating duplicate."""
    # Create role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_code == "field_engineer").first()
    if not role:
        role = Role(role_code="field_engineer", display_name="Field Engineer")
        db_session.add(role)
        db_session.flush()

    user = User(
        subject_id="test.engineer3",
        display_name="Test Engineer 3",
        email="test.engineer3@example.com",
        hashed_password=hash_password("test123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id)
    db_session.add(user_role)
    db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.engineer3@example.com", "password": "test123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Create simple template
    template = ChecklistTemplate(
        template_code="UPSERT_TEST",
        name="Upsert Test Template",
        description="Test",
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
    create_response = client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get item ID
    detail_response = client.get(f"/api/v1/checklists/{instance_id}")
    item_id = detail_response.json()["items"][0]["id"]

    # Submit initial answer
    client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [
                {"item_id": item_id, "value_type": "text", "value_text": "Initial value"}
            ]
        }
    )

    # Submit updated answer
    client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [
                {"item_id": item_id, "value_type": "text", "value_text": "Updated value"}
            ]
        }
    )

    # Verify only one answer exists (upsert, not duplicate)
    from app.models.checklist import ChecklistAnswer
    answers = db_session.query(ChecklistAnswer).filter(
        ChecklistAnswer.checklist_instance_item_id == item_id
    ).all()

    assert len(answers) == 1
    assert answers[0].value_text == "Updated value"
