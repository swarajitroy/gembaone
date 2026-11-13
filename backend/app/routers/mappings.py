"""Mapping router for API endpoints."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_context import get_current_user
from app.models.auth import User
from app.schemas.mappings import (
    CreateMappingRequest,
    MappingDefinitionResponse,
    MappingListResponse,
    MappingVersionResponse,
    PublishMappingVersionRequest,
)
from app.services.mapping_service import MappingService

router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.post("", response_model=MappingDefinitionResponse, status_code=201)
def create_mapping(
    request_data: CreateMappingRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new mapping definition with initial entries."""
    service = MappingService(db)
    return service.create_mapping_definition(request_data, user.id)


@router.get("", response_model=MappingListResponse)
def list_mappings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all mapping definitions with their active versions."""
    service = MappingService(db)
    return service.list_mappings()


@router.post("/{id}/versions", response_model=MappingVersionResponse, status_code=201)
def publish_version(
    id: int,
    request_data: PublishMappingVersionRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a new version of a mapping definition."""
    service = MappingService(db)
    return service.publish_mapping_version(id, request_data, user.id)
