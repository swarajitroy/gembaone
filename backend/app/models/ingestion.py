"""Ingestion models."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IngestionRecord(Base):
    """Ingestion record."""

    __tablename__ = "ingestion_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mapping_versions.id"), nullable=False, index=True
    )
    validation_rule_set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("validation_rule_sets.id"), nullable=False, index=True
    )
    raw_file_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_objects.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validation_started_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_completed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failure_detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionEvent(Base):
    """Ingestion event."""

    __tablename__ = "ingestion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_records.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    from_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_message: Mapped[str] = mapped_column(Text, nullable=False)
    event_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    correlation_id: Mapped[str] = mapped_column(Text, nullable=False)


class IngestionRowResult(Base):
    """Ingestion row result."""

    __tablename__ = "ingestion_row_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_records.id"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    target_record_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapped_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ValidationIssue(Base):
    """Validation issue."""

    __tablename__ = "validation_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_records.id"), nullable=False, index=True
    )
    ingestion_row_result_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ingestion_row_results.id"), nullable=True, index=True
    )
    issue_scope: Mapped[str] = mapped_column(Text, nullable=False)
    issue_code: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rule_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GeneratedReport(Base):
    """Generated report."""

    __tablename__ = "generated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_records.id"), nullable=False, index=True
    )
    file_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_objects.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
