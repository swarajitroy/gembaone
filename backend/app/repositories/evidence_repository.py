"""Evidence repository for file objects and attachments."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.checklist import ChecklistAttachment
from app.models.storage import FileObject


class EvidenceRepository:
    """Repository for evidence operations (file objects and attachments)."""

    def __init__(self, db: Session):
        self.db = db

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
        """Create file object metadata record."""
        file_obj = FileObject(
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            original_filename=original_filename,
            content_type=content_type,
            byte_size=byte_size,
            sha256_hex=sha256_hex,
            immutable_flag=immutable_flag,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(file_obj)
        self.db.commit()
        self.db.refresh(file_obj)
        return file_obj

    def get_file_object_by_id(self, file_object_id: int) -> FileObject | None:
        """Get file object by ID."""
        return self.db.query(FileObject).filter(FileObject.id == file_object_id).first()

    def create_attachment(
        self,
        checklist_instance_id: int,
        checklist_instance_item_id: int,
        file_object_id: int,
        uploaded_by_user_id: int,
    ) -> ChecklistAttachment:
        """Create checklist attachment record."""
        attachment = ChecklistAttachment(
            checklist_instance_id=checklist_instance_id,
            checklist_instance_item_id=checklist_instance_item_id,
            file_object_id=file_object_id,
            uploaded_by_user_id=uploaded_by_user_id,
            uploaded_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def get_attachments_by_instance(self, instance_id: int) -> list[ChecklistAttachment]:
        """Get all attachments for checklist instance."""
        return (
            self.db.query(ChecklistAttachment)
            .filter(ChecklistAttachment.checklist_instance_id == instance_id)
            .all()
        )

    def get_attachments_by_item(self, item_id: int) -> list[ChecklistAttachment]:
        """Get all attachments for checklist instance item."""
        return (
            self.db.query(ChecklistAttachment)
            .filter(ChecklistAttachment.checklist_instance_item_id == item_id)
            .all()
        )
