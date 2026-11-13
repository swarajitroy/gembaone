"""Acceptance tests for FR-004: Capture structured answers."""


def test_fr004_answers_stored_with_types(auth_client, db_session):
    """FR-004: Answers are stored per checklist item with defined data types."""
    # Use seeded template and instance
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    assert create_response.status_code == 200
    instance_id = create_response.json()["id"]

    # Get items
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]

    # Submit answers with different types
    answers = []
    for item in items:
        if item["item_key"] == "site_access":
            answers.append({
                "item_id": item["id"],
                "value_type": "text",
                "value_text": "Clear"
            })
        elif item["item_key"] == "site_photo":
            # Skip file type for now (handled by attachment upload)
            pass

    if answers:
        answer_response = auth_client.put(
            f"/api/v1/checklists/{instance_id}/answers",
            json={"answers": answers}
        )
        assert answer_response.status_code == 200

    # Verify answers were stored
    from app.models.checklist import ChecklistAnswer, ChecklistInstanceItem
    stored_answers = db_session.query(ChecklistAnswer).join(
        ChecklistInstanceItem,
        ChecklistAnswer.checklist_instance_item_id == ChecklistInstanceItem.id
    ).filter(ChecklistInstanceItem.checklist_instance_id == instance_id).all()

    assert len(stored_answers) > 0
    # Verify each answer has correct type
    for answer in stored_answers:
        assert answer.value_type in ["text", "number", "boolean", "date", "json"]
        if answer.value_type == "text":
            assert answer.value_text is not None


def test_fr004_malformed_values_rejected(auth_client, db_session):
    """FR-004: The platform rejects malformed values that do not match the item type."""
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get items
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    item_id = items[0]["id"]

    # Try to submit number answer without value_number (malformed)
    answer_response = auth_client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [{
                "item_id": item_id,
                "value_type": "number",
                "value_text": "123"  # Wrong: should be value_number
            }]
        }
    )

    # Should reject with 400
    assert answer_response.status_code == 400
    assert "requires" in answer_response.json()["detail"].lower()


def test_fr004_answers_retrievable(auth_client, db_session):
    """FR-004: Submitted answers can be retrieved in a structured response format."""
    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get items
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]

    site_access_item = next((item for item in items if item["item_key"] == "site_access"), None)
    assert site_access_item is not None

    # Submit answer
    answer_response = auth_client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [{
                "item_id": site_access_item["id"],
                "value_type": "text",
                "value_text": "Clear"
            }]
        }
    )
    assert answer_response.status_code == 200

    # Retrieve answers (via database query)
    from app.models.checklist import ChecklistAnswer
    answers = db_session.query(ChecklistAnswer).filter(
        ChecklistAnswer.checklist_instance_item_id == site_access_item["id"]
    ).all()

    assert len(answers) == 1
    assert answers[0].value_type == "text"
    assert answers[0].value_text == "Clear"


def test_fr004_responses_preserved_independently(auth_client, db_session):
    """FR-004: Structured responses are preserved independently of display formatting."""
    # This test verifies that answers are stored as structured data
    # and not as formatted strings

    from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion

    template = db_session.query(ChecklistTemplate).filter(
        ChecklistTemplate.template_code == "SITE_SURVEY_V1"
    ).first()

    version = db_session.query(ChecklistTemplateVersion).filter(
        ChecklistTemplateVersion.template_id == template.id,
        ChecklistTemplateVersion.status == "published"
    ).first()

    # Create instance
    create_response = auth_client.post(
        "/api/v1/checklists",
        json={"template_version_id": version.id}
    )
    instance_id = create_response.json()["id"]

    # Get items
    detail_response = auth_client.get(f"/api/v1/checklists/{instance_id}")
    items = detail_response.json()["items"]
    item_id = items[0]["id"]

    # Submit structured answer
    auth_client.put(
        f"/api/v1/checklists/{instance_id}/answers",
        json={
            "answers": [{
                "item_id": item_id,
                "value_type": "text",
                "value_text": "Structured Value"
            }]
        }
    )

    # Verify stored in structured columns, not as formatted string
    from app.models.checklist import ChecklistAnswer
    answer = db_session.query(ChecklistAnswer).filter(
        ChecklistAnswer.checklist_instance_item_id == item_id
    ).first()

    assert answer is not None
    assert answer.value_type == "text"
    assert answer.value_text == "Structured Value"
    # Verify separate columns exist (not a single formatted_value column)
    assert hasattr(answer, "value_text")
    assert hasattr(answer, "value_number")
    assert hasattr(answer, "value_boolean")
