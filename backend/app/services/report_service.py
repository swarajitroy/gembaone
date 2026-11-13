"""Report service."""
import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.adapters.object_storage import ObjectStorageAdapter
from app.models.auth import User
from app.repositories.report_repository import ReportRepository


class ReportService:
    """Service for report generation and download."""

    def __init__(
        self,
        db: Session,
        storage_adapter: ObjectStorageAdapter | None = None,
    ):
        self.db = db
        self.repository = ReportRepository(db)
        self.storage_adapter = storage_adapter or ObjectStorageAdapter()

    def generate_result_report(
        self,
        ingestion_id: int,
        user: User,
    ) -> dict:
        """Generate CSV report from ingestion row results.

        Args:
            ingestion_id: Ingestion ID
            user: Current user

        Returns:
            Dictionary with report details

        Raises:
            HTTPException: If ingestion not found or access denied
        """
        # Get ingestion record
        from app.repositories.ingestion_repository import IngestionRepository

        ingestion_repo = IngestionRepository(self.db)
        ingestion = ingestion_repo.get_ingestion_by_id(ingestion_id)

        if not ingestion:
            raise HTTPException(status_code=404, detail="Ingestion not found")

        # Check ASP permission: ASP users can only generate reports for their own ingestions
        from app.services.permission_service import PermissionService

        permission_service = PermissionService(self.db)
        role_codes = permission_service.get_user_roles(user.id)

        if "asp_user" in role_codes and "internal_admin" not in role_codes:
            if ingestion.uploaded_by_user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied to this report")

        # Check if ingestion is completed
        if ingestion.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Report can only be generated for completed ingestions"
            )

        # Get row results with validation issues
        from app.repositories.validation_repository import ValidationRepository

        validation_repo = ValidationRepository(self.db)
        row_results, total = validation_repo.get_row_results_by_ingestion_id(
            ingestion_id, limit=10000, offset=0
        )

        # Generate CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "row_number",
            "outcome",
            "target_record_key",
            "issues_summary",
            "mapped_payload_excerpt",
        ])

        # Write data rows
        for row_result in row_results:
            # Get issues for this row
            issues = validation_repo.get_issues_by_row_result_id(row_result.id)

            # Build issues summary
            issues_summary = "; ".join([
                f"{issue.severity.upper()}: {issue.message}"
                for issue in issues
            ]) if issues else ""

            # Build mapped payload excerpt (first 100 chars)
            payload_excerpt = ""
            if row_result.mapped_payload_json:
                try:
                    payload = json.loads(row_result.mapped_payload_json)
                    payload_str = json.dumps(payload, separators=(',', ':'))
                    payload_excerpt = payload_str[:100]
                    if len(payload_str) > 100:
                        payload_excerpt += "..."
                except json.JSONDecodeError:
                    payload_excerpt = row_result.mapped_payload_json[:100]

            writer.writerow([
                row_result.row_number,
                row_result.outcome,
                row_result.target_record_key or "",
                issues_summary,
                payload_excerpt,
            ])

        # Get CSV content as bytes
        csv_content = output.getvalue().encode('utf-8')
        csv_bytes = len(csv_content)

        # Compute SHA256 checksum
        sha256_hex = hashlib.sha256(csv_content).hexdigest()

        # Generate storage key
        storage_key = f"{uuid.uuid4()}/report_{ingestion_id}.csv"
        storage_bucket = "ingestion-reports"
        storage_path = f"{storage_bucket}/{storage_key}"

        # Store report file
        try:
            obj_ref = self.storage_adapter.put_object(
                path=storage_path,
                data=csv_content,
                content_type="text/csv",
                immutable=True,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store report: {str(e)}")

        # Create file_objects metadata record
        from app.repositories.ingestion_repository import IngestionRepository

        ingestion_repo = IngestionRepository(self.db)
        file_object = ingestion_repo.create_file_object(
            storage_bucket=obj_ref.bucket,
            storage_key=obj_ref.storage_key,
            original_filename=f"report_{ingestion_id}.csv",
            content_type="text/csv",
            byte_size=csv_bytes,
            sha256_hex=sha256_hex,
            immutable_flag=True,
            created_by_user_id=user.id,
        )

        # Create generated_reports record
        report = self.repository.create_generated_report(
            ingestion_id=ingestion_id,
            file_object_id=file_object.id,
            report_type="csv",
            generated_by_user_id=user.id,
        )

        return {
            "report_id": report.id,
            "report_type": report.report_type,
            "generated_at": report.generated_at_utc.isoformat(),
            "file_object_id": file_object.id,
        }

    def get_report_download(
        self,
        ingestion_id: int,
        user: User,
    ) -> dict:
        """Get signed download URL for report.

        Args:
            ingestion_id: Ingestion ID
            user: Current user

        Returns:
            Dictionary with download URL and expiry

        Raises:
            HTTPException: If report not found or access denied
        """
        # Get ingestion record
        from app.repositories.ingestion_repository import IngestionRepository

        ingestion_repo = IngestionRepository(self.db)
        ingestion = ingestion_repo.get_ingestion_by_id(ingestion_id)

        if not ingestion:
            raise HTTPException(status_code=404, detail="Ingestion not found")

        # Check ASP permission
        from app.services.permission_service import PermissionService

        permission_service = PermissionService(self.db)
        role_codes = permission_service.get_user_roles(user.id)

        if "asp_user" in role_codes and "internal_admin" not in role_codes:
            if ingestion.uploaded_by_user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied to this report")

        # Get generated report
        report = self.repository.get_report_by_ingestion_id(ingestion_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found for this ingestion")

        # Get file object metadata
        file_object = self.repository.get_file_object_by_id(report.file_object_id)
        if not file_object:
            raise HTTPException(status_code=404, detail="Report file object not found")

        # Generate signed download URL with 1 hour expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        storage_path = f"{file_object.storage_bucket}/{file_object.storage_key}"

        download_link = self.storage_adapter.get_signed_download(
            path=storage_path,
            expires_at=expires_at.isoformat(),
        )

        return {
            "download_url": download_link.url,
            "expires_at": download_link.expires_at,
            "report_type": report.report_type,
            "generated_at": report.generated_at_utc.isoformat(),
        }
