"""Unit tests for report service."""
import json
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.ingestion import GeneratedReport, IngestionRecord, IngestionRowResult, ValidationIssue
from app.models.storage import FileObject
from app.services.report_service import ReportService


def test_generate_result_report_success(db_session, admin_user):
    """Test generate result report success."""
    # Create file object for ingestion
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
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
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
        accepted_count=2,
        rejected_count=1,
        warning_count=0,
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create row results with validation issues
    row1 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=1,
        target_record_key="SITE-0001",
        mapped_payload_json=json.dumps({"site_id": "SITE-0001", "site_name": "Site 1"}),
        outcome="accepted",
    )
    db_session.add(row1)
    db_session.flush()

    row2 = IngestionRowResult(
        ingestion_id=ingestion.id,
        row_number=2,
        target_record_key="SITE-0002",
        mapped_payload_json=json.dumps({"site_id": "SITE-0002", "latitude": 95.0}),
        outcome="rejected",
    )
    db_session.add(row2)
    db_session.flush()

    # Add validation issue to rejected row
    issue = ValidationIssue(
        ingestion_id=ingestion.id,
        ingestion_row_result_id=row2.id,
        issue_scope="row",
        issue_code="LATITUDE_RANGE",
        severity="error",
        message="Invalid latitude",
        rule_code="LATITUDE_RANGE",
    )
    db_session.add(issue)
    db_session.commit()

    # Generate report
    service = ReportService(db_session)
    result = service.generate_result_report(ingestion.id, admin_user)

    assert result["report_type"] == "csv"
    assert "generated_at" in result
    assert "file_object_id" in result


def test_generate_result_report_ingestion_not_completed(db_session, admin_user):
    """Test generate report fails for non-completed ingestion."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create submitted ingestion (not completed)
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="submitted",
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Try to generate report
    service = ReportService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.generate_result_report(ingestion.id, admin_user)

    assert exc_info.value.status_code == 400
    assert "completed" in exc_info.value.detail


def test_generate_result_report_asp_access_denied(db_session, admin_user):
    """Test ASP user cannot generate report for another user's ingestion."""
    from app.models.auth import Role, User, UserRole

    # Create ASP user
    asp_role = Role(role_code="asp_user", display_name="ASP User")
    db_session.add(asp_role)
    db_session.flush()

    asp_user = User(
        subject_id="asp.test",
        display_name="ASP Test",
        email="asp@test.com",
        hashed_password="hash",
        is_active=True,
    )
    db_session.add(asp_user)
    db_session.flush()

    user_role = UserRole(
        user_id=asp_user.id,
        role_id=asp_role.id,
        assigned_by_user_id=admin_user.id,
    )
    db_session.add(user_role)
    db_session.flush()

    # Create file object and completed ingestion for admin
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # ASP user tries to generate report for admin's ingestion
    service = ReportService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.generate_result_report(ingestion.id, asp_user)

    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


def test_get_report_download_success(db_session, admin_user):
    """Test get report download URL success."""
    # Create file object for ingestion
    raw_file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(raw_file_obj)
    db_session.flush()

    # Create ingestion
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=raw_file_obj.id,
        status="completed",
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.flush()

    # Create report file object
    report_file_obj = FileObject(
        storage_bucket="ingestion-reports",
        storage_key="test/report.csv",
        original_filename="report.csv",
        content_type="text/csv",
        byte_size=512,
        sha256_hex="def456",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(report_file_obj)
    db_session.flush()

    # Create generated report
    generated_report = GeneratedReport(
        ingestion_id=ingestion.id,
        file_object_id=report_file_obj.id,
        report_type="csv",
        generated_at_utc=datetime.now(timezone.utc),
        generated_by_user_id=admin_user.id,
    )
    db_session.add(generated_report)
    db_session.commit()

    # Get download URL
    service = ReportService(db_session)
    result = service.get_report_download(ingestion.id, admin_user)

    assert "download_url" in result
    assert "expires_at" in result
    assert result["report_type"] == "csv"
    assert "generated_at" in result


def test_get_report_download_not_found(db_session, admin_user):
    """Test get report download for ingestion without report."""
    # Create file object
    file_obj = FileObject(
        storage_bucket="ingestion-raw-files",
        storage_key="test/file.xlsx",
        original_filename="test.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        byte_size=1024,
        sha256_hex="abc123",
        immutable_flag=True,
        created_by_user_id=admin_user.id,
    )
    db_session.add(file_obj)
    db_session.flush()

    # Create ingestion without report
    ingestion = IngestionRecord(
        mapping_version_id=1,
        validation_rule_set_id=1,
        raw_file_object_id=file_obj.id,
        status="completed",
        source_filename="test.xlsx",
        uploaded_by_user_id=admin_user.id,
        uploaded_at_utc=datetime.now(timezone.utc),
    )
    db_session.add(ingestion)
    db_session.commit()

    # Try to get download URL
    service = ReportService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.get_report_download(ingestion.id, admin_user)

    assert exc_info.value.status_code == 404
    assert "Report not found" in exc_info.value.detail
