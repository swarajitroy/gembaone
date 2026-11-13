"""Acceptance tests for report download - FR-020."""
import json
from datetime import datetime, timezone

from app.models.auth import User
from app.models.ingestion import GeneratedReport, IngestionRecord, IngestionRowResult, ValidationIssue
from app.models.storage import FileObject


def test_fr020_completed_ingestion_has_downloadable_report(client, db_session, admin_user, auth_client):
    """FR-020: A completed ingestion exposes a downloadable report for authorized users."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/completed_report.xlsx",
        original_filename="completed_report.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="completed_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create completed ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="completed_report.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=0,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row result
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.commit()

    # Generate report
    from app.services.report_service import ReportService

    report_service = ReportService(db_session)
    result = report_service.generate_result_report(ingestion.id, admin_user)

    assert result["report_type"] == "csv"

    # Download report
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/report")
    assert response.status_code == 200

    data = response.json()
    assert "download_url" in data
    assert data["report_type"] == "csv"


def test_fr020_report_contains_outcome_and_reasons(client, db_session, admin_user):
    """FR-020: The report contains accepted/rejected outcomes and reasons at the necessary level of detail."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/outcome_report.xlsx",
        original_filename="outcome_report.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="outcome_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create completed ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="outcome_report.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=1,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create accepted row
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.flush()

    # Create rejected row with validation issue
    row2 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=2,
        target_record_key="SITE-0002",
        mapped_payload_json=json.dumps({"site_id": "SITE-0002"}),
        outcome="rejected",
    )
    db_session.add(row2)
    db_session.flush()

    issue = ValidationIssue(
        ingestion_id=ingestion.id,
        ingestion_row_result_id=row2.id,
        issue_scope="row",
        issue_code="LATITUDE_RANGE",
        severity="error",
        message="Invalid latitude value",
        rule_code="LATITUDE_RANGE",
    )
    db_session.add(issue)
    db_session.commit()

    # Generate report
    from app.services.report_service import ReportService

    report_service = ReportService(db_session)
    result = report_service.generate_result_report(ingestion.id, admin_user)

    # Verify report was created with outcomes
    assert result["report_type"] == "csv"


def test_fr020_report_corresponds_to_ingestion(client, db_session, admin_user, auth_client):
    """FR-020: Report content corresponds to the ingestion record viewed."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/corresponds.xlsx",
        original_filename="corresponds.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="corresponds_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create completed ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="corresponds.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=0,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row result
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.commit()

    # Generate report
    from app.services.report_service import ReportService

    report_service = ReportService(db_session)
    _result = report_service.generate_result_report(ingestion.id, admin_user)

    # Verify report is linked to correct ingestion
    generated_report = db_session.query(GeneratedReport).filter(
        GeneratedReport.ingestion_id == ingestion.id
    ).first()

    assert generated_report is not None
    assert generated_report.ingestion_id == ingestion.id


def test_fr020_downloads_are_auditable(client, db_session, admin_user, auth_client):
    """FR-020: Downloads are auditable."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/auditable.xlsx",
        original_filename="auditable.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="auditable_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create completed ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="auditable.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=0,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row result
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.commit()

    # Generate report
    from app.services.report_service import ReportService

    report_service = ReportService(db_session)
    _result = report_service.generate_result_report(ingestion.id, admin_user)

    # Download report (creates audit event)
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/report")
    assert response.status_code == 200

    # Verify audit log entry was created
    from app.models.audit import AuditLog

    # Get the auth user (admin@example.com)
    auth_user = db_session.query(User).filter(User.email == "admin@example.com").first()

    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.event_type == "report_download",
        AuditLog.entity_type == "ingestion_record",
        AuditLog.entity_id == str(ingestion.id),
    ).first()

    assert audit_entry is not None
    assert audit_entry.actor_user_id == auth_user.id
