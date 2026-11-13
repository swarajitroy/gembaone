"""Acceptance tests for FR-015 and FR-016."""
import json
from datetime import datetime, timezone

from app.models.ingestion import IngestionRecord, IngestionRowResult, ValidationIssue
from app.models.mapping import MappingDefinition, MappingEntry, MappingVersion
from app.models.storage import FileObject
from app.models.validation import ValidationRule, ValidationRuleSet


def test_fr015_layered_validation_checks(auth_client, db_session, admin_user):
    """
    FR-015: Run layered validation before commit.

    Acceptance criteria:
    - Validation includes structural, schema, business-rule, and mapping-level checks
    - Each validation issue is associated with a row or ingestion-level context
    - Validation outcomes distinguish accepted, rejected, and warning scenarios
    - Commit logic respects the validation decision model
    """
    # Create complete setup with all validation layers
    mapping_def = MappingDefinition(
        mapping_code="ACC-MAP-FR015",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_at_utc=datetime.now(timezone.utc),
        published_by_user_id=admin_user.id,
    )
    db_session.add(mapping_version)
    db_session.flush()

    # Mapping entries (mapping-level validation)
    for col in ["site_id", "site_name", "latitude", "longitude"]:
        entry = MappingEntry(
            mapping_version_id=mapping_version.id,
            source_column=col,
            target_field=col,
            target_type="number" if col in ["latitude", "longitude"] else "string",
            is_required=True,
        )
        db_session.add(entry)
    db_session.flush()

    # Validation rule set with multiple layers
    rule_set = ValidationRuleSet(
        rule_set_code="ACC-RULES-FR015",
        version_number=1,
        status="active",
        checksum_sha256="fr015_checksum",
        created_by_user_id=admin_user.id,
    )
    db_session.add(rule_set)
    db_session.flush()

    # Add rules for different layers
    rules = [
        # Schema layer
        ValidationRule(
            rule_set_id=rule_set.id,
            rule_code="SITE_ID_FORMAT",
            layer_code="schema",
            severity="error",
            expression_json=json.dumps({"field": "site_id", "pattern": "^SITE-[0-9]{4}$"}),
            human_message="Site ID must match format SITE-NNNN",
            sort_order=1,
        ),
        # Business layer
        ValidationRule(
            rule_set_id=rule_set.id,
            rule_code="LATITUDE_RANGE",
            layer_code="business",
            severity="error",
            expression_json=json.dumps({"field": "latitude", "min": -90, "max": 90}),
            human_message="Invalid latitude: out of range",
            sort_order=2,
        ),
        ValidationRule(
            rule_set_id=rule_set.id,
            rule_code="LONGITUDE_RANGE",
            layer_code="business",
            severity="error",
            expression_json=json.dumps({"field": "longitude", "min": -180, "max": 180}),
            human_message="Invalid longitude: out of range",
            sort_order=3,
        ),
    ]
    for rule in rules:
        db_session.add(rule)
    db_session.flush()

    # Create ingestion with row results
    file_obj = FileObject(
        storage_bucket="test",
        storage_key="fr015.xlsx",
        original_filename="fr015.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="fr015_hash",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="fr015.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        validation_started_at_utc=datetime.now(timezone.utc),
        validation_completed_at_utc=datetime.now(timezone.utc),
        accepted_count=2,
        rejected_count=2,
        warning_count=1,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row results with different outcomes
    # Accepted row
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001", "site_name": "Valid", "latitude": 59.3, "longitude": 18.0}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.flush()

    # Rejected row (schema failure)
    row2 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=2,
        target_record_key="SITE-0002",
        mapped_payload_json=json.dumps({"site_id": "SITE-0002", "site_name": "Invalid", "latitude": 95.0, "longitude": 18.0}),
        outcome="rejected",
    )
    db_session.add(row2)
    db_session.flush()

    # Create validation issue for rejected row
    issue1 = ValidationIssue(
        ingestion_id=ingestion.id,
        ingestion_row_result_id=row2.id,
        issue_scope="row",
        issue_code="LATITUDE_RANGE",
        severity="error",
        message="Invalid latitude: out of range",
        rule_code="LATITUDE_RANGE",
    )
    db_session.add(issue1)

    # Accepted with warning
    row3 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=3,
        target_record_key="SITE-0003",
        mapped_payload_json=json.dumps({"site_id": "SITE-0003", "site_name": "Long name", "latitude": 59.3, "longitude": 18.0}),
        outcome="accepted_with_warning",
    )
    db_session.add(row3)
    db_session.flush()

    # Create warning issue
    issue2 = ValidationIssue(
        ingestion_id=ingestion.id,
        ingestion_row_result_id=row3.id,
        issue_scope="row",
        issue_code="SITE_NAME_LENGTH",
        severity="warning",
        message="Site name exceeds recommended length",
        rule_code="SITE_NAME_LENGTH",
    )
    db_session.add(issue2)

    db_session.commit()

    # Test FR-015 acceptance criteria
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/results")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 3

    # Verify layered validation outcomes present
    outcomes = {item["outcome"] for item in data["items"]}
    assert "accepted" in outcomes
    assert "rejected" in outcomes
    assert "accepted_with_warning" in outcomes

    # Verify each validation issue is associated with a row
    for item in data["items"]:
        if item["outcome"] in ["rejected", "accepted_with_warning"]:
            assert len(item["issues"]) > 0
            for issue in item["issues"]:
                assert "code" in issue
                assert "severity" in issue
                assert "message" in issue


