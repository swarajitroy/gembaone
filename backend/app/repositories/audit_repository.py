"""Audit repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_audit_log(
        self,
        event_type: str,
        actor_user_id: int | None,
        entity_type: str | None,
        entity_id: str | None,
        correlation_id: str | None,
        event_payload_json: str | None,
    ) -> AuditLog:
        """Create audit log entry."""
        audit_log = AuditLog(
            event_type=event_type,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            event_payload_json=event_payload_json,
            occurred_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log
