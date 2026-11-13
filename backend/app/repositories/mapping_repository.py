"""Mapping repository for database operations."""
from sqlalchemy.orm import Session

from app.models.mapping import MappingDefinition, MappingEntry, MappingVersion


class MappingRepository:
    """Repository for mapping operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_mapping_definition(
        self,
        mapping_code: str,
        source_entity: str,
        target_entity: str,
        status: str,
        created_by_user_id: int,
    ) -> MappingDefinition:
        """Create a new mapping definition."""
        mapping = MappingDefinition(
            mapping_code=mapping_code,
            source_entity=source_entity,
            target_entity=target_entity,
            status=status,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(mapping)
        self.db.flush()
        return mapping

    def get_mapping_by_code(self, mapping_code: str) -> MappingDefinition | None:
        """Get mapping definition by code."""
        return self.db.query(MappingDefinition).filter(MappingDefinition.mapping_code == mapping_code).first()

    def get_mapping_by_id(self, mapping_id: int) -> MappingDefinition | None:
        """Get mapping definition by ID."""
        return self.db.query(MappingDefinition).filter(MappingDefinition.id == mapping_id).first()

    def list_mappings(self) -> list[MappingDefinition]:
        """List all mapping definitions."""
        return self.db.query(MappingDefinition).order_by(MappingDefinition.created_at_utc.desc()).all()

    def create_mapping_version(
        self,
        mapping_definition_id: int,
        version_number: int,
        version_label: str,
        status: str,
        published_by_user_id: int | None = None,
    ) -> MappingVersion:
        """Create a new mapping version."""
        from datetime import datetime, timezone

        mapping_version = MappingVersion(
            mapping_definition_id=mapping_definition_id,
            version_number=version_number,
            version_label=version_label,
            status=status,
            published_at_utc=datetime.now(timezone.utc) if status == "active" else None,
            published_by_user_id=published_by_user_id,
        )
        self.db.add(mapping_version)
        self.db.flush()
        return mapping_version

    def get_latest_version_number(self, mapping_definition_id: int) -> int:
        """Get the latest version number for a mapping definition."""
        result = (
            self.db.query(MappingVersion.version_number)
            .filter(MappingVersion.mapping_definition_id == mapping_definition_id)
            .order_by(MappingVersion.version_number.desc())
            .first()
        )
        return result[0] if result else 0

    def get_version_by_id(self, version_id: int) -> MappingVersion | None:
        """Get mapping version by ID."""
        return self.db.query(MappingVersion).filter(MappingVersion.id == version_id).first()

    def get_active_version(self, mapping_definition_id: int) -> MappingVersion | None:
        """Get active version for a mapping definition."""
        return (
            self.db.query(MappingVersion)
            .filter(
                MappingVersion.mapping_definition_id == mapping_definition_id,
                MappingVersion.status == "active",
            )
            .first()
        )

    def mark_version_superseded(self, version_id: int) -> None:
        """Mark a mapping version as superseded."""
        version = self.get_version_by_id(version_id)
        if version:
            version.status = "superseded"
            self.db.flush()

    def create_mapping_entry(
        self,
        mapping_version_id: int,
        source_column: str,
        target_field: str,
        target_type: str,
        is_required: bool,
        transform_expression: str | None = None,
    ) -> MappingEntry:
        """Create a new mapping entry."""
        entry = MappingEntry(
            mapping_version_id=mapping_version_id,
            source_column=source_column,
            target_field=target_field,
            target_type=target_type,
            is_required=is_required,
            transform_expression=transform_expression,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_entries_for_version(self, version_id: int) -> list[MappingEntry]:
        """Get all entries for a mapping version."""
        return (
            self.db.query(MappingEntry)
            .filter(MappingEntry.mapping_version_id == version_id)
            .order_by(MappingEntry.id)
            .all()
        )

    def get_required_target_fields(self, version_id: int) -> set[str]:
        """Get set of required target fields for a version."""
        entries = self.get_entries_for_version(version_id)
        return {entry.target_field for entry in entries if entry.is_required}

    def get_mapped_source_columns(self, version_id: int) -> set[str]:
        """Get set of mapped source columns for a version."""
        entries = self.get_entries_for_version(version_id)
        return {entry.source_column for entry in entries}