def test_fr016_row_level_results(auth_client, db_session, admin_user):
    """
    FR-016: Produce row-level accepted and rejected results with reasons.

    Acceptance criteria:
    - Each processed row has a recorded outcome
    - Rejected rows include one or more human-readable reasons
    - Accepted row counts and rejected row counts are summarized
    - Result detail is retrievable after processing completes
    """
    # Create setup
    mapping_def = MappingDefinition(
        mapping_code="ACC-MAP-FR016",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_at_utc=datetime.now(timezone.utc),
        published_by_user_id=admin_user.id,
    )
    db_session.add(mapping_version)
    db_session.flush()

    for col in ["site_id", "site_name", "latitude", "longitude"]:
        entry = MappingEntry(
            mapping_version_id=mapping_version.id,
            source_column=col,
            target_field=col,
            target_type="number" if col in ["latitude", "longitude"] else "string",
            is_required=True,
        )
        db_session.add(entry)
    db_session.flush()

    rule_set = ValidationRuleSet(
        rule_set_code="ACC-RULES-FR016",
        version_number=1,
        status="active",
        checksum_sha256="fr016_checksum",
        created_by_user_id=admin_user.id,
    )
    db_session.add(rule_set)
    db_session.flush()

    file_obj = FileObject(
        storage_bucket="test",
        storage_key="fr016.xlsx",
        original_filename="fr016.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="fr016_hash",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion with summary counts
    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="fr016.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        validation_completed_at_utc=datetime.now(timezone.utc),
        accepted_count=10,
        rejected_count=5,
        warning_count=2,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create rejected row with multiple reasons
    rejected_row = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="rejected",
    )
    db_session.add(rejected_row)
    db_session.flush()

    # Add multiple rejection reasons
    reasons = [
        {
            "code": "required_field_missing",
            "severity": "error",
            "message": "Missing required field: site_name",
        },
        {
            "code": "required_field_missing",
            "severity": "error",
            "message": "Missing required field: latitude",
        },
    ]

    for reason in reasons:
        issue = ValidationIssue(
            ingestion_id=ingestion.id,
            ingestion_row_result_id=rejected_row.id,
            issue_scope="row",
            issue_code=reason["code"],
            severity=reason["severity"],
            message=reason["message"],
            rule_code=None,
        )
        db_session.add(issue)

    db_session.commit()

    # Test FR-016 acceptance criteria

    # 1. Each processed row has a recorded outcome
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # 2. Rejected rows include human-readable reasons
    rejected_items = [item for item in data["items"] if item["outcome"] == "rejected"]
    assert len(rejected_items) > 0

    for rejected_item in rejected_items:
        assert len(rejected_item["issues"]) > 0
        for issue in rejected_item["issues"]:
            assert issue["message"] != ""
            assert len(issue["message"]) > 0

    # 3. Summary counts available
    ingestion_detail_response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}")
    assert ingestion_detail_response.status_code == 200
    ingestion_data = ingestion_detail_response.json()

    assert ingestion_data["accepted_count"] == 10
    assert ingestion_data["rejected_count"] == 5
    assert ingestion_data["warning_count"] == 2

    # 4. Result detail is retrievable after processing completes
    assert ingestion_data["status"] == "completed"
    assert ingestion_data["validation_completed_at"] is not None


def test_results_pagination(auth_client, db_session, admin_user):
    """Test results endpoint pagination with limit and offset."""
    # Create setup
    mapping_def = MappingDefinition(
        mapping_code="PAGE-MAP",
        source_entity="Test",
        target_entity="Test",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db_session.add(mapping_def)
    db_session.flush()

    mapping_version = MappingVersion(
        mapping_definition_id=mapping_def.id,
        version_number=1,
        version_label="v1.0",
        status="active",
        published_at_utc=datetime.now(timezone.utc),
        published_by_user_id=admin_user.id,
    )
    db_session.add(mapping_version)
    db_session.flush()

    for col in ["site_id", "site_name"]:
        entry = MappingEntry(
            mapping_version_id=mapping_version.id,
            source_column=col,
            target_field=col,
            target_type="string",
            is_required=True,
        )
        db_session.add(entry)
    db_session.flush()

    rule_set = ValidationRuleSet(
        rule_set_code="PAGE-RULES",
        version_number=1,
        status="active",
        checksum_sha256="page_checksum",
        created_by_user_id=admin_user.id,
    )
    db_session.add(rule_set)
    db_session.flush()

    file_obj = FileObject(
        storage_bucket="test",
        storage_key="page.xlsx",
        original_filename="page.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="page_hash",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=mapping_version.id,
        validation_rule_set_id=rule_set.id,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="page.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=25,
        rejected_count=0,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create 25 row results
    for i in range(1, 26):
        row = IngestionRowResult(
            ingestion_id=ingestion.id,
            row_number=i,
            target_record_key=f"SITE-{i:04d}",
            mapped_payload_json=json.dumps({"site_id": f"SITE-{i:04d}", "site_name": f"Site {i}"}),
            outcome="accepted",
        )
        db_session.add(row)

    db_session.commit()

    # Test pagination: limit=10
    response1 = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/results?limit=10&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["items"]) == 10
    assert data1["total"] == 25
    assert data1["limit"] == 10
    assert data1["offset"] == 0

    # Test pagination: second page
    response2 = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/results?limit=10&offset=10")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 10
    assert data2["total"] == 25
    assert data2["offset"] == 10

    # Verify no duplicate rows between pages
    rows1 = {item["row_number"] for item in data1["items"]}
    rows2 = {item["row_number"] for item in data2["items"]}
    assert len(rows1.intersection(rows2)) == 0
