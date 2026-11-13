"""Ingestion repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ingestion import IngestionEvent, IngestionRecord
from app.models.storage import FileObject


class IngestionRepository:
    """Repository for ingestion operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_ingestion(
        self,
        mapping_version_id: int,
        validation_rule_set_id: int,
        raw_file_object_id: int,
        source_filename: str,
        uploaded_by_user_id: int,
        status: str = "submitted",
    ) -> IngestionRecord:
        """Create ingestion record."""
        ingestion = IngestionRecord(
            mapping_version_id=mapping_version_id,
            validation_rule_set_id=validation_rule_set_id,
            raw_file_object_id=raw_file_object_id,
            status=status,
            source_filename=source_filename,
            uploaded_by_user_id=uploaded_by_user_id,
            uploaded_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(ingestion)
        self.db.commit()
        self.db.refresh(ingestion)
        return ingestion

    def get_ingestion_by_id(self, ingestion_id: int) -> IngestionRecord | None:
        """Get ingestion by ID."""
        return self.db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).first()

    def list_ingestions(self, uploaded_by_user_id: int | None = None) -> list[IngestionRecord]:
        """List ingestions with optional user filter for ASP visibility."""
        query = self.db.query(IngestionRecord)
        if uploaded_by_user_id is not None:
            query = query.filter(IngestionRecord.uploaded_by_user_id == uploaded_by_user_id)
        return query.order_by(IngestionRecord.uploaded_at_utc.desc()).all()

    def update_ingestion_status(
        self,
        ingestion_id: int,
        status: str,
        failure_detail: str | None = None,
        validation_started_at_utc: datetime | None = None,
        validation_completed_at_utc: datetime | None = None,
    ) -> IngestionRecord | None:
        """Update ingestion status."""
        ingestion = self.get_ingestion_by_id(ingestion_id)
        if not ingestion:
            return None

        ingestion.status = status
        if failure_detail is not None:
            ingestion.failure_detail = failure_detail
        if validation_started_at_utc is not None:
            ingestion.validation_started_at_utc = validation_started_at_utc
        if validation_completed_at_utc is not None:
            ingestion.validation_completed_at_utc = validation_completed_at_utc

        self.db.commit()
        self.db.refresh(ingestion)
        return ingestion

    def create_ingestion_event(
        self,
        ingestion_id: int,
        event_type: str,
        from_status: str | None,
        to_status: str | None,
        event_message: str,
        actor_user_id: int | None,
        correlation_id: str,
    ) -> IngestionEvent:
        """Create ingestion event."""
        event = IngestionEvent(
            ingestion_id=ingestion_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            event_message=event_message,
            event_at_utc=datetime.now(timezone.utc),
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_file_object(
        self,
        storage_bucket: str,
        storage_key: str,
        original_filename: str,
        content_type: str,
        byte_size: int,
        sha256_hex: str,
        immutable_flag: bool,
        created_by_user_id: int,
    ) -> FileObject:
        """Create file object metadata."""
        file_object = FileObject(
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            original_filename=original_filename,
            content_type=content_type,
            byte_size=byte_size,
            sha256_hex=sha256_hex,
            immutable_flag=immutable_flag,
            created_by_user_id=created_by_user_id,
            created_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(file_object)
        self.db.commit()
        self.db.refresh(file_object)
        return file_object
