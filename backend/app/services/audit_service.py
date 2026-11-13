"""Audit service."""
import json

from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for audit event recording."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditRepository(db)

    def record_event(
        self,
        event_type: str,
        actor: int | None,
        entity_ref: tuple[str, str] | None,
        correlation_id: str | None,
        payload: dict | None = None,
    ) -> None:
        """Record audit event.

        Args:
            event_type: Type of event (e.g., "login_success", "template_published")
            actor: User ID of the actor
            entity_ref: Tuple of (entity_type, entity_id)
            correlation_id: Correlation ID for request tracing
            payload: Additional event payload data
        """
        entity_type = entity_ref[0] if entity_ref else None
        entity_id = entity_ref[1] if entity_ref else None
        payload_json = json.dumps(payload) if payload else None

        self.repository.create_audit_log(
            event_type=event_type,
            actor_user_id=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            event_payload_json=payload_json,
        )
