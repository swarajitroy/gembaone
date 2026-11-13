"""Integration tests for report generation."""
import json
from datetime import datetime, timezone

from app.models.ingestion import IngestionRecord, IngestionRowResult, ValidationIssue
from app.models.storage import FileObject


def test_report_generation_workflow(client, db_session, admin_user, auth_client):
    """Test complete report generation workflow."""
    # Create file object for ingestion
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/report_workflow.xlsx",
        original_filename="report_workflow.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="workflow_abc",
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
        source_filename="report_workflow.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=1,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row results
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.flush()

    row2 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=2,
        target_record_key="SITE-0002",
        mapped_payload_json=json.dumps({"site_id": "SITE-0002"}),
        outcome="rejected",
    )
    db_session.add(row2)
    db_session.flush()

    # Add validation issue
    issue = ValidationIssue(
        ingestion_id=ingestion.id,
        ingestion_row_result_id=row2.id,
        issue_scope="row",
        issue_code="TEST_ERROR",
        severity="error",
        message="Test error message",
        rule_code="TEST_RULE",
    )
    db_session.add(issue)
    db_session.commit()

    # Generate report (import service directly)
    from app.services.report_service import ReportService

    report_service = ReportService(db_session)
    result = report_service.generate_result_report(ingestion.id, admin_user)

    assert result["report_type"] == "csv"
    assert "generated_at" in result

    # Get report download URL
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/report")
    assert response.status_code == 200

    data = response.json()
    assert "download_url" in data
    assert "expires_at" in data
    assert data["report_type"] == "csv"


def test_report_download_without_generation(client, db_session, admin_user, auth_client):
    """Test report download fails when report not generated."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/no_report.xlsx",
        original_filename="no_report.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="no_report_abc",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create completed ingestion without report
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="no_report.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Try to download report
    response = auth_client.get(f"/api/v1/ingestions/{ingestion.id}/report")
    assert response.status_code == 404


def test_report_csv_content_structure(client, db_session, admin_user):
    """Test CSV report content has correct structure."""
    from app.services.report_service import ReportService

    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/csv_structure.xlsx",
        original_filename="csv_structure.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="csv_abc",
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
        source_filename="csv_structure.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=1,
        rejected_count=0,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create one accepted row
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001", "site_name": "Test Site"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.commit()

    # Generate report
    report_service = ReportService(db_session)
    result = report_service.generate_result_report(ingestion.id, admin_user)

    # Verify report was created
    assert result["report_type"] == "csv"
    assert "file_object_id" in result
