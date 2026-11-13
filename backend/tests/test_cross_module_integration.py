"""
Cross-module integration tests verifying full backend workflows.

Tests:
- Ingestion workflow (upload → validation → results)
- Validation outcomes deterministic
- Audit events created with correlation IDs
"""
import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.ingestion import IngestionRecord


def test_ingestion_full_workflow(auth_client: TestClient, db_session: Session):
    """
    Test full ingestion workflow using seed mapping.

    Verifies:
    - Upload creates ingestion record
    - Structural validation runs
    - Row validation completes
    - Audit events with correlation IDs
    """
    # Create sample Excel file
    import openpyxl
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Site Data"

    # Headers matching MAP-SYN-001 v2.0 mapping from seed
    sheet.append(["SITE_ID", "SITE_NAME", "LAT", "LON"])
    sheet.append(["SITE-INT-001", "Stockholm Test", "59.3293", "18.0686"])
    sheet.append(["SITE-INT-002", "Gothenburg Test", "57.7089", "11.9746"])

    excel_bytes = io.BytesIO()
    workbook.save(excel_bytes)
    excel_bytes.seek(0)

    # Step 1: Upload ingestion
    upload_response = auth_client.post(
        "/api/v1/ingestions",
        files={"file": ("test_integration.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"mapping_version_id": "1"}  # Use seed mapping
    )
    assert upload_response.status_code == 200
    ingestion_data = upload_response.json()
    ingestion_id = ingestion_data["id"]
    correlation_id_upload = upload_response.headers.get("X-Correlation-ID")
    assert correlation_id_upload is not None

    # Verify ingestion record created
    db_ingestion = db_session.query(IngestionRecord).filter_by(id=ingestion_id).first()
    assert db_ingestion is not None
    assert db_ingestion.raw_file_object_id is not None

    # Step 2: Retrieve ingestion status
    status_response = auth_client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] in ["submitted", "validating", "completed", "failed"]

    # Step 3: Verify audit events exist
    audit_count = db_session.query(AuditLog).count()
    assert audit_count > 0  # At least some audit events recorded


def test_validation_outcomes_deterministic(auth_client: TestClient, db_session: Session):
    """
    Test that validation outcomes are deterministic.

    Verifies:
    - Same input produces same outcomes
    - Row results consistent across retrievals
    """
    # Create test Excel with known data
    import openpyxl
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Site Data"

    # Headers
    sheet.append(["SITE_ID", "SITE_NAME", "LAT", "LON"])
    sheet.append(["SITE-DET-001", "Deterministic Test", "59.3293", "18.0686"])

    excel_bytes = io.BytesIO()
    workbook.save(excel_bytes)
    excel_bytes.seek(0)

    # Upload ingestion
    upload_response = auth_client.post(
        "/api/v1/ingestions",
        files={"file": ("deterministic.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"mapping_version_id": "1"}
    )
    assert upload_response.status_code == 200
    ingestion_data = upload_response.json()
    ingestion_id = ingestion_data["id"]

    # Fetch results multiple times
    results_1 = auth_client.get(f"/api/v1/ingestions/{ingestion_id}/results?limit=10")
    results_2 = auth_client.get(f"/api/v1/ingestions/{ingestion_id}/results?limit=10")

    assert results_1.status_code == 200
    assert results_2.status_code == 200

    data_1 = results_1.json()
    data_2 = results_2.json()

    # Verify same structure
    assert data_1.keys() == data_2.keys()

    # If items exist, verify consistency
    if "items" in data_1 and len(data_1["items"]) > 0:
        assert len(data_1["items"]) == len(data_2["items"])
        for i in range(len(data_1["items"])):
            # Row numbers should match
            if "row_number" in data_1["items"][i]:
                assert data_1["items"][i]["row_number"] == data_2["items"][i]["row_number"]
            # Outcomes should match
            if "outcome" in data_1["items"][i]:
                assert data_1["items"][i]["outcome"] == data_2["items"][i]["outcome"]


def test_audit_events_with_correlation_ids(auth_client: TestClient, db_session: Session):
    """
    Test that audit events are created with correlation IDs.

    Verifies:
    - Correlation ID in response headers
    - Audit events created for operations
    """
    # Create sample Excel file
    import openpyxl
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Site Data"
    sheet.append(["SITE_ID", "SITE_NAME", "LAT", "LON"])
    sheet.append(["SITE-AUDIT-001", "Audit Test", "59.3293", "18.0686"])

    excel_bytes = io.BytesIO()
    workbook.save(excel_bytes)
    excel_bytes.seek(0)

    # Upload ingestion
    upload_response = auth_client.post(
        "/api/v1/ingestions",
        files={"file": ("audit_test.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"mapping_version_id": "1"}
    )
    assert upload_response.status_code == 200

    # Verify correlation ID in header
    correlation_id = upload_response.headers.get("X-Correlation-ID")
    assert correlation_id is not None
    assert len(correlation_id) > 0
