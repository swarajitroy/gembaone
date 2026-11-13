"""Validation repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ingestion import IngestionRowResult, ValidationIssue
from app.models.validation import ValidationRule, ValidationRuleSet


class ValidationRepository:
    """Repository for validation operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_rule_set_by_id(self, rule_set_id: int) -> ValidationRuleSet | None:
        """Get validation rule set by ID."""
        return (
            self.db.query(ValidationRuleSet)
            .filter(ValidationRuleSet.id == rule_set_id)
            .first()
        )

    def get_rule_set_by_code(self, rule_set_code: str) -> ValidationRuleSet | None:
        """Get validation rule set by code."""
        return (
            self.db.query(ValidationRuleSet)
            .filter(ValidationRuleSet.rule_set_code == rule_set_code)
            .first()
        )

    def get_rules_by_rule_set_id(self, rule_set_id: int) -> list[ValidationRule]:
        """Get validation rules by rule set ID, ordered by sort_order."""
        return (
            self.db.query(ValidationRule)
            .filter(ValidationRule.rule_set_id == rule_set_id)
            .order_by(ValidationRule.sort_order)
            .all()
        )

    def create_row_result(
        self,
        ingestion_id: int,
        row_number: int,
        target_record_key: str | None,
        mapped_payload_json: str | None,
        outcome: str,
    ) -> IngestionRowResult:
        """Create ingestion row result."""
        row_result = IngestionRowResult(
            ingestion_id=ingestion_id,
            row_number=row_number,
            target_record_key=target_record_key,
            mapped_payload_json=mapped_payload_json,
            outcome=outcome,
            created_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(row_result)
        self.db.flush()
        return row_result

    def create_validation_issue(
        self,
        ingestion_id: int,
        ingestion_row_result_id: int | None,
        issue_scope: str,
        issue_code: str,
        severity: str,
        message: str,
        rule_code: str | None,
    ) -> ValidationIssue:
        """Create validation issue."""
        issue = ValidationIssue(
            ingestion_id=ingestion_id,
            ingestion_row_result_id=ingestion_row_result_id,
            issue_scope=issue_scope,
            issue_code=issue_code,
            severity=severity,
            message=message,
            rule_code=rule_code,
            created_at_utc=datetime.now(timezone.utc),
        )
        self.db.add(issue)
        self.db.flush()
        return issue

    def get_row_results_by_ingestion_id(
        self, ingestion_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[list[IngestionRowResult], int]:
        """Get paginated row results by ingestion ID."""
        query = self.db.query(IngestionRowResult).filter(
            IngestionRowResult.ingestion_id == ingestion_id
        )
        total = query.count()
        results = query.order_by(IngestionRowResult.row_number).offset(offset).limit(limit).all()
        return results, total

    def get_issues_by_row_result_id(self, row_result_id: int) -> list[ValidationIssue]:
        """Get validation issues by row result ID."""
        return (
            self.db.query(ValidationIssue)
            .filter(ValidationIssue.ingestion_row_result_id == row_result_id)
            .order_by(ValidationIssue.created_at_utc)
            .all()
        )

    def update_ingestion_summary(
        self,
        ingestion_id: int,
        accepted_count: int,
        rejected_count: int,
        warning_count: int,
    ) -> None:
        """Update ingestion summary counts."""
        from app.models.ingestion import IngestionRecord

        ingestion = (
            self.db.query(IngestionRecord)
            .filter(IngestionRecord.id == ingestion_id)
            .first()
        )
        if ingestion:
            ingestion.accepted_count = accepted_count
            ingestion.rejected_count = rejected_count
            ingestion.warning_count = warning_count
            self.db.flush()
