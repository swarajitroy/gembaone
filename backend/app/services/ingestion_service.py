"""Ingestion service."""
import hashlib
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.adapters.object_storage import ObjectStorageAdapter
from app.models.auth import User
from app.repositories.ingestion_repository import IngestionRepository

# Allowed MIME types for ingestion
ALLOWED_INGESTION_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# Maximum file size (25 MB)
MAX_INGESTION_FILE_SIZE = 25 * 1024 * 1024


class IngestionService:
    """Service for ingestion operations."""

    def __init__(
        self,
        db: Session,
        storage_adapter: ObjectStorageAdapter | None = None,
    ):
        self.db = db
        self.repository = IngestionRepository(db)
        self.storage_adapter = storage_adapter or ObjectStorageAdapter()

    def create_ingestion(
        self,
        file: UploadFile,
        mapping_version_id: int,
        user: User,
        correlation_id: str,
    ) -> dict:
        """Create ingestion from uploaded file.

        Args:
            file: Uploaded .xlsx file
            mapping_version_id: Mapping version to use
            user: Current user uploading file
            correlation_id: Request correlation ID

        Returns:
            Dictionary with ingestion details

        Raises:
            HTTPException: If validation fails
        """
        # Validate file extension
        if not file.filename or not file.filename.lower().endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .xlsx files are allowed."
            )

        # Read file content
        content = file.file.read()

        # Validate file size
        if len(content) > MAX_INGESTION_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_INGESTION_FILE_SIZE / (1024 * 1024):.0f}MB"
            )

        # Validate content type (allow common Excel MIME types)
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_INGESTION_TYPES and content_type != "application/vnd.ms-excel":
            # Also accept if filename is .xlsx
            if not file.filename.lower().endswith('.xlsx'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{content_type}' not allowed. Only Excel .xlsx files are supported."
                )

        # Compute SHA256 checksum
        sha256_hex = hashlib.sha256(content).hexdigest()

        # Generate storage key (UUID-based to ensure uniqueness)
        storage_key = f"{uuid.uuid4()}/{file.filename}"
        storage_bucket = "ingestion-raw-files"
        storage_path = f"{storage_bucket}/{storage_key}"

        # Store file using object storage adapter with immutable flag
        try:
            obj_ref = self.storage_adapter.put_object(
                path=storage_path,
                data=content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                immutable=True,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

        # Create file_objects metadata record
        file_object = self.repository.create_file_object(
            storage_bucket=obj_ref.bucket,
            storage_key=obj_ref.storage_key,
            original_filename=file.filename or "unnamed.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            byte_size=len(content),
            sha256_hex=sha256_hex,
            immutable_flag=True,
            created_by_user_id=user.id,
        )

        # Get validation_rule_set_id from mapping_version (for now use fixed rule set ID 1)
        # In a real implementation, this would be resolved from the mapping configuration
        validation_rule_set_id = 1

        # Create ingestion record with status=submitted
        ingestion = self.repository.create_ingestion(
            mapping_version_id=mapping_version_id,
            validation_rule_set_id=validation_rule_set_id,
            raw_file_object_id=file_object.id,
            source_filename=file.filename or "unnamed.xlsx",
            uploaded_by_user_id=user.id,
            status="submitted",
        )

        # Create ingestion_event for upload
        self.repository.create_ingestion_event(
            ingestion_id=ingestion.id,
            event_type="ingestion_uploaded",
            from_status=None,
            to_status="submitted",
            event_message=f"Ingestion file '{file.filename}' uploaded successfully",
            actor_user_id=user.id,
            correlation_id=correlation_id,
        )

        return {
            "id": ingestion.id,
            "status": ingestion.status,
            "uploaded_by": ingestion.uploaded_by_user_id,
            "uploaded_at": ingestion.uploaded_at_utc.isoformat(),
            "source_filename": ingestion.source_filename,
            "raw_file_object_id": ingestion.raw_file_object_id,
        }

    def list_ingestions(self, user: User) -> list[dict]:
        """List ingestions with ASP visibility scoping.

        Args:
            user: Current user

        Returns:
            List of ingestion records
        """
        # Check if user is ASP - if so, only show their own records
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(self.db)
        role_codes = permission_service.get_user_roles(user.id)

        # ASP users can only see their own ingestions
        if "asp_user" in role_codes and "internal_admin" not in role_codes:
            ingestions = self.repository.list_ingestions(uploaded_by_user_id=user.id)
        else:
            # Internal admins can see all ingestions
            ingestions = self.repository.list_ingestions()

        return [
            {
                "id": ing.id,
                "status": ing.status,
                "uploaded_by": ing.uploaded_by_user_id,
                "uploaded_at": ing.uploaded_at_utc.isoformat(),
                "source_filename": ing.source_filename,
                "raw_file_object_id": ing.raw_file_object_id,
                "mapping_version_id": ing.mapping_version_id,
                "validation_rule_set_id": ing.validation_rule_set_id,
                "validation_started_at": ing.validation_started_at_utc.isoformat() if ing.validation_started_at_utc else None,
                "validation_completed_at": ing.validation_completed_at_utc.isoformat() if ing.validation_completed_at_utc else None,
                "accepted_count": ing.accepted_count,
                "rejected_count": ing.rejected_count,
                "warning_count": ing.warning_count,
                "failure_detail": ing.failure_detail,
            }
            for ing in ingestions
        ]

    def get_ingestion(self, ingestion_id: int, user: User) -> dict | None:
        """Get ingestion detail with ASP visibility scoping.

        Args:
            ingestion_id: Ingestion ID
            user: Current user

        Returns:
            Ingestion details or None
        """
        ingestion = self.repository.get_ingestion_by_id(ingestion_id)
        if not ingestion:
            return None

        # Check ASP visibility
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(self.db)
        role_codes = permission_service.get_user_roles(user.id)

        # ASP users can only see their own ingestions
        if "asp_user" in role_codes and "internal_admin" not in role_codes:
            if ingestion.uploaded_by_user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied to this ingestion")

        return {
            "id": ingestion.id,
            "status": ingestion.status,
            "source_filename": ingestion.source_filename,
            "mapping_version_id": ingestion.mapping_version_id,
            "validation_rule_set_id": ingestion.validation_rule_set_id,
            "raw_file_object_id": ingestion.raw_file_object_id,
            "uploaded_by": ingestion.uploaded_by_user_id,
            "uploaded_at": ingestion.uploaded_at_utc.isoformat(),
            "validation_started_at": ingestion.validation_started_at_utc.isoformat() if ingestion.validation_started_at_utc else None,
            "validation_completed_at": ingestion.validation_completed_at_utc.isoformat() if ingestion.validation_completed_at_utc else None,
            "accepted_count": ingestion.accepted_count,
            "rejected_count": ingestion.rejected_count,
            "warning_count": ingestion.warning_count,
            "failure_detail": ingestion.failure_detail,
        }
