"""Checklist execution service."""
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.checklist import ChecklistInstance
from app.repositories.answer_repository import AnswerRepository
from app.repositories.checklist_repository import ChecklistRepository
from app.repositories.checklist_template_repository import ChecklistTemplateRepository
from app.services.audit_service import AuditService


class ChecklistExecutionService:
    """Service for checklist execution operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ChecklistRepository(db)
        self.template_repository = ChecklistTemplateRepository(db)
        self.answer_repository = AnswerRepository(db)
        self.audit_service = AuditService(db)

    def create_instance(
        self,
        template_version_id: int,
        title: str | None,
        user: User,
        correlation_id: str | None,
    ) -> int:
        """Create checklist instance from active template version.

        Args:
            template_version_id: ID of the template version to use
            title: Optional custom title for instance
            user: Current user creating the instance
            correlation_id: Correlation ID for audit trail

        Returns:
            ID of created checklist instance

        Raises:
            HTTPException: If template version not found or not active
        """
        # Get template version
        version = self.repository.get_template_version_by_id(template_version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Template version not found")

        # FR-003: Only active (published) versions can be instantiated
        if version.status != "published":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create instance from {version.status} template version. Only published versions are allowed."
            )

        # Snapshot template structure
        template = self.template_repository.get_template_by_id(version.template_id)
        items = self.template_repository.get_items_by_version(template_version_id)

        template_snapshot = {
            "template_code": template.template_code if template else "",
            "template_name": template.name if template else "",
            "version_number": version.version_number,
            "version_label": version.version_label,
            "items": []
        }

        # Create instance
        instance = self.repository.create_instance(
            template_version_id=template_version_id,
            title=title or (template.name if template else "Untitled Checklist"),
            status="draft",
            template_snapshot_json=json.dumps(template_snapshot),
            created_by_user_id=user.id,
        )

        # Create instance items
        for item in items:
            # Snapshot item condition if exists
            condition = self.template_repository.get_condition_by_item(item.id)
            condition_snapshot = None
            if condition:
                condition_snapshot = json.dumps({
                    "source_item_key": condition.source_item_key,
                    "operator": condition.operator,
                    "expected_value": condition.expected_value
                })

            self.repository.create_instance_item(
                checklist_instance_id=instance.id,
                template_item_id=item.id,
                item_key=item.item_key,
                label=item.label,
                item_type=item.item_type,
                display_order=item.display_order,
                is_required=item.is_required,
                evidence_required=item.evidence_required,
                location_mode=item.location_mode,
                condition_snapshot_json=condition_snapshot,
            )

        # Audit event
        self.audit_service.record_event(
            event_type="checklist_instance_created",
            actor=user.id,
            entity_ref=("checklist_instance", str(instance.id)),
            correlation_id=correlation_id,
            payload={
                "template_version_id": template_version_id,
                "instance_id": instance.id,
                "status": "draft"
            }
        )

        return instance.id

    def upsert_answers(
        self,
        instance_id: int,
        answers: list[dict],
        user: User,
        correlation_id: str | None,
    ) -> ChecklistInstance:
        """Upsert answers for checklist instance and re-evaluate conditional visibility.

        Args:
            instance_id: Checklist instance ID
            answers: List of answer dicts with item_id, value_type, and value fields
            user: Current user answering
            correlation_id: Correlation ID for audit trail

        Returns:
            Updated checklist instance

        Raises:
            HTTPException: If instance not found or validation fails
        """
        # Verify instance exists
        instance = self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # FR-008: Submitted instances become read-only
        if instance.status == "submitted":
            raise HTTPException(
                status_code=409,
                detail="Cannot modify answers for submitted checklist. Submitted instances are read-only."
            )

        # Get all instance items
        items = self.repository.get_items_by_instance(instance_id)
        items_by_id = {item.id: item for item in items}
        {item.item_key: item for item in items}

        # Validate and upsert answers
        for answer_data in answers:
            item_id = answer_data.get("item_id")
            value_type = answer_data.get("value_type", "")

            # Validate item exists and belongs to instance
            if item_id not in items_by_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {item_id} not found or does not belong to instance"
                )

            items_by_id[item_id]

            # Type validation
            value_text = answer_data.get("value_text")
            value_number = answer_data.get("value_number")
            value_boolean = answer_data.get("value_boolean")
            value_date = answer_data.get("value_date")
            value_json = answer_data.get("value_json")

            # Validate value matches type
            if value_type == "text" and value_text is None:
                raise HTTPException(status_code=400, detail="text answer requires value_text")
            elif value_type == "number" and value_number is None:
                raise HTTPException(status_code=400, detail="number answer requires value_number")
            elif value_type == "boolean" and value_boolean is None:
                raise HTTPException(status_code=400, detail="boolean answer requires value_boolean")
            elif value_type == "date" and value_date is None:
                raise HTTPException(status_code=400, detail="date answer requires value_date")
            elif value_type == "json" and value_json is None:
                raise HTTPException(status_code=400, detail="json answer requires value_json")

            # Parse date if provided
            date_value = None
            if value_date:
                try:
                    date_value = datetime.fromisoformat(value_date.replace("Z", "+00:00"))
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")

            # Upsert answer
            self.answer_repository.upsert_answer(
                checklist_instance_item_id=item_id,
                value_type=value_type,
                value_text=value_text,
                value_number=value_number,
                value_boolean=value_boolean,
                value_date=date_value,
                value_json=value_json,
                answered_by_user_id=user.id,
            )

        # Evaluate conditional visibility (LLD Section 5.3)
        visibility_trace = self._evaluate_visibility(instance_id, items)

        # Update instance with visibility trace
        instance.visibility_trace_json = json.dumps(visibility_trace)
        self.db.commit()
        self.db.refresh(instance)

        # Audit event
        self.audit_service.record_event(
            event_type="checklist_answers_updated",
            actor=user.id,
            entity_ref=("checklist_instance", str(instance_id)),
            correlation_id=correlation_id,
            payload={
                "instance_id": instance_id,
                "answer_count": len(answers),
            }
        )

        return instance

    def _evaluate_visibility(self, instance_id: int, items: list) -> dict:
        """Evaluate conditional visibility for all items.

        Implements LLD Section 5.3 conditional visibility evaluation algorithm:
        1. Load template snapshot and conditional rules
        2. Iterate items in stable display order
        3. For each item with condition, inspect source answer and compare per operator
        4. Mark visible if satisfied, else mark hidden and non-required
        5. Return visibility trace

        Args:
            instance_id: Checklist instance ID
            items: List of checklist instance items

        Returns:
            Dictionary with visibility state for each item
        """
        visibility_trace = {}

        # Build item lookup by key
        items_by_key = {item.item_key: item for item in items}

        # Get all answers for the instance
        answers = self.answer_repository.get_answers_by_instance(instance_id)
        answers_by_item_id = {answer.checklist_instance_item_id: answer for answer in answers}

        # Evaluate each item in display order
        for item in sorted(items, key=lambda x: x.display_order):
            # Default: visible and required as configured
            is_visible = True
            is_required = item.is_required

            # Check if item has condition
            if item.condition_snapshot_json:
                try:
                    condition = json.loads(item.condition_snapshot_json)
                    source_item_key = condition.get("source_item_key")
                    operator = condition.get("operator")
                    expected_value = condition.get("expected_value")

                    # Find source item
                    source_item = items_by_key.get(source_item_key)
                    if source_item:
                        # Get source answer
                        source_answer = answers_by_item_id.get(source_item.id)

                        if source_answer:
                            # Get actual value based on type
                            actual_value: str | float | bool | None = None
                            if source_answer.value_type == "text":
                                actual_value = source_answer.value_text
                            elif source_answer.value_type == "number":
                                actual_value = source_answer.value_number
                            elif source_answer.value_type == "boolean":
                                actual_value = source_answer.value_boolean

                            # Evaluate condition
                            is_visible = self._check_condition(operator, actual_value, expected_value)
                        else:
                            # No answer yet - condition not satisfied
                            is_visible = False

                    # If hidden by condition, mark as not required
                    if not is_visible:
                        is_required = False

                except (json.JSONDecodeError, KeyError):
                    # Invalid condition - default to visible
                    is_visible = True

            visibility_trace[item.item_key] = {
                "visible": is_visible,
                "required": is_required,
                "has_condition": item.condition_snapshot_json is not None,
            }

        return visibility_trace

    def _check_condition(self, operator: str, actual_value, expected_value: str) -> bool:
        """Check if condition is satisfied.

        Supported operators: equals, not_equals, contains, greater_than, less_than

        Args:
            operator: Comparison operator
            actual_value: Actual answer value
            expected_value: Expected value (as string)

        Returns:
            True if condition satisfied, False otherwise
        """
        if actual_value is None:
            return False

        try:
            if operator == "equals":
                return str(actual_value) == expected_value
            elif operator == "not_equals":
                return str(actual_value) != expected_value
            elif operator == "contains":
                return expected_value in str(actual_value)
            elif operator == "greater_than":
                return float(actual_value) > float(expected_value)
            elif operator == "less_than":
                return float(actual_value) < float(expected_value)
            else:
                # Unknown operator - default to not satisfied
                return False
        except (ValueError, TypeError):
            # Type conversion failed - condition not satisfied
            return False

    def capture_instance_location(
        self,
        instance_id: int,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
        user: User,
        correlation_id: str | None,
    ) -> int:
        """Capture instance-level location.

        Args:
            instance_id: Checklist instance ID
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            accuracy_meters: Optional accuracy in meters
            user: Current user capturing location
            correlation_id: Correlation ID for audit trail

        Returns:
            ID of created location record

        Raises:
            HTTPException: If instance not found
        """
        # Verify instance exists
        instance = self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # Create location record
        location = self.repository.create_location(
            checklist_instance_id=instance_id,
            checklist_instance_item_id=None,  # Instance-level location
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            captured_by_user_id=user.id,
        )

        # Audit event
        self.audit_service.record_event(
            event_type="checklist_location_captured",
            actor=user.id,
            entity_ref=("checklist_instance", str(instance_id)),
            correlation_id=correlation_id,
            payload={
                "location_id": location.id,
                "latitude": latitude,
                "longitude": longitude,
                "scope": "instance"
            }
        )

        return location.id

    def submit_checklist(
        self,
        instance_id: int,
        user: User,
        correlation_id: str | None,
    ) -> dict:
        """Submit checklist instance for review.

        Implements LLD Section 11.3 submission validation rules:
        - Validates all visible required items are answered
        - Validates required evidence is attached per template item configuration
        - Transitions instance status from draft to submitted
        - Records submitter_id and submitted_at
        - Makes instance read-only
        - Returns validation failures with readable guidance if blocked

        Args:
            instance_id: Checklist instance ID
            user: Current user submitting
            correlation_id: Correlation ID for audit trail

        Returns:
            Dictionary with submission result:
            - status: "submitted" if success
            - submitted_by: User ID
            - submitted_at: ISO timestamp
            - validation_issues: List of SubmissionValidationIssue if blocked

        Raises:
            HTTPException: If instance not found or invalid state
        """
        from datetime import datetime, timezone

        # Get instance
        instance = self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # Validate instance is in draft status
        if instance.status != "draft":
            raise HTTPException(
                status_code=409,
                detail=f"Cannot submit checklist in {instance.status} status. Only draft checklists can be submitted."
            )

        # Get items and visibility trace
        items = self.repository.get_items_by_instance(instance_id)
        visibility_trace = {}
        if instance.visibility_trace_json:
            try:
                visibility_trace = json.loads(instance.visibility_trace_json)
            except json.JSONDecodeError:
                pass

        # Get all answers
        answers = self.answer_repository.get_answers_by_instance(instance_id)
        answers_by_item_id = {answer.checklist_instance_item_id: answer for answer in answers}

        # Get all attachments
        from app.repositories.evidence_repository import EvidenceRepository
        evidence_repo = EvidenceRepository(self.db)
        attachments = evidence_repo.get_attachments_by_instance(instance_id)
        attachments_by_item_id: dict[int, list] = {}
        for attachment in attachments:
            item_id = attachment.checklist_instance_item_id
            if item_id:
                attachments_by_item_id.setdefault(item_id, []).append(attachment)

        # Validation issues list
        validation_issues: list[dict] = []

        # Validate each item
        for item in items:
            item_trace = visibility_trace.get(item.item_key, {})
            is_visible = item_trace.get("visible", True)
            is_required = item_trace.get("required", item.is_required)

            # Skip hidden items (LLD Section 11.3: hidden items excluded from validation)
            if not is_visible:
                continue

            # Check required answer
            if is_required:
                answer = answers_by_item_id.get(item.id)
                if not answer:
                    validation_issues.append({
                        "item_id": item.id,
                        "code": "required_answer_missing",
                        "message": f"Required item '{item.label}' must be answered before submission.",
                        "severity": "error"
                    })

            # Check required evidence
            if item.evidence_required:
                item_attachments = attachments_by_item_id.get(item.id, [])
                if not item_attachments:
                    validation_issues.append({
                        "item_id": item.id,
                        "code": "required_evidence_missing",
                        "message": f"Item '{item.label}' requires at least one attachment before submission.",
                        "severity": "error"
                    })

        # If validation issues exist, return them without submitting
        if validation_issues:
            return {
                "status": "draft",
                "submitted_by": None,
                "submitted_at": None,
                "validation_issues": validation_issues
            }

        # All validations passed - update instance to submitted status
        now = datetime.now(timezone.utc)
        instance.status = "submitted"
        instance.submitted_by_user_id = user.id
        instance.submitted_at_utc = now
        self.db.commit()
        self.db.refresh(instance)

        # Audit event
        self.audit_service.record_event(
            event_type="checklist_submitted",
            actor=user.id,
            entity_ref=("checklist_instance", str(instance_id)),
            correlation_id=correlation_id,
            payload={
                "instance_id": instance_id,
                "submitted_at": now.isoformat(),
            }
        )

        return {
            "status": "submitted",
            "submitted_by": user.id,
            "submitted_at": now.isoformat(),
            "validation_issues": []
        }

    def capture_item_location(
        self,
        instance_id: int,
        item_id: int,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
        user: User,
        correlation_id: str | None,
    ) -> int:
        """Capture item-level location.

        Args:
            instance_id: Checklist instance ID
            item_id: Checklist instance item ID
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            accuracy_meters: Optional accuracy in meters
            user: Current user capturing location
            correlation_id: Correlation ID for audit trail

        Returns:
            ID of created location record

        Raises:
            HTTPException: If instance or item not found
        """
        # Verify instance exists
        instance = self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # Verify item exists and belongs to instance
        item = self.repository.get_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Checklist item not found")

        if item.checklist_instance_id != instance_id:
            raise HTTPException(status_code=400, detail="Item does not belong to specified instance")

        # Create location record
        location = self.repository.create_location(
            checklist_instance_id=instance_id,
            checklist_instance_item_id=item_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            captured_by_user_id=user.id,
        )

        # Audit event
        self.audit_service.record_event(
            event_type="checklist_location_captured",
            actor=user.id,
            entity_ref=("checklist_instance", str(instance_id)),
            correlation_id=correlation_id,
            payload={
                "location_id": location.id,
                "item_id": item_id,
                "latitude": latitude,
                "longitude": longitude,
                "scope": "item"
            }
        )

        return location.id
