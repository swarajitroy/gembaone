"""Checklist template schemas."""
from pydantic import BaseModel


class ItemConditionRequest(BaseModel):
    """Condition for a checklist item."""
    source_item_key: str
    operator: str  # equals, not_equals, contains, greater_than, less_than
    expected_value: str


class ChecklistItemRequest(BaseModel):
    """Checklist item request schema."""
    item_key: str
    label: str
    item_type: str  # text, number, boolean, date, single_select, multi_select, file
    display_order: int
    is_required: bool
    evidence_required: bool = False
    location_mode: str = "none"  # none, optional, required
    options: dict | None = None
    condition: ItemConditionRequest | None = None


class CreateTemplateRequest(BaseModel):
    """Create template request schema."""
    template_code: str
    name: str
    description: str
    items: list[ChecklistItemRequest]


class PublishVersionRequest(BaseModel):
    """Publish version request schema."""
    version_label: str
    items: list[ChecklistItemRequest]


class ItemConditionResponse(BaseModel):
    """Condition response for a checklist item."""
    source_item_key: str
    operator: str
    expected_value: str

    class Config:
        from_attributes = True


class ChecklistItemResponse(BaseModel):
    """Checklist item response schema."""
    id: int
    item_key: str
    label: str
    item_type: str
    display_order: int
    is_required: bool
    evidence_required: bool
    location_mode: str
    options: dict | None
    condition: ItemConditionResponse | None

    class Config:
        from_attributes = True


class TemplateVersionResponse(BaseModel):
    """Template version response schema."""
    id: int
    template_id: int
    version_number: int
    version_label: str
    status: str
    published_at_utc: str | None
    published_by_user_id: int | None
    items: list[ChecklistItemResponse]
    created_at_utc: str

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Template response schema."""
    id: int
    template_code: str
    name: str
    description: str
    current_version_id: int | None
    status: str
    created_by_user_id: int
    created_at_utc: str
    updated_at_utc: str

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Template list response schema."""
    items: list[TemplateResponse]
    total: int
