"""Checklist review service."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.checklist_repository import ChecklistRepository
from app.schemas.checklists import (
    ChecklistDetailResponse,
    ChecklistInstanceItemResponse,
    ChecklistInstanceResponse,
    LocationResponse,
    TemplateVersionMetadata,
)


class ChecklistReviewService:
    """Service for checklist review operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ChecklistRepository(db)

    def get_checklist_detail(self, instance_id: int) -> ChecklistDetailResponse:
        """Retrieve checklist instance with full context.

        Args:
            instance_id: Checklist instance ID

        Returns:
            ChecklistDetailResponse with instance, items, locations, and template metadata

        Raises:
            HTTPException: If instance not found
        """
        # Get instance
        instance = self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # Get items
        items = self.repository.get_items_by_instance(instance_id)

        # Get locations
        locations = self.repository.get_locations_by_instance(instance_id)

        # Get template version metadata
        version = self.repository.get_template_version_by_id(instance.template_version_id)
        if not version:
            raise HTTPException(status_code=500, detail="Template version not found")

        # Build response
        instance_response = ChecklistInstanceResponse(
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

        item_responses = [
            ChecklistInstanceItemResponse(
                id=item.id,
                checklist_instance_id=item.checklist_instance_id,
                template_item_id=item.template_item_id,
                item_key=item.item_key,
                label=item.label,
                item_type=item.item_type,
                display_order=item.display_order,
                is_required=item.is_required,
                evidence_required=item.evidence_required,
                location_mode=item.location_mode,
                condition_snapshot_json=item.condition_snapshot_json,
            )
            for item in items
        ]

        location_responses = [
            LocationResponse(
                id=loc.id,
                checklist_instance_id=loc.checklist_instance_id,
                checklist_instance_item_id=loc.checklist_instance_item_id,
                latitude=loc.latitude,
                longitude=loc.longitude,
                accuracy_meters=loc.accuracy_meters,
                captured_by_user_id=loc.captured_by_user_id,
                captured_at_utc=loc.captured_at_utc.isoformat(),
            )
            for loc in locations
        ]

        template_version_metadata = TemplateVersionMetadata(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            version_label=version.version_label,
            status=version.status,
        )

        return ChecklistDetailResponse(
            instance=instance_response,
            items=item_responses,
            locations=location_responses,
            template_version=template_version_metadata,
        )
