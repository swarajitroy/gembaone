"""Mapping schemas for request/response."""
from datetime import datetime

from pydantic import BaseModel, Field


class MappingEntryRequest(BaseModel):
    """Mapping entry request."""

    source_column: str = Field(..., description="Source column name from workbook")
    target_field: str = Field(..., description="Target field name in system")
    target_type: str = Field(..., description="Target data type (string, number, date, boolean)")
    is_required: bool = Field(..., description="Whether this field is required")
    transform_expression: str | None = Field(None, description="Optional transform expression")


class MappingEntryResponse(BaseModel):
    """Mapping entry response."""

    id: int
    mapping_version_id: int
    source_column: str
    target_field: str
    target_type: str
    is_required: bool
    transform_expression: str | None
    created_at_utc: datetime

    class Config:
        from_attributes = True


class CreateMappingRequest(BaseModel):
    """Create mapping definition request."""

    mapping_code: str = Field(..., description="Unique mapping code")
    source_entity: str = Field(..., description="Source entity description")
    target_entity: str = Field(..., description="Target entity name")
    entries: list[MappingEntryRequest] = Field(..., description="Initial mapping entries")


class PublishMappingVersionRequest(BaseModel):
    """Publish new mapping version request."""

    version_label: str = Field(..., description="Version label (e.g., v2.0)")
    entries: list[MappingEntryRequest] = Field(..., description="Mapping entries for this version")


class MappingVersionResponse(BaseModel):
    """Mapping version response."""

    id: int
    mapping_definition_id: int
    version_number: int
    version_label: str
    status: str
    published_at_utc: datetime | None
    published_by_user_id: int | None
    created_at_utc: datetime
    entries: list[MappingEntryResponse]

    class Config:
        from_attributes = True


class MappingDefinitionResponse(BaseModel):
    """Mapping definition response."""

    id: int
    mapping_code: str
    source_entity: str
    target_entity: str
    status: str
    created_by_user_id: int
    created_at_utc: datetime
    updated_at_utc: datetime
    current_version: MappingVersionResponse | None = None

    class Config:
        from_attributes = True


class MappingListResponse(BaseModel):
    """Mapping list response."""

    items: list[MappingDefinitionResponse]
    total: int
