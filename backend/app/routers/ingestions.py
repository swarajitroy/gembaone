"""Ingestion router."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_context import get_correlation_id, get_current_user
from app.models.auth import User
from app.schemas.ingestions import (
    IngestionDetailResponse,
    IngestionListResponse,
    IngestionResponse,
    IngestionRowResultResponse,
    IngestionRowResultsResponse,
    ValidationIssueResponse,
)
from app.schemas.reports import RawFileDownloadResponse, ReportDownloadResponse
from app.services.audit_service import AuditService
from app.services.ingestion_service import IngestionService
from app.services.permission_service import PermissionService
from app.services.raw_file_service import RawFileService
from app.services.report_service import ReportService

router = APIRouter(prefix="/ingestions", tags=["ingestions"])


async def get_request(request: Request) -> Request:
    """Get request for correlation ID."""
    return request


@router.post("", response_model=IngestionResponse)
def upload_ingestion(
    file: UploadFile = File(...),
    mapping_version_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = Depends(get_request),
):
    """Upload Excel file for ingestion.

    Accepts multipart form data with:
    - file: .xlsx file (binary)
    - mapping_version_id: UUID of mapping version to use

    Returns ingestion record with status=submitted.
    After successful upload, structural validation will be performed synchronously.
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_upload")

    # Get correlation ID
    correlation_id = get_correlation_id(request) or "unknown"

    # Create ingestion
    ingestion_service = IngestionService(db)
    result = ingestion_service.create_ingestion(
        file=file,
        mapping_version_id=mapping_version_id,
        user=user,
        correlation_id=correlation_id,
    )

    return IngestionResponse(
        id=result["id"],
        status=result["status"],
        uploaded_by=result["uploaded_by"],
        uploaded_at=result["uploaded_at"],
        source_filename=result["source_filename"],
        raw_file_object_id=result["raw_file_object_id"],
        mapping_version_id=mapping_version_id,
        validation_rule_set_id=1,  # Fixed for now
        accepted_count=0,
        rejected_count=0,
        warning_count=0,
    )


@router.get("", response_model=IngestionListResponse)
def list_ingestions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List ingestions with ASP visibility scoping.

    ASP users see only their own ingestions.
    Internal admins see all ingestions.
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_view")

    # List ingestions
    ingestion_service = IngestionService(db)
    items = ingestion_service.list_ingestions(user=user)

    return IngestionListResponse(
        items=[IngestionResponse(**item) for item in items],
        total=len(items),
    )


@router.get("/{id}", response_model=IngestionDetailResponse)
def get_ingestion(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ingestion detail with ASP visibility scoping.

    ASP users can only retrieve their own ingestions.
    Internal admins can retrieve any ingestion.
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_view")

    # Get ingestion
    ingestion_service = IngestionService(db)
    result = ingestion_service.get_ingestion(ingestion_id=id, user=user)

    if not result:
        raise HTTPException(status_code=404, detail="Ingestion not found")

    return IngestionDetailResponse(**result)


@router.get("/{id}/results", response_model=IngestionRowResultsResponse)
def get_ingestion_results(
    id: int,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get row-level results for an ingestion with pagination.

    Returns paginated row results with validation issues.
    Each row includes:
    - row_number: original row number from source file
    - outcome: accepted, rejected, or accepted_with_warning
    - target_record_key: optional business key from mapped data
    - issues: list of validation issues for rejected/warning rows

    Query parameters:
    - limit: maximum number of rows to return (default 50)
    - offset: number of rows to skip (default 0)
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_view")

    # Check ingestion visibility for ASP users
    ingestion_service = IngestionService(db)
    ingestion = ingestion_service.get_ingestion(ingestion_id=id, user=user)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")

    # Get row results
    from app.repositories.validation_repository import ValidationRepository

    validation_repo = ValidationRepository(db)
    row_results, total = validation_repo.get_row_results_by_ingestion_id(id, limit, offset)

    # Build response with issues
    items = []
    for row_result in row_results:
        # Get issues for this row
        issues = validation_repo.get_issues_by_row_result_id(row_result.id)

        items.append(
            IngestionRowResultResponse(
                row_number=row_result.row_number,
                outcome=row_result.outcome,
                target_record_key=row_result.target_record_key,
                issues=[
                    ValidationIssueResponse(
                        code=issue.issue_code,
                        severity=issue.severity,
                        message=issue.message,
                        rule_code=issue.rule_code,
                    )
                    for issue in issues
                ],
            )
        )

    return IngestionRowResultsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}/raw-file", response_model=RawFileDownloadResponse)
def get_raw_file_download(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = Depends(get_request),
):
    """Get signed download URL for raw uploaded file.

    Returns:
    - download_url: Signed URL for downloading the raw file
    - expires_at: ISO 8601 timestamp when the URL expires
    - original_filename: Original filename of the uploaded file
    - byte_size: Size of the file in bytes

    Permission: ASP users can only download their own files.
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_view")

    # Get raw file download link
    raw_file_service = RawFileService(db)
    result = raw_file_service.get_raw_file_download(ingestion_id=id, user=user)

    # Record audit event
    correlation_id = get_correlation_id(request) or "unknown"
    audit_service = AuditService(db)
    audit_service.record_event(
        event_type="raw_file_download",
        actor=user.id,
        entity_ref=("ingestion_record", str(id)),
        correlation_id=correlation_id,
        payload={"original_filename": result["original_filename"]},
    )

    return RawFileDownloadResponse(
        download_url=result["download_url"],
        expires_at=result["expires_at"],
        original_filename=result["original_filename"],
        byte_size=result["byte_size"],
    )


@router.get("/{id}/report", response_model=ReportDownloadResponse)
def get_report_download(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = Depends(get_request),
):
    """Get signed download URL for result report.

    Returns:
    - download_url: Signed URL for downloading the report
    - expires_at: ISO 8601 timestamp when the URL expires
    - report_type: Type of report (e.g., 'csv')
    - generated_at: ISO 8601 timestamp when the report was generated

    Permission: ASP users can only download their own reports.
    """
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "ingestion_view")

    # Get report download link
    report_service = ReportService(db)
    result = report_service.get_report_download(ingestion_id=id, user=user)

    # Record audit event
    correlation_id = get_correlation_id(request) or "unknown"
    audit_service = AuditService(db)
    audit_service.record_event(
        event_type="report_download",
        actor=user.id,
        entity_ref=("ingestion_record", str(id)),
        correlation_id=correlation_id,
        payload={"report_type": result["report_type"]},
    )

    return ReportDownloadResponse(
        download_url=result["download_url"],
        expires_at=result["expires_at"],
        report_type=result["report_type"],
        generated_at=result["generated_at"],
    )
