"""Report repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ingestion import GeneratedReport
from app.models.storage import FileObject


class ReportRepository:
    """Repository for report operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_generated_report(
        self,
        ingestion_id: int,
        file_object_id: int,
        report_type: str,
        generated_by_user_id: int,
    ) -> GeneratedReport:
        """Create generated report record."""
        report = GeneratedReport(
            ingestion_id=ingestion_id,
            file_object_id=file_object_id,
            report_type=report_type,
            generated_at_utc=datetime.now(timezone.utc),
            generated_by_user_id=generated_by_user_id,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report_by_ingestion_id(self, ingestion_id: int) -> GeneratedReport | None:
        """Get report by ingestion ID."""
        return (
            self.db.query(GeneratedReport)
            .filter(GeneratedReport.ingestion_id == ingestion_id)
            .first()
        )

    def get_file_object_by_id(self, file_object_id: int) -> FileObject | None:
        """Get file object by ID."""
        return self.db.query(FileObject).filter(FileObject.id == file_object_id).first()
