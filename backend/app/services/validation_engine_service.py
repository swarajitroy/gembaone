"""Validation engine service implementing layered row validation."""
import io
import json
import re
from datetime import datetime, timezone

import openpyxl
from sqlalchemy.orm import Session

from app.adapters.object_storage import ObjectStorageAdapter
from app.models.mapping import MappingEntry, MappingVersion
from app.models.storage import FileObject
from app.repositories.ingestion_repository import IngestionRepository
from app.repositories.validation_repository import ValidationRepository


class ValidationEngineService:
    """Validation engine service for layered row validation pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.validation_repo = ValidationRepository(db)
        self.ingestion_repo = IngestionRepository(db)
        self.storage_adapter = ObjectStorageAdapter()

    def run_validation_pipeline(self, ingestion_id: int) -> dict:
        """
        Run layered validation pipeline for an ingestion.

        Algorithm per LLD Section 5.5:
        1. Read ingestion, resolve mapping version and validation rule set
        2. For each row:
           a. Apply mapping version to source row
           b. Schema check: type validation per target_type (if fail → rejected with schema reasons)
           c. If schema passes: business check (if fail → rejected with business reasons)
           d. If business passes: warning check (if warnings → accepted_with_warning, else accepted)
           e. Persist row result
        3. Finalize run: persist ingestion summary and transition to completed

        Outcome decision model:
        - Any error-level issue → rejected
        - Warnings only → accepted_with_warning
        - No findings → accepted
        """
        # Get ingestion record
        ingestion = self.ingestion_repo.get_ingestion_by_id(ingestion_id)
        if not ingestion:
            raise ValueError(f"Ingestion {ingestion_id} not found")

        # Get mapping version
        mapping_version = (
            self.db.query(MappingVersion)
            .filter(MappingVersion.id == ingestion.mapping_version_id)
            .first()
        )
        if not mapping_version:
            raise ValueError(f"Mapping version {ingestion.mapping_version_id} not found")

        # Get mapping entries
        mapping_entries = (
            self.db.query(MappingEntry)
            .filter(MappingEntry.mapping_version_id == mapping_version.id)
            .all()
        )

        # Get validation rule set
        rule_set = self.validation_repo.get_rule_set_by_id(ingestion.validation_rule_set_id)
        if not rule_set:
            raise ValueError(f"Validation rule set {ingestion.validation_rule_set_id} not found")

        # Get validation rules
        validation_rules = self.validation_repo.get_rules_by_rule_set_id(rule_set.id)

        # Update ingestion status to validating
        self.ingestion_repo.update_ingestion_status(
            ingestion_id=ingestion_id,
            status="validating",
            validation_started_at_utc=datetime.now(timezone.utc),
        )

        # Read actual file data from storage
        accepted_count = 0
        rejected_count = 0
        warning_count = 0

        # Check if already processed
        if ingestion.accepted_count > 0 or ingestion.rejected_count > 0:
            # Already processed, just return summary
            accepted_count = ingestion.accepted_count
            rejected_count = ingestion.rejected_count
            warning_count = ingestion.warning_count
        else:
            # New ingestion - read and process actual file
            file_object = (
                self.db.query(FileObject)
                .filter(FileObject.id == ingestion.raw_file_object_id)
                .first()
            )
            if not file_object:
                raise ValueError(f"File object {ingestion.raw_file_object_id} not found")

            # Read file from storage
            storage_path = f"{file_object.storage_bucket}/{file_object.storage_key}"
            try:
                file_data = self.storage_adapter.get_object(storage_path)
            except FileNotFoundError:
                raise ValueError(f"File not found in storage: {storage_path}")

            # Parse Excel file and extract rows
            rows = self._read_excel_rows(file_data, mapping_entries)

            # Process each row
            for row_number, source_row in enumerate(rows, start=1):
                # Apply mapping to source row
                mapped_payload, mapping_issues = self._apply_mapping(source_row, mapping_entries)

                # Collect all issues for this row
                all_issues = []
                all_issues.extend(mapping_issues)

                # Schema validation
                schema_issues = self._validate_schema(mapped_payload, mapping_entries)
                all_issues.extend(schema_issues)

                # Business rules validation (only if schema passes)
                if not any(issue["severity"] == "error" for issue in schema_issues):
                    business_issues = self._validate_business_rules(
                        mapped_payload, validation_rules
                    )
                    all_issues.extend(business_issues)

                # Determine outcome
                has_errors = any(issue["severity"] == "error" for issue in all_issues)
                has_warnings = any(issue["severity"] == "warning" for issue in all_issues)

                if has_errors:
                    outcome = "rejected"
                    rejected_count += 1
                elif has_warnings:
                    outcome = "accepted_with_warning"
                    warning_count += 1
                else:
                    outcome = "accepted"
                    accepted_count += 1

                # Create row result
                row_result = self.validation_repo.create_row_result(
                    ingestion_id=ingestion_id,
                    row_number=row_number,
                    target_record_key=mapped_payload.get("site_id"),
                    mapped_payload_json=json.dumps(mapped_payload),
                    outcome=outcome,
                )

                # Create validation issues for this row
                for issue in all_issues:
                    self.validation_repo.create_validation_issue(
                        ingestion_id=ingestion_id,
                        ingestion_row_result_id=row_result.id,
                        issue_scope="row",
                        issue_code=issue["code"],
                        severity=issue["severity"],
                        message=issue["message"],
                        rule_code=issue.get("rule_code"),
                    )

        # Update ingestion summary and transition to completed
        self.validation_repo.update_ingestion_summary(
            ingestion_id=ingestion_id,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            warning_count=warning_count,
        )

        self.ingestion_repo.update_ingestion_status(
            ingestion_id=ingestion_id,
            status="completed",
            validation_completed_at_utc=datetime.now(timezone.utc),
        )

        self.db.commit()

        return {
            "ingestion_id": ingestion_id,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "warning_count": warning_count,
            "status": "completed",
        }

    def _read_excel_rows(
        self, file_data: bytes, mapping_entries: list[MappingEntry]
    ) -> list[dict]:
        """
        Read rows from Excel file.

        Returns:
            List of dictionaries with source column data
        """
        # Load workbook from bytes
        workbook = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
        
        # Get the first sheet
        sheet = workbook.active
        
        # Read header row (first row)
        header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(cell).strip() if cell is not None else f"Column_{i}" 
                   for i, cell in enumerate(header_row, start=1)]
        
        # Read data rows (skip header)
        rows = []
        for row_cells in sheet.iter_rows(min_row=2, values_only=True):
            # Skip empty rows
            if all(cell is None or str(cell).strip() == "" for cell in row_cells):
                continue
                
            # Build row dictionary using headers
            row_dict = {}
            for header, cell in zip(headers, row_cells):
                if cell is not None:
                    # Convert to string and strip whitespace
                    row_dict[header] = str(cell).strip()
            
            if row_dict:  # Only add non-empty rows
                rows.append(row_dict)
        
        return rows

    def _apply_mapping(
        self, source_row: dict, mapping_entries: list[MappingEntry]
    ) -> tuple[dict, list[dict]]:
        """
        Apply mapping entries to source row.

        Returns:
            Tuple of (mapped_payload, mapping_issues)
        """
        mapped_payload = {}
        issues = []

        # Apply each mapping entry
        for entry in mapping_entries:
            source_value = source_row.get(entry.source_column)

            if source_value is None and entry.is_required:
                issues.append({
                    "code": "required_field_missing",
                    "severity": "error",
                    "message": f"Missing required field: {entry.target_field}",
                    "rule_code": None,
                })
            elif source_value is not None:
                mapped_payload[entry.target_field] = source_value

        return mapped_payload, issues

    def _validate_schema(
        self, mapped_payload: dict, mapping_entries: list[MappingEntry]
    ) -> list[dict]:
        """
        Validate schema: type validation per target_type.

        Returns:
            List of schema validation issues
        """
        issues = []

        for entry in mapping_entries:
            field_name = entry.target_field
            field_value = mapped_payload.get(field_name)

            if field_value is None:
                continue

            target_type = entry.target_type

            # Type validation based on target_type
            if target_type == "decimal":
                try:
                    float(field_value)
                except ValueError:
                    issues.append({
                        "code": "invalid_type",
                        "severity": "error",
                        "message": f"Field '{field_name}' must be a decimal number, got: {field_value}",
                        "rule_code": None,
                    })
            elif target_type == "string":
                # String is always valid since we convert everything to string
                pass

        return issues

    def _validate_business_rules(
        self, mapped_payload: dict, validation_rules: list
    ) -> list[dict]:
        """
        Validate business rules.

        Returns:
            List of business validation issues
        """
        issues = []

        for rule in validation_rules:
            # Parse expression_json to get field and validation config
            try:
                expression = json.loads(rule.expression_json)
            except (json.JSONDecodeError, AttributeError):
                continue

            field_name = expression.get("field")
            if not field_name:
                continue

            # Get field value
            field_value = mapped_payload.get(field_name)

            if field_value is None:
                continue

            # Determine rule type from expression content
            # If it has min/max and looks numeric, it's a range rule
            if "min" in expression or "max" in expression:
                try:
                    value_float = float(field_value)
                    min_val = expression.get("min")
                    max_val = expression.get("max")

                    if min_val is not None and value_float < min_val:
                        issues.append({
                            "code": "value_out_of_range",
                            "severity": rule.severity,
                            "message": f"Field '{field_name}' value {value_float} is below minimum {min_val}",
                            "rule_code": rule.rule_code,
                        })
                    elif max_val is not None and value_float > max_val:
                        issues.append({
                            "code": "value_out_of_range",
                            "severity": rule.severity,
                            "message": f"Field '{field_name}' value {value_float} is above maximum {max_val}",
                            "rule_code": rule.rule_code,
                        })
                except ValueError:
                    # Not a valid number, but schema validation should have caught this
                    pass

            # Check for length validation
            elif "min_length" in expression or "max_length" in expression:
                str_value = str(field_value)
                min_len = expression.get("min_length")
                max_len = expression.get("max_length")

                if min_len is not None and len(str_value) < min_len:
                    issues.append({
                        "code": "length_out_of_range",
                        "severity": rule.severity,
                        "message": f"Field '{field_name}' length {len(str_value)} is below minimum {min_len}",
                        "rule_code": rule.rule_code,
                    })
                elif max_len is not None and len(str_value) > max_len:
                    issues.append({
                        "code": "length_out_of_range",
                        "severity": rule.severity,
                        "message": f"Field '{field_name}' length {len(str_value)} is above maximum {max_len}",
                        "rule_code": rule.rule_code,
                    })

            # Check for pattern validation
            elif "pattern" in expression:
                str_value = str(field_value)
                pattern = expression.get("pattern")

                if pattern and not re.match(pattern, str_value):
                    issues.append({
                        "code": "pattern_mismatch",
                        "severity": rule.severity,
                        "message": f"Field '{field_name}' does not match required pattern",
                        "rule_code": rule.rule_code,
                    })

        return issues
