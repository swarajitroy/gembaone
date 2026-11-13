"""Mapping service for business logic."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.mapping import MappingDefinition, MappingVersion
from app.repositories.mapping_repository import MappingRepository
from app.schemas.mappings import (
    CreateMappingRequest,
    MappingDefinitionResponse,
    MappingEntryResponse,
    MappingListResponse,
    MappingVersionResponse,
    PublishMappingVersionRequest,
)


class MappingService:
    """Service for mapping operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = MappingRepository(db)

    def create_mapping_definition(
        self, request: CreateMappingRequest, user_id: int
    ) -> MappingDefinitionResponse:
        """Create a new mapping definition with initial entries."""
        # Check if mapping code already exists
        existing = self.repo.get_mapping_by_code(request.mapping_code)
        if existing:
            raise HTTPException(status_code=400, detail=f"Mapping code '{request.mapping_code}' already exists")

        # Validate entries
        self._validate_entries(request.entries, create=True)

        # Create mapping definition
        mapping = self.repo.create_mapping_definition(
            mapping_code=request.mapping_code,
            source_entity=request.source_entity,
            target_entity=request.target_entity,
            status="active",
            created_by_user_id=user_id,
        )

        # Create initial version
        version = self.repo.create_mapping_version(
            mapping_definition_id=mapping.id,
            version_number=1,
            version_label="v1.0",
            status="active",
            published_by_user_id=user_id,
        )

        # Create entries
        for entry_data in request.entries:
            self.repo.create_mapping_entry(
                mapping_version_id=version.id,
                source_column=entry_data.source_column,
                target_field=entry_data.target_field,
                target_type=entry_data.target_type,
                is_required=entry_data.is_required,
                transform_expression=entry_data.transform_expression,
            )

        self.db.commit()

        # Return response with version and entries
        return self._build_mapping_response(mapping, version)

    def publish_mapping_version(
        self, mapping_id: int, request: PublishMappingVersionRequest, user_id: int
    ) -> MappingVersionResponse:
        """Publish a new version of a mapping definition."""
        # Get mapping definition
        mapping = self.repo.get_mapping_by_id(mapping_id)
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping definition not found")

        # Validate entries
        self._validate_entries(request.entries, create=False)

        # Get next version number
        next_version = self.repo.get_latest_version_number(mapping.id) + 1

        # Mark current active version as superseded
        current_active = self.repo.get_active_version(mapping.id)
        if current_active:
            self.repo.mark_version_superseded(current_active.id)

        # Create new version
        new_version = self.repo.create_mapping_version(
            mapping_definition_id=mapping.id,
            version_number=next_version,
            version_label=request.version_label,
            status="active",
            published_by_user_id=user_id,
        )

        # Create entries
        for entry_data in request.entries:
            self.repo.create_mapping_entry(
                mapping_version_id=new_version.id,
                source_column=entry_data.source_column,
                target_field=entry_data.target_field,
                target_type=entry_data.target_type,
                is_required=entry_data.is_required,
                transform_expression=entry_data.transform_expression,
            )

        self.db.commit()

        # Build response
        entries = self.repo.get_entries_for_version(new_version.id)
        entry_responses = [
            MappingEntryResponse(
                id=entry.id,
                mapping_version_id=entry.mapping_version_id,
                source_column=entry.source_column,
                target_field=entry.target_field,
                target_type=entry.target_type,
                is_required=entry.is_required,
                transform_expression=entry.transform_expression,
                created_at_utc=entry.created_at_utc,
            )
            for entry in entries
        ]

        return MappingVersionResponse(
            id=new_version.id,
            mapping_definition_id=new_version.mapping_definition_id,
            version_number=new_version.version_number,
            version_label=new_version.version_label,
            status=new_version.status,
            published_at_utc=new_version.published_at_utc,
            published_by_user_id=new_version.published_by_user_id,
            created_at_utc=new_version.created_at_utc,
            entries=entry_responses,
        )

    def list_mappings(self) -> MappingListResponse:
        """List all mapping definitions with their active versions."""
        mappings = self.repo.list_mappings()

        items = []
        for mapping in mappings:
            active_version = self.repo.get_active_version(mapping.id)
            version_response = None

            if active_version:
                entries = self.repo.get_entries_for_version(active_version.id)
                entry_responses = [
                    MappingEntryResponse(
                        id=entry.id,
                        mapping_version_id=entry.mapping_version_id,
                        source_column=entry.source_column,
                        target_field=entry.target_field,
                        target_type=entry.target_type,
                        is_required=entry.is_required,
                        transform_expression=entry.transform_expression,
                        created_at_utc=entry.created_at_utc,
                    )
                    for entry in entries
                ]

                version_response = MappingVersionResponse(
                    id=active_version.id,
                    mapping_definition_id=active_version.mapping_definition_id,
                    version_number=active_version.version_number,
                    version_label=active_version.version_label,
                    status=active_version.status,
                    published_at_utc=active_version.published_at_utc,
                    published_by_user_id=active_version.published_by_user_id,
                    created_at_utc=active_version.created_at_utc,
                    entries=entry_responses,
                )

            items.append(
                MappingDefinitionResponse(
                    id=mapping.id,
                    mapping_code=mapping.mapping_code,
                    source_entity=mapping.source_entity,
                    target_entity=mapping.target_entity,
                    status=mapping.status,
                    created_by_user_id=mapping.created_by_user_id,
                    created_at_utc=mapping.created_at_utc,
                    updated_at_utc=mapping.updated_at_utc,
                    current_version=version_response,
                )
            )

        return MappingListResponse(items=items, total=len(items))

    def resolve_active_mapping(self, entity_code: str) -> MappingVersion | None:
        """Resolve the active mapping version for a given entity code."""
        mapping = self.repo.get_mapping_by_code(entity_code)
        if not mapping:
            return None

        return self.repo.get_active_version(mapping.id)

    def _validate_entries(self, entries: list, create: bool = False) -> None:
        """Validate mapping entries."""
        if not entries:
            raise HTTPException(status_code=400, detail="At least one mapping entry is required")

        # Check for duplicate source columns
        source_columns = [entry.source_column for entry in entries]
        if len(source_columns) != len(set(source_columns)):
            raise HTTPException(status_code=400, detail="Duplicate source columns are not allowed")

        # Validate target types
        valid_types = {"string", "number", "date", "boolean"}
        for entry in entries:
            if entry.target_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target type '{entry.target_type}'. Must be one of: {', '.join(valid_types)}",
                )

    def _build_mapping_response(
        self, mapping: MappingDefinition, version: MappingVersion
    ) -> MappingDefinitionResponse:
        """Build mapping definition response with version and entries."""
        entries = self.repo.get_entries_for_version(version.id)
        entry_responses = [
            MappingEntryResponse(
                id=entry.id,
                mapping_version_id=entry.mapping_version_id,
                source_column=entry.source_column,
                target_field=entry.target_field,
                target_type=entry.target_type,
                is_required=entry.is_required,
                transform_expression=entry.transform_expression,
                created_at_utc=entry.created_at_utc,
            )
            for entry in entries
        ]

        version_response = MappingVersionResponse(
            id=version.id,
            mapping_definition_id=version.mapping_definition_id,
            version_number=version.version_number,
            version_label=version.version_label,
            status=version.status,
            published_at_utc=version.published_at_utc,
            published_by_user_id=version.published_by_user_id,
            created_at_utc=version.created_at_utc,
            entries=entry_responses,
        )

        return MappingDefinitionResponse(
            id=mapping.id,
            mapping_code=mapping.mapping_code,
            source_entity=mapping.source_entity,
            target_entity=mapping.target_entity,
            status=mapping.status,
            created_by_user_id=mapping.created_by_user_id,
            created_at_utc=mapping.created_at_utc,
            updated_at_utc=mapping.updated_at_utc,
            current_version=version_response,
        )
