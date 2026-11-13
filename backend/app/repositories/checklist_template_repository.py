"""Checklist template repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.checklist import (
    ChecklistItemCondition,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)


class ChecklistTemplateRepository:
    """Repository for checklist template operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_template_by_id(self, template_id: int) -> ChecklistTemplate | None:
        """Get template by ID."""
        return self.db.query(ChecklistTemplate).filter(ChecklistTemplate.id == template_id).first()

    def get_template_by_code(self, template_code: str) -> ChecklistTemplate | None:
        """Get template by code."""
        return self.db.query(ChecklistTemplate).filter(ChecklistTemplate.template_code == template_code).first()

    def list_templates(self, offset: int = 0, limit: int = 100) -> tuple[list[ChecklistTemplate], int]:
        """List templates with pagination."""
        query = self.db.query(ChecklistTemplate).order_by(ChecklistTemplate.created_at_utc.desc())
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def create_template(
        self,
        template_code: str,
        name: str,
        description: str,
        created_by_user_id: int,
        status: str = "draft",
    ) -> ChecklistTemplate:
        """Create template."""
        template = ChecklistTemplate(
            template_code=template_code,
            name=name,
            description=description,
            status=status,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update_template_current_version(self, template_id: int, version_id: int) -> None:
        """Update template current version."""
        self.db.query(ChecklistTemplate).filter(ChecklistTemplate.id == template_id).update(
            {"current_version_id": version_id}
        )
        self.db.commit()

    def update_template_status(self, template_id: int, status: str) -> None:
        """Update template status."""
        self.db.query(ChecklistTemplate).filter(ChecklistTemplate.id == template_id).update(
            {"status": status}
        )
        self.db.commit()

    def create_version(
        self,
        template_id: int,
        version_number: int,
        version_label: str,
        schema_snapshot_json: str,
        status: str = "draft",
    ) -> ChecklistTemplateVersion:
        """Create template version."""
        version = ChecklistTemplateVersion(
            template_id=template_id,
            version_number=version_number,
            version_label=version_label,
            status=status,
            schema_snapshot_json=schema_snapshot_json,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def publish_version(self, version_id: int, published_by_user_id: int) -> None:
        """Publish template version."""
        now = datetime.now(timezone.utc)
        self.db.query(ChecklistTemplateVersion).filter(ChecklistTemplateVersion.id == version_id).update(
            {
                "status": "published",
                "published_at_utc": now,
                "published_by_user_id": published_by_user_id,
            }
        )
        self.db.commit()

    def get_version_by_id(self, version_id: int) -> ChecklistTemplateVersion | None:
        """Get version by ID."""
        return self.db.query(ChecklistTemplateVersion).filter(ChecklistTemplateVersion.id == version_id).first()

    def get_latest_version_number(self, template_id: int) -> int:
        """Get latest version number for template."""
        result = (
            self.db.query(ChecklistTemplateVersion.version_number)
            .filter(ChecklistTemplateVersion.template_id == template_id)
            .order_by(ChecklistTemplateVersion.version_number.desc())
            .first()
        )
        return result[0] if result else 0

    def create_item(
        self,
        template_version_id: int,
        item_key: str,
        label: str,
        item_type: str,
        display_order: int,
        is_required: bool,
        evidence_required: bool,
        location_mode: str,
        options_json: str | None,
    ) -> ChecklistTemplateItem:
        """Create template item."""
        item = ChecklistTemplateItem(
            template_version_id=template_version_id,
            item_key=item_key,
            label=label,
            item_type=item_type,
            display_order=display_order,
            is_required=is_required,
            evidence_required=evidence_required,
            location_mode=location_mode,
            options_json=options_json,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_items_by_version(self, version_id: int) -> list[ChecklistTemplateItem]:
        """Get items for version."""
        return (
            self.db.query(ChecklistTemplateItem)
            .filter(ChecklistTemplateItem.template_version_id == version_id)
            .order_by(ChecklistTemplateItem.display_order)
            .all()
        )

    def create_condition(
        self,
        template_item_id: int,
        source_item_key: str,
        operator: str,
        expected_value: str,
    ) -> ChecklistItemCondition:
        """Create item condition."""
        condition = ChecklistItemCondition(
            template_item_id=template_item_id,
            source_item_key=source_item_key,
            operator=operator,
            expected_value=expected_value,
        )
        self.db.add(condition)
        self.db.commit()
        self.db.refresh(condition)
        return condition

    def get_condition_by_item(self, item_id: int) -> ChecklistItemCondition | None:
        """Get condition for item."""
        return self.db.query(ChecklistItemCondition).filter(ChecklistItemCondition.template_item_id == item_id).first()
