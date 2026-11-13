"""Checklist instance schemas."""
from pydantic import BaseModel, Field


class CreateChecklistRequest(BaseModel):
    """Create checklist instance request."""
    template_version_id: int
    title: str | None = None


class AnswerRequest(BaseModel):
    """Single answer request."""
    item_id: int
    value_type: str  # text, number, boolean, date, json
    value_text: str | None = None
    value_number: float | None = None
    value_boolean: bool | None = None
    value_date: str | None = None  # ISO 8601
    value_json: str | None = None


class UpsertAnswersRequest(BaseModel):
    """Upsert answers request."""
    answers: list[AnswerRequest]


class CaptureLocationRequest(BaseModel):
    """Capture location request."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_meters: float | None = Field(None, ge=0)


class LocationResponse(BaseModel):
    """Location response."""
    id: int
    checklist_instance_id: int
    checklist_instance_item_id: int | None
    latitude: float
    longitude: float
    accuracy_meters: float | None
    captured_by_user_id: int
    captured_at_utc: str

    class Config:
        from_attributes = True


class ChecklistInstanceItemResponse(BaseModel):
    """Checklist instance item response."""
    id: int
    checklist_instance_id: int
    template_item_id: int
    item_key: str
    label: str
    item_type: str
    display_order: int
    is_required: bool
    evidence_required: bool
    location_mode: str
    condition_snapshot_json: str | None

    class Config:
        from_attributes = True


class ChecklistInstanceResponse(BaseModel):
    """Checklist instance response."""
    id: int
    template_version_id: int
    title: str | None
    status: str
    visibility_trace_json: str | None
    created_by_user_id: int
    created_at_utc: str
    submitted_by_user_id: int | None
    submitted_at_utc: str | None

    class Config:
        from_attributes = True


class TemplateVersionMetadata(BaseModel):
    """Template version metadata for detail response."""
    id: int
    template_id: int
    version_number: int
    version_label: str
    status: str


class ChecklistDetailResponse(BaseModel):
    """Checklist detail response with full context."""
    instance: ChecklistInstanceResponse
    items: list[ChecklistInstanceItemResponse]
    locations: list[LocationResponse]
    template_version: TemplateVersionMetadata


class AttachmentResponse(BaseModel):
    """Attachment response."""
    id: int
    file_object_id: int
    original_filename: str
    content_type: str
    byte_size: int
    sha256_hex: str
    uploaded_by_user_id: int
    uploaded_at_utc: str


class SubmissionValidationIssue(BaseModel):
    """Submission validation issue."""
    item_id: int | None
    code: str
    message: str
    severity: str


class ChecklistSubmissionResponse(BaseModel):
    """Checklist submission response."""
    status: str
    submitted_by: int | None
    submitted_at: str | None
    validation_issues: list[SubmissionValidationIssue]


class ChecklistListItem(BaseModel):
    """Checklist list item response."""
    id: int
    title: str | None
    status: str
    template_version_id: int
    created_by_user_id: int
    created_at_utc: str
    submitted_by_user_id: int | None
    submitted_at_utc: str | None

    class Config:
        from_attributes = True


class ChecklistListResponse(BaseModel):
    """Checklist list response."""
    items: list[ChecklistListItem]
    total: int
