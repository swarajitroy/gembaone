"""Workbook validation service."""
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories.ingestion_repository import IngestionRepository


class WorkbookValidationService:
    """Service for workbook structural validation.

    Implements the structural validation algorithm from LLD Section 5.4.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = IngestionRepository(db)

    def validate_workbook_structure(
        self,
        ingestion_id: int,
        raw_file_path: str,
        required_sheets: list[str],
        expected_headers: dict[str, list[str]],
        correlation_id: str,
    ) -> dict:
        """Validate workbook structure per LLD Section 5.4 algorithm.

        Algorithm steps:
        1. Resolve immutable raw workbook reference
        2. Check workbook readable (if no: record structural failure and mark ingestion failed, stop)
        3. Verify xlsx content type and extension
        4. Check required sheets present (if no: fail sheets with ingestion-level validation issue, stop)
        5. Validate configured header set (if headers not OK: fail headers with structural validation issues, stop)
        6. Resolve active mapping version
        7. Transition ingestion to status=validating (pass structure)

        Args:
            ingestion_id: Ingestion ID
            raw_file_path: Path to raw file in object storage
            required_sheets: List of required sheet names
            expected_headers: Dict mapping sheet name to list of expected headers
            correlation_id: Request correlation ID

        Returns:
            Dictionary with validation result: {"success": bool, "failure_detail": str | None}
        """
        # Step 1: Resolve immutable raw workbook reference (already done - file is stored)
        ingestion = self.repository.get_ingestion_by_id(ingestion_id)
        if not ingestion:
            return {"success": False, "failure_detail": "Ingestion not found"}

        # Step 2: Check workbook readable
        try:
            # Import openpyxl here to avoid requiring it if not used
            import openpyxl
            from openpyxl.utils.exceptions import InvalidFileException
        except ImportError:
            return {
                "success": False,
                "failure_detail": "Workbook validation library not available (openpyxl required)"
            }

        try:
            # Parse storage path to get actual file path
            # Format: backend/uploads/bucket/key
            backend_dir = Path(__file__).resolve().parents[2]
            file_path = backend_dir / "uploads" / raw_file_path

            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        except (InvalidFileException, FileNotFoundError, PermissionError) as e:
            # Step 2 failure: Record structural failure and mark ingestion failed
            failure_detail = f"Workbook not readable: {str(e)}"
            self.repository.update_ingestion_status(
                ingestion_id=ingestion_id,
                status="failed",
                failure_detail=failure_detail,
            )
            self.repository.create_ingestion_event(
                ingestion_id=ingestion_id,
                event_type="validation_failed",
                from_status="submitted",
                to_status="failed",
                event_message=f"Structural validation failed: {failure_detail}",
                actor_user_id=None,
                correlation_id=correlation_id,
            )
            return {"success": False, "failure_detail": failure_detail}
        except Exception as e:
            # Unexpected error
            failure_detail = f"Unexpected error reading workbook: {str(e)}"
            self.repository.update_ingestion_status(
                ingestion_id=ingestion_id,
                status="failed",
                failure_detail=failure_detail,
            )
            self.repository.create_ingestion_event(
                ingestion_id=ingestion_id,
                event_type="validation_failed",
                from_status="submitted",
                to_status="failed",
                event_message=f"Structural validation failed: {failure_detail}",
                actor_user_id=None,
                correlation_id=correlation_id,
            )
            return {"success": False, "failure_detail": failure_detail}

        # Step 3: Verify xlsx content type and extension (already validated in upload)

        # Step 4: Check required sheets present
        sheet_names = workbook.sheetnames
        missing_sheets = [sheet for sheet in required_sheets if sheet not in sheet_names]

        if missing_sheets:
            # Step 4 failure: Create ingestion-level validation issue
            failure_detail = f"Required sheet '{missing_sheets[0]}' not found"
            workbook.close()
            self.repository.update_ingestion_status(
                ingestion_id=ingestion_id,
                status="failed",
                failure_detail=failure_detail,
            )
            self.repository.create_ingestion_event(
                ingestion_id=ingestion_id,
                event_type="validation_failed",
                from_status="submitted",
                to_status="failed",
                event_message=f"Structural validation failed: {failure_detail}",
                actor_user_id=None,
                correlation_id=correlation_id,
            )
            return {"success": False, "failure_detail": failure_detail}

        # Step 5: Validate configured header set
        validation_issues = []
        for sheet_name, expected_cols in expected_headers.items():
            if sheet_name not in sheet_names:
                continue  # Already checked in step 4

            sheet = workbook[sheet_name]
            # Get first row headers
            header_row = []
            for cell in sheet[1]:
                header_row.append(cell.value)

            # Check for missing required headers
            missing_headers = [col for col in expected_cols if col not in header_row]
            if missing_headers:
                validation_issues.append(
                    f"Sheet '{sheet_name}' missing required headers: {', '.join(missing_headers)}"
                )

        workbook.close()

        if validation_issues:
            # Step 5 failure: Fail headers with structural validation issues
            failure_detail = f"Header validation failed: {'; '.join(validation_issues)}"
            self.repository.update_ingestion_status(
                ingestion_id=ingestion_id,
                status="failed",
                failure_detail=failure_detail,
            )
            self.repository.create_ingestion_event(
                ingestion_id=ingestion_id,
                event_type="validation_failed",
                from_status="submitted",
                to_status="failed",
                event_message=f"Structural validation failed: {failure_detail}",
                actor_user_id=None,
                correlation_id=correlation_id,
            )
            return {"success": False, "failure_detail": failure_detail}

        # Step 6: Resolve active mapping version (already provided in ingestion)

        # Step 7: Transition ingestion to status=validating (pass structure)
        self.repository.update_ingestion_status(
            ingestion_id=ingestion_id,
            status="validating",
            validation_started_at_utc=datetime.now(timezone.utc),
        )
        self.repository.create_ingestion_event(
            ingestion_id=ingestion_id,
            event_type="validation_started",
            from_status="submitted",
            to_status="validating",
            event_message="Structural validation passed, starting row validation",
            actor_user_id=None,
            correlation_id=correlation_id,
        )

        return {"success": True, "failure_detail": None}
