"""Raw file service."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.adapters.object_storage import ObjectStorageAdapter
from app.models.auth import User
from app.repositories.report_repository import ReportRepository


class RawFileService:
    """Service for raw file access."""

    def __init__(
        self,
        db: Session,
        storage_adapter: ObjectStorageAdapter | None = None,
    ):
        self.db = db
        self.repository = ReportRepository(db)
        self.storage_adapter = storage_adapter or ObjectStorageAdapter()

    def get_raw_file_metadata(
        self,
        ingestion_id: int,
        user: User,
    ) -> dict:
        """Get raw file metadata for an ingestion.

        Args:
            ingestion_id: Ingestion ID
            user: Current user

        Returns:
            Dictionary with file metadata

        Raises:
            HTTPException: If ingestion not found or access denied
        """
        # Get ingestion record
        from app.repositories.ingestion_repository import IngestionRepository

        ingestion_repo = IngestionRepository(self.db)
        ingestion = ingestion_repo.get_ingestion_by_id(ingestion_id)

        if not ingestion:
            raise HTTPException(status_code=404, detail="Ingestion not found")

        # Check ASP permission: ASP users can only access their own uploads
        from app.services.permission_service import PermissionService

        permission_service = PermissionService(self.db)
        role_codes = permission_service.get_user_roles(user.id)

        if "asp_user" in role_codes and "internal_admin" not in role_codes:
            if ingestion.uploaded_by_user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied to this raw file")

        # Get file object metadata
        file_object = self.repository.get_file_object_by_id(ingestion.raw_file_object_id)
        if not file_object:
            raise HTTPException(status_code=404, detail="Raw file object not found")

        return {
            "file_object_id": file_object.id,
            "original_filename": file_object.original_filename,
            "byte_size": file_object.byte_size,
            "content_type": file_object.content_type,
            "storage_bucket": file_object.storage_bucket,
            "storage_key": file_object.storage_key,
        }

    def get_raw_file_download(
        self,
        ingestion_id: int,
        user: User,
    ) -> dict:
        """Get signed download URL for raw file.

        Args:
            ingestion_id: Ingestion ID
            user: Current user

        Returns:
            Dictionary with download URL and expiry

        Raises:
            HTTPException: If ingestion not found or access denied
        """
        # Get file metadata (includes permission check)
        metadata = self.get_raw_file_metadata(ingestion_id, user)

        # Generate signed download URL with 1 hour expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        storage_path = f"{metadata['storage_bucket']}/{metadata['storage_key']}"

        download_link = self.storage_adapter.get_signed_download(
            path=storage_path,
            expires_at=expires_at.isoformat(),
        )

        return {
            "download_url": download_link.url,
            "expires_at": download_link.expires_at,
            "original_filename": metadata["original_filename"],
            "byte_size": metadata["byte_size"],
        }
