"""Evidence service for file attachments."""
import hashlib
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.adapters.object_storage import ObjectStorageAdapter
from app.models.auth import User
from app.repositories.checklist_repository import ChecklistRepository
from app.repositories.evidence_repository import EvidenceRepository

# Allowed MIME types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
}

# Maximum file size (25 MB)
MAX_FILE_SIZE = 25 * 1024 * 1024


class EvidenceService:
    """Service for evidence capture operations."""

    def __init__(self, db: Session, storage_adapter: ObjectStorageAdapter | None = None):
        self.db = db
        self.repository = EvidenceRepository(db)
        self.checklist_repository = ChecklistRepository(db)
        self.storage_adapter = storage_adapter or ObjectStorageAdapter()

    def upload_attachment(
        self,
        checklist_instance_id: int,
        checklist_instance_item_id: int,
        file: UploadFile,
        user: User,
    ) -> dict:
        """Upload attachment for checklist item.

        Args:
            checklist_instance_id: Checklist instance ID
            checklist_instance_item_id: Checklist instance item ID
            file: Uploaded file
            user: Current user uploading file

        Returns:
            Dictionary with attachment details

        Raises:
            HTTPException: If validation fails
        """
        # Verify instance exists
        instance = self.checklist_repository.get_instance_by_id(checklist_instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Checklist instance not found")

        # Verify item exists and belongs to instance
        item = self.checklist_repository.get_item_by_id(checklist_instance_item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Checklist item not found")

        if item.checklist_instance_id != checklist_instance_id:
            raise HTTPException(status_code=400, detail="Item does not belong to specified instance")

        # Read file content
        content = file.file.read()

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB"
            )

        # Validate content type
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{content_type}' not allowed. Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )

        # Compute SHA256 checksum
        sha256_hex = hashlib.sha256(content).hexdigest()

        # Generate storage key (UUID-based to ensure uniqueness)
        storage_key = f"{uuid.uuid4()}/{file.filename}"
        storage_bucket = "checklist-attachments"
        storage_path = f"{storage_bucket}/{storage_key}"

        # Store file using object storage adapter
        try:
            obj_ref = self.storage_adapter.put_object(
                path=storage_path,
                data=content,
                content_type=content_type,
                immutable=True,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

        # Create file_objects metadata record
        file_object = self.repository.create_file_object(
            storage_bucket=obj_ref.bucket,
            storage_key=obj_ref.storage_key,
            original_filename=file.filename or "unnamed",
            content_type=content_type,
            byte_size=len(content),
            sha256_hex=sha256_hex,
            immutable_flag=True,
            created_by_user_id=user.id,
        )

        # Create checklist_attachments record
        attachment = self.repository.create_attachment(
            checklist_instance_id=checklist_instance_id,
            checklist_instance_item_id=checklist_instance_item_id,
            file_object_id=file_object.id,
            uploaded_by_user_id=user.id,
        )

        return {
            "id": attachment.id,
            "file_object_id": file_object.id,
            "original_filename": file_object.original_filename,
            "content_type": file_object.content_type,
            "byte_size": file_object.byte_size,
            "sha256_hex": file_object.sha256_hex,
            "uploaded_by_user_id": attachment.uploaded_by_user_id,
            "uploaded_at_utc": attachment.uploaded_at_utc.isoformat(),
        }
