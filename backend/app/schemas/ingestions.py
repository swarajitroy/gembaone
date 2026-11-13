"""Ingestion schemas."""

from pydantic import BaseModel


class IngestionResponse(BaseModel):
    """Ingestion response."""

    id: int
    status: str
    uploaded_by: int
    uploaded_at: str
    source_filename: str
    raw_file_object_id: int
    mapping_version_id: int
    validation_rule_set_id: int
    validation_started_at: str | None = None
    validation_completed_at: str | None = None
    accepted_count: int
    rejected_count: int
    warning_count: int
    failure_detail: str | None = None


class IngestionDetailResponse(BaseModel):
    """Ingestion detail response."""

    id: int
    status: str
    source_filename: str
    mapping_version_id: int
    validation_rule_set_id: int
    raw_file_object_id: int
    uploaded_by: int
    uploaded_at: str
    validation_started_at: str | None = None
    validation_completed_at: str | None = None
    accepted_count: int
    rejected_count: int
    warning_count: int
    failure_detail: str | None = None


class IngestionListResponse(BaseModel):
    """Ingestion list response."""

    items: list[IngestionResponse]
    total: int


class ValidationIssueResponse(BaseModel):
    """Validation issue response."""

    code: str
    severity: str
    message: str
    rule_code: str | None = None


class IngestionRowResultResponse(BaseModel):
    """Ingestion row result response."""

    row_number: int
    outcome: str
    target_record_key: str | None = None
    issues: list[ValidationIssueResponse]


class IngestionRowResultsResponse(BaseModel):
    """Ingestion row results response with pagination."""

    items: list[IngestionRowResultResponse]
    total: int
    limit: int
    offset: int
