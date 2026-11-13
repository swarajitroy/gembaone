"""Checklist instance repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.checklist import (
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistLocation,
    ChecklistTemplateVersion,
)


class ChecklistRepository:
    """Repository for checklist instance operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_instance(
        self,
        template_version_id: int,
        title: str | None,
        status: str,
        template_snapshot_json: str,
        created_by_user_id: int,
    ) -> ChecklistInstance:
        """Create checklist instance."""
        instance = ChecklistInstance(
            template_version_id=template_version_id,
            title=title,
            status=status,
            template_snapshot_json=template_snapshot_json,
            visibility_trace_json=None,  # Initialize empty, evaluated later
            created_by_user_id=created_by_user_id,
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get_instance_by_id(self, instance_id: int) -> ChecklistInstance | None:
        """Get checklist instance by ID."""
        return self.db.query(ChecklistInstance).filter(ChecklistInstance.id == instance_id).first()

    def create_instance_item(
        self,
        checklist_instance_id: int,
        template_item_id: int,
        item_key: str,
        label: str,
        item_type: str,
        display_order: int,
        is_required: bool,
        evidence_required: bool,
        location_mode: str,
        condition_snapshot_json: str | None,
    ) -> ChecklistInstanceItem:
        """Create checklist instance item."""
        item = ChecklistInstanceItem(
            checklist_instance_id=checklist_instance_id,
            template_item_id=template_item_id,
            item_key=item_key,
            label=label,
            item_type=item_type,
            display_order=display_order,
            is_required=is_required,
            evidence_required=evidence_required,
            location_mode=location_mode,
            condition_snapshot_json=condition_snapshot_json,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_items_by_instance(self, instance_id: int) -> list[ChecklistInstanceItem]:
        """Get items for checklist instance."""
        return (
            self.db.query(ChecklistInstanceItem)
            .filter(ChecklistInstanceItem.checklist_instance_id == instance_id)
            .order_by(ChecklistInstanceItem.display_order)
            .all()
        )

    def get_item_by_id(self, item_id: int) -> ChecklistInstanceItem | None:
        """Get checklist instance item by ID."""
        return self.db.query(ChecklistInstanceItem).filter(ChecklistInstanceItem.id == item_id).first()

    def create_location(
        self,
        checklist_instance_id: int,
        checklist_instance_item_id: int | None,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
        captured_by_user_id: int,
    ) -> ChecklistLocation:
        """Create location record."""
        location = ChecklistLocation(
            checklist_instance_id=checklist_instance_id,
            checklist_instance_item_id=checklist_instance_item_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            captured_by_user_id=captured_by_user_id,
            captured_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def get_locations_by_instance(self, instance_id: int) -> list[ChecklistLocation]:
        """Get all locations for checklist instance."""
        return (
            self.db.query(ChecklistLocation)
            .filter(ChecklistLocation.checklist_instance_id == instance_id)
            .all()
        )

    def get_template_version_by_id(self, version_id: int) -> ChecklistTemplateVersion | None:
        """Get template version by ID."""
        return self.db.query(ChecklistTemplateVersion).filter(ChecklistTemplateVersion.id == version_id).first()
