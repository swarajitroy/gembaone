"""Checklist instance router."""
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_context import get_correlation_id, get_current_user
from app.models.auth import User
from app.schemas.checklists import (
    AttachmentResponse,
    CaptureLocationRequest,
    ChecklistDetailResponse,
    ChecklistInstanceResponse,
    ChecklistListItem,
    ChecklistListResponse,
    ChecklistSubmissionResponse,
    CreateChecklistRequest,
    LocationResponse,
    SubmissionValidationIssue,
    UpsertAnswersRequest,
)
from app.services.checklist_execution_service import ChecklistExecutionService
from app.services.checklist_review_service import ChecklistReviewService
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("", response_model=ChecklistListResponse)
def list_checklists(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List checklist instances.

    Returns a paginated list of checklist instances accessible to the current user.
    """
    from app.models.checklist import ChecklistInstance

    query = db.query(ChecklistInstance).order_by(ChecklistInstance.created_at_utc.desc())
    
    total = query.count()
    instances = query.offset(offset).limit(limit).all()
    
    items = [
        ChecklistListItem(
            id=instance.id,
            title=instance.title,
            status=instance.status,
            template_version_id=instance.template_version_id,
            created_by_user_id=instance.created_by_user_id,
            created_at_utc=instance.created_at_utc.isoformat(),
            submitted_by_user_id=instance.submitted_by_user_id,
            submitted_at_utc=instance.submitted_at_utc.isoformat() if instance.submitted_at_utc else None,
        )
        for instance in instances
    ]
    
    return ChecklistListResponse(items=items, total=total)


@router.post("", response_model=ChecklistInstanceResponse)
def create_checklist(
    request_data: CreateChecklistRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create checklist instance from template version.

    Creates a new checklist instance from an active (published) template version.
    The instance captures a snapshot of the template structure and starts in draft status.
    """
    correlation_id = get_correlation_id(request)
    service = ChecklistExecutionService(db)

    instance_id = service.create_instance(
        template_version_id=request_data.template_version_id,
        title=request_data.title,
        user=user,
        correlation_id=correlation_id,
    )

    # Retrieve created instance for response
    review_service = ChecklistReviewService(db)
    detail = review_service.get_checklist_detail(instance_id)

    return detail.instance


@router.get("/{id}", response_model=ChecklistDetailResponse)
def get_checklist_detail(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve checklist instance with full context.

    Returns the checklist instance, all items, captured locations, and template version metadata.
    """
    service = ChecklistReviewService(db)
    return service.get_checklist_detail(id)


@router.put("/{id}/answers", response_model=ChecklistInstanceResponse)
def upsert_answers(
    id: int,
    request_data: UpsertAnswersRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upsert answers for checklist instance.

    Updates or creates answers for checklist items and re-evaluates conditional visibility.
    Returns the updated instance with visibility_trace_json.
    """
    correlation_id = get_correlation_id(request)
    service = ChecklistExecutionService(db)

    # Convert Pydantic models to dicts for service layer
    answers_list = [answer.model_dump() for answer in request_data.answers]

    instance = service.upsert_answers(
        instance_id=id,
        answers=answers_list,
        user=user,
        correlation_id=correlation_id,
    )

    return ChecklistInstanceResponse(
        id=instance.id,
        template_version_id=instance.template_version_id,
        title=instance.title,
        status=instance.status,
        visibility_trace_json=instance.visibility_trace_json,
        created_by_user_id=instance.created_by_user_id,
        created_at_utc=instance.created_at_utc.isoformat(),
        submitted_by_user_id=instance.submitted_by_user_id,
        submitted_at_utc=instance.submitted_at_utc.isoformat() if instance.submitted_at_utc else None,
    )


@router.post("/{id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    id: int,
    item_id: int = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload attachment for checklist item.

    Uploads a file (photo or document) and links it to a checklist item.
    Validates file type and size before storage.
    """
    service = EvidenceService(db)

    attachment_data = service.upload_attachment(
        checklist_instance_id=id,
        checklist_instance_item_id=item_id,
        file=file,
        user=user,
    )

    return AttachmentResponse(**attachment_data)


@router.put("/{id}/location", response_model=LocationResponse)
def capture_instance_location(
    id: int,
    request_data: CaptureLocationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Capture instance-level location.

    Records geo-location for the entire checklist instance.
    Latitude must be between -90 and 90, longitude between -180 and 180.
    """
    correlation_id = get_correlation_id(request)
    service = ChecklistExecutionService(db)

    location_id = service.capture_instance_location(
        instance_id=id,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        accuracy_meters=request_data.accuracy_meters,
        user=user,
        correlation_id=correlation_id,
    )

    # Retrieve created location for response
    review_service = ChecklistReviewService(db)
    detail = review_service.get_checklist_detail(id)

    # Find the location we just created
    for loc in detail.locations:
        if loc.id == location_id:
            return loc

    # Fallback (should not happen)
    from app.repositories.checklist_repository import ChecklistRepository
    repo = ChecklistRepository(db)
    locations = repo.get_locations_by_instance(id)
    matching = [loc for loc in locations if loc.id == location_id]
    if matching:
        return LocationResponse(
            id=matching[0].id,
            checklist_instance_id=matching[0].checklist_instance_id,
            checklist_instance_item_id=matching[0].checklist_instance_item_id,
            latitude=matching[0].latitude,
            longitude=matching[0].longitude,
            accuracy_meters=matching[0].accuracy_meters,
            captured_by_user_id=matching[0].captured_by_user_id,
            captured_at_utc=matching[0].captured_at_utc.isoformat(),
        )


@router.post("/{id}/submit", response_model=ChecklistSubmissionResponse)
def submit_checklist(
    id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit checklist instance for review.

    Validates that all visible required items are answered and required evidence is attached.
    If validation fails, returns validation issues with readable guidance.
    If validation succeeds, transitions instance to submitted status and makes it read-only.
    """
    correlation_id = get_correlation_id(request)
    service = ChecklistExecutionService(db)

    result = service.submit_checklist(
        instance_id=id,
        user=user,
        correlation_id=correlation_id,
    )

    # Convert to response model
    issues = [SubmissionValidationIssue(**issue) for issue in result["validation_issues"]]

    # If validation failed, return 400 with issues
    if issues:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Checklist validation failed. Please address the issues before submitting.",
                "validation_issues": [issue.model_dump() for issue in issues]
            }
        )

    return ChecklistSubmissionResponse(
        status=result["status"],
        submitted_by=result["submitted_by"],
        submitted_at=result["submitted_at"],
        validation_issues=issues,
    )


@router.put("/{id}/items/{itemId}/location", response_model=LocationResponse)
def capture_item_location(
    id: int,
    itemId: int,
    request_data: CaptureLocationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Capture item-level location.

    Records geo-location for a specific checklist item.
    Latitude must be between -90 and 90, longitude between -180 and 180.
    """
    correlation_id = get_correlation_id(request)
    service = ChecklistExecutionService(db)

    location_id = service.capture_item_location(
        instance_id=id,
        item_id=itemId,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        accuracy_meters=request_data.accuracy_meters,
        user=user,
        correlation_id=correlation_id,
    )

    # Retrieve created location for response
    review_service = ChecklistReviewService(db)
    detail = review_service.get_checklist_detail(id)

    # Find the location we just created
    for loc in detail.locations:
        if loc.id == location_id:
            return loc

    # Fallback (should not happen)
    from app.repositories.checklist_repository import ChecklistRepository
    repo = ChecklistRepository(db)
    locations = repo.get_locations_by_instance(id)
    matching = [loc for loc in locations if loc.id == location_id]
    if matching:
        return LocationResponse(
            id=matching[0].id,
            checklist_instance_id=matching[0].checklist_instance_id,
            checklist_instance_item_id=matching[0].checklist_instance_item_id,
            latitude=matching[0].latitude,
            longitude=matching[0].longitude,
            accuracy_meters=matching[0].accuracy_meters,
            captured_by_user_id=matching[0].captured_by_user_id,
            captured_at_utc=matching[0].captured_at_utc.isoformat(),
        )
