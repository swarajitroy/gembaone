"""Checklist template service."""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.checklist import ChecklistTemplate, ChecklistTemplateVersion
from app.repositories.checklist_template_repository import ChecklistTemplateRepository
from app.schemas.checklist_templates import ChecklistItemRequest
from app.services.audit_service import AuditService


class ChecklistTemplateService:
    """Service for checklist template operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ChecklistTemplateRepository(db)
        self.audit_service = AuditService(db)

    def validate_conditional_items(self, items: list[ChecklistItemRequest]) -> None:
        """Validate that conditional items reference source items that appear earlier.

        Raises:
            HTTPException: If validation fails
        """
        # Build item key to display order map
        item_order = {item.item_key: item.display_order for item in items}

        for item in items:
            if item.condition:
                source_key = item.condition.source_item_key

                # Check source exists
                if source_key not in item_order:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Conditional item '{item.item_key}' references unknown source '{source_key}'"
                    )

                # Check source appears earlier
                if item_order[source_key] >= item.display_order:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Conditional item '{item.item_key}' must appear after its source '{source_key}' in display order"
                    )

    def create_template(
        self,
        template_code: str,
        name: str,
        description: str,
        items: list[ChecklistItemRequest],
        user: User,
        correlation_id: str | None,
    ) -> tuple[ChecklistTemplate, ChecklistTemplateVersion]:
        """Create template with initial version.

        Returns:
            Tuple of (template, version)
        """
        # Check uniqueness
        existing = self.repository.get_template_by_code(template_code)
        if existing:
            raise HTTPException(status_code=400, detail=f"Template code '{template_code}' already exists")

        # Validate conditional items
        self.validate_conditional_items(items)

        # Create template
        template = self.repository.create_template(
            template_code=template_code,
            name=name,
            description=description,
            created_by_user_id=user.id,
            status="active",
        )

        # Create version
        schema_snapshot = json.dumps({
            "template_code": template_code,
            "name": name,
            "description": description,
            "items": [item.model_dump() for item in items]
        })

        version = self.repository.create_version(
            template_id=template.id,
            version_number=1,
            version_label="v1.0",
            schema_snapshot_json=schema_snapshot,
            status="published",
        )

        # Publish version
        self.repository.publish_version(version.id, user.id)

        # Create items
        for item_data in items:
            options_json = json.dumps(item_data.options) if item_data.options else None
            item = self.repository.create_item(
                template_version_id=version.id,
                item_key=item_data.item_key,
                label=item_data.label,
                item_type=item_data.item_type,
                display_order=item_data.display_order,
                is_required=item_data.is_required,
                evidence_required=item_data.evidence_required,
                location_mode=item_data.location_mode,
                options_json=options_json,
            )

            # Create condition if specified
            if item_data.condition:
                self.repository.create_condition(
                    template_item_id=item.id,
                    source_item_key=item_data.condition.source_item_key,
                    operator=item_data.condition.operator,
                    expected_value=item_data.condition.expected_value,
                )

        # Update template with current version
        self.repository.update_template_current_version(template.id, version.id)

        # Audit
        self.audit_service.record_event(
            event_type="template_created",
            actor=user.id,
            entity_ref=("template", str(template.id)),
            correlation_id=correlation_id,
            payload={"template_code": template_code, "version": "v1.0"},
        )

        return template, version

    def list_templates(self, offset: int = 0, limit: int = 100) -> tuple[list[ChecklistTemplate], int]:
        """List templates."""
        return self.repository.list_templates(offset, limit)

    def get_template(self, template_id: int) -> ChecklistTemplate:
        """Get template by ID."""
        template = self.repository.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template

    def publish_version(
        self,
        template_id: int,
        version_label: str,
        items: list[ChecklistItemRequest],
        user: User,
        correlation_id: str | None,
    ) -> ChecklistTemplateVersion:
        """Publish new version of template."""
        # Get template
        template = self.repository.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Validate conditional items
        self.validate_conditional_items(items)

        # Get next version number
        version_number = self.repository.get_latest_version_number(template_id) + 1

        # Create version
        schema_snapshot = json.dumps({
            "template_code": template.template_code,
            "name": template.name,
            "description": template.description,
            "items": [item.model_dump() for item in items]
        })

        version = self.repository.create_version(
            template_id=template.id,
            version_number=version_number,
            version_label=version_label,
            schema_snapshot_json=schema_snapshot,
            status="published",
        )

        # Publish version
        self.repository.publish_version(version.id, user.id)

        # Create items
        for item_data in items:
            options_json = json.dumps(item_data.options) if item_data.options else None
            item = self.repository.create_item(
                template_version_id=version.id,
                item_key=item_data.item_key,
                label=item_data.label,
                item_type=item_data.item_type,
                display_order=item_data.display_order,
                is_required=item_data.is_required,
                evidence_required=item_data.evidence_required,
                location_mode=item_data.location_mode,
                options_json=options_json,
            )

            # Create condition if specified
            if item_data.condition:
                self.repository.create_condition(
                    template_item_id=item.id,
                    source_item_key=item_data.condition.source_item_key,
                    operator=item_data.condition.operator,
                    expected_value=item_data.condition.expected_value,
                )

        # Update template with new current version
        self.repository.update_template_current_version(template.id, version.id)

        # Audit
        self.audit_service.record_event(
            event_type="template_version_published",
            actor=user.id,
            entity_ref=("template_version", str(version.id)),
            correlation_id=correlation_id,
            payload={"template_id": template_id, "version_label": version_label},
        )

        return version

    def retire_template(
        self,
        template_id: int,
        user: User,
        correlation_id: str | None,
    ) -> ChecklistTemplate:
        """Retire template."""
        template = self.repository.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        self.repository.update_template_status(template_id, "retired")

        # Audit
        self.audit_service.record_event(
            event_type="template_retired",
            actor=user.id,
            entity_ref=("template", str(template_id)),
            correlation_id=correlation_id,
            payload={"template_code": template.template_code},
        )

        # Return refreshed template
        refreshed = self.repository.get_template_by_id(template_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Template not found after update")
        return refreshed
