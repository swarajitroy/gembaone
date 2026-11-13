"""Checklist template and instance models."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChecklistTemplate(Base):
    """Checklist template."""

    __tablename__ = "checklist_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    current_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ChecklistTemplateVersion(Base):
    """Checklist template version."""

    __tablename__ = "checklist_template_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklist_templates.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    published_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    retired_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schema_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChecklistTemplateItem(Base):
    """Checklist template item."""

    __tablename__ = "checklist_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_template_versions.id"), nullable=False, index=True
    )
    item_key: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    location_mode: Mapped[str] = mapped_column(Text, nullable=False, default="none", server_default="none")
    options_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChecklistItemCondition(Base):
    """Checklist item conditional visibility."""

    __tablename__ = "checklist_item_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_template_items.id"), unique=True, nullable=False
    )
    source_item_key: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChecklistInstance(Base):
    """Checklist instance."""

    __tablename__ = "checklist_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_template_versions.id"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    template_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    visibility_trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    submitted_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChecklistInstanceItem(Base):
    """Checklist instance item."""

    __tablename__ = "checklist_instance_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checklist_instance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_instances.id"), nullable=False, index=True
    )
    template_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklist_template_items.id"), nullable=False)
    item_key: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    location_mode: Mapped[str] = mapped_column(Text, nullable=False)
    condition_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ChecklistAnswer(Base):
    """Checklist answer."""

    __tablename__ = "checklist_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checklist_instance_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_instance_items.id"), unique=True, nullable=False
    )
    value_type: Mapped[str] = mapped_column(Text, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[float | None] = mapped_column(nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    answered_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChecklistAttachment(Base):
    """Checklist attachment."""

    __tablename__ = "checklist_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checklist_instance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_instances.id"), nullable=False, index=True
    )
    checklist_instance_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_instance_items.id"), nullable=False, index=True
    )
    file_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_objects.id"), nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChecklistLocation(Base):
    """Checklist location."""

    __tablename__ = "checklist_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checklist_instance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checklist_instances.id"), nullable=False, index=True
    )
    checklist_instance_item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("checklist_instance_items.id"), nullable=True, index=True
    )
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    accuracy_meters: Mapped[float | None] = mapped_column(nullable=True)
    captured_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    captured_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
