"""Permission service."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import Role, User, UserRole


class PermissionService:
    """Service for permission enforcement."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_roles(self, user_id: int) -> list[str]:
        """Get user role codes."""
        user_roles = (
            self.db.query(Role.role_code)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return [r[0] for r in user_roles]

    def require_permission(self, user: User, permission_code: str) -> None:
        """Require user to have permission (role-based check)."""
        role_codes = self.get_user_roles(user.id)

        # Map permissions to roles
        permission_map = {
            "template_management": ["internal_admin"],
            "checklist_creation": ["internal_admin", "field_engineer"],
            "checklist_submission": ["internal_admin", "field_engineer"],
            "checklist_review": ["internal_admin", "reviewer"],
            "ingestion_upload": ["internal_admin", "asp_user"],
            "ingestion_view": ["internal_admin", "asp_user"],
            "mapping_management": ["internal_admin"],
        }

        allowed_roles = permission_map.get(permission_code, [])
        if not any(role in role_codes for role in allowed_roles):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission_code}")

    def enforce_ingestion_visibility(self, user: User, ingestion_id: int) -> None:
        """Enforce ingestion visibility rules (ASP users see only own records)."""
        from app.repositories.ingestion_repository import IngestionRepository

        role_codes = self.get_user_roles(user.id)

        # Internal admins can see all
        if "internal_admin" in role_codes:
            return

        # ASP users can only see their own ingestions
        if "asp_user" in role_codes:
            repository = IngestionRepository(self.db)
            ingestion = repository.get_ingestion_by_id(ingestion_id)
            if not ingestion:
                raise HTTPException(status_code=404, detail="Ingestion not found")
            if ingestion.uploaded_by_user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied to this ingestion")

    def enforce_checklist_visibility(self, user: User, checklist_id: int) -> None:
        """Enforce checklist visibility rules."""
        role_codes = self.get_user_roles(user.id)

        # Internal admins, field engineers, and reviewers can see all checklists
        if any(role in role_codes for role in ["internal_admin", "field_engineer", "reviewer"]):
            return

        # ASP users cannot access checklists
        raise HTTPException(status_code=403, detail="Access denied to checklist")

    def deny_delete_for_asp(self, user: User) -> None:
        """Deny delete operations for ASP users."""
        role_codes = self.get_user_roles(user.id)
        if "asp_user" in role_codes:
            raise HTTPException(status_code=403, detail="Delete operations not allowed for ASP users")
