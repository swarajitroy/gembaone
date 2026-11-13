"""Mapping definition models."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MappingDefinition(Base):
    """Mapping definition."""

    __tablename__ = "mapping_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source_entity: Mapped[str] = mapped_column(Text, nullable=False)
    target_entity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class MappingVersion(Base):
    """Mapping version."""

    __tablename__ = "mapping_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mapping_definitions.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    published_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MappingEntry(Base):
    """Mapping entry."""

    __tablename__ = "mapping_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mapping_versions.id"), nullable=False, index=True
    )
    source_column: Mapped[str] = mapped_column(Text, nullable=False)
    target_field: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    transform_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
