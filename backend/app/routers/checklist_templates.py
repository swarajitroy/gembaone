"""Checklist templates router."""
import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_context import get_correlation_id, get_current_user
from app.models.auth import User
from app.schemas.checklist_templates import (
    ChecklistItemResponse,
    CreateTemplateRequest,
    ItemConditionResponse,
    PublishVersionRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateVersionResponse,
)
from app.services.checklist_template_service import ChecklistTemplateService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/checklist-templates", tags=["checklist-templates"])


@router.post("", response_model=TemplateResponse)
def create_template(
    request_data: CreateTemplateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create checklist template."""
    correlation_id = get_correlation_id(request)

    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "template_management")

    # Create template
    template_service = ChecklistTemplateService(db)
    template, version = template_service.create_template(
        template_code=request_data.template_code,
        name=request_data.name,
        description=request_data.description,
        items=request_data.items,
        user=user,
        correlation_id=correlation_id,
    )

    return TemplateResponse(
        id=template.id,
        template_code=template.template_code,
        name=template.name,
        description=template.description,
        current_version_id=template.current_version_id,
        status=template.status,
        created_by_user_id=template.created_by_user_id,
        created_at_utc=template.created_at_utc.isoformat(),
        updated_at_utc=template.updated_at_utc.isoformat(),
    )


@router.get("", response_model=TemplateListResponse)
def list_templates(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List checklist templates."""
    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "template_management")

    # List templates
    template_service = ChecklistTemplateService(db)
    offset = (page - 1) * page_size
    templates, total = template_service.list_templates(offset, page_size)

    items = [
        TemplateResponse(
            id=t.id,
            template_code=t.template_code,
            name=t.name,
            description=t.description,
            current_version_id=t.current_version_id,
            status=t.status,
            created_by_user_id=t.created_by_user_id,
            created_at_utc=t.created_at_utc.isoformat(),
            updated_at_utc=t.updated_at_utc.isoformat(),
        )
        for t in templates
    ]

    return TemplateListResponse(items=items, total=total)


@router.post("/{template_id}/versions", response_model=TemplateVersionResponse)
def publish_version(
    template_id: int,
    request_data: PublishVersionRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish new version of checklist template."""
    correlation_id = get_correlation_id(request)

    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "template_management")

    # Publish version
    template_service = ChecklistTemplateService(db)
    version = template_service.publish_version(
        template_id=template_id,
        version_label=request_data.version_label,
        items=request_data.items,
        user=user,
        correlation_id=correlation_id,
    )

    # Get items for response
    items = template_service.repository.get_items_by_version(version.id)

    item_responses = []
    for item in items:
        # Get condition if exists
        condition = template_service.repository.get_condition_by_item(item.id)
        condition_response = None
        if condition:
            condition_response = ItemConditionResponse(
                source_item_key=condition.source_item_key,
                operator=condition.operator,
                expected_value=condition.expected_value,
            )

        # Parse options
        options = json.loads(item.options_json) if item.options_json else None

        item_responses.append(
            ChecklistItemResponse(
                id=item.id,
                item_key=item.item_key,
                label=item.label,
                item_type=item.item_type,
                display_order=item.display_order,
                is_required=item.is_required,
                evidence_required=item.evidence_required,
                location_mode=item.location_mode,
                options=options,
                condition=condition_response,
            )
        )

    return TemplateVersionResponse(
        id=version.id,
        template_id=version.template_id,
        version_number=version.version_number,
        version_label=version.version_label,
        status=version.status,
        published_at_utc=version.published_at_utc.isoformat() if version.published_at_utc else None,
        published_by_user_id=version.published_by_user_id,
        items=item_responses,
        created_at_utc=version.created_at_utc.isoformat(),
    )


@router.post("/{template_id}/retire", response_model=TemplateResponse)
def retire_template(
    template_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retire checklist template."""
    correlation_id = get_correlation_id(request)

    # Check permission
    permission_service = PermissionService(db)
    permission_service.require_permission(user, "template_management")

    # Retire template
    template_service = ChecklistTemplateService(db)
    template = template_service.retire_template(
        template_id=template_id,
        user=user,
        correlation_id=correlation_id,
    )

    return TemplateResponse(
        id=template.id,
        template_code=template.template_code,
        name=template.name,
        description=template.description,
        current_version_id=template.current_version_id,
        status=template.status,
        created_by_user_id=template.created_by_user_id,
        created_at_utc=template.created_at_utc.isoformat(),
        updated_at_utc=template.updated_at_utc.isoformat(),
    )
