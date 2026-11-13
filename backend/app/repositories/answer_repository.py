"""Answer repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.checklist import ChecklistAnswer


class AnswerRepository:
    """Repository for checklist answer operations."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_answer(
        self,
        checklist_instance_item_id: int,
        value_type: str,
        value_text: str | None,
        value_number: float | None,
        value_boolean: bool | None,
        value_date: datetime | None,
        value_json: str | None,
        answered_by_user_id: int,
    ) -> ChecklistAnswer:
        """Upsert answer for checklist instance item.

        Updates existing answer or creates new one.
        """
        # Check if answer exists
        existing = self.db.query(ChecklistAnswer).filter(
            ChecklistAnswer.checklist_instance_item_id == checklist_instance_item_id
        ).first()

        if existing:
            # Update existing answer
            existing.value_type = value_type
            existing.value_text = value_text
            existing.value_number = value_number
            existing.value_boolean = value_boolean
            existing.value_date = value_date
            existing.value_json = value_json
            existing.answered_by_user_id = answered_by_user_id
            existing.answered_at_utc = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new answer
            answer = ChecklistAnswer(
                checklist_instance_item_id=checklist_instance_item_id,
                value_type=value_type,
                value_text=value_text,
                value_number=value_number,
                value_boolean=value_boolean,
                value_date=value_date,
                value_json=value_json,
                answered_by_user_id=answered_by_user_id,
                answered_at_utc=datetime.now(timezone.utc),
            )
            self.db.add(answer)
            self.db.commit()
            self.db.refresh(answer)
            return answer

    def get_answers_by_instance(self, instance_id: int) -> list[ChecklistAnswer]:
        """Get all answers for checklist instance."""
        from app.models.checklist import ChecklistInstanceItem

        return (
            self.db.query(ChecklistAnswer)
            .join(ChecklistInstanceItem, ChecklistAnswer.checklist_instance_item_id == ChecklistInstanceItem.id)
            .filter(ChecklistInstanceItem.checklist_instance_id == instance_id)
            .all()
        )

    def get_answer_by_item_key(self, instance_id: int, item_key: str) -> ChecklistAnswer | None:
        """Get answer by instance and item key."""
        from app.models.checklist import ChecklistInstanceItem

        return (
            self.db.query(ChecklistAnswer)
            .join(ChecklistInstanceItem, ChecklistAnswer.checklist_instance_item_id == ChecklistInstanceItem.id)
            .filter(
                ChecklistInstanceItem.checklist_instance_id == instance_id,
                ChecklistInstanceItem.item_key == item_key
            )
            .first()
        )
