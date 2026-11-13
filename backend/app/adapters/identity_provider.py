"""Identity provider adapter."""
import bcrypt
from sqlalchemy.orm import Session

from app.models.auth import User


class IdentityClaims:
    """Identity claims from authentication."""

    def __init__(self, user_id: int, subject_id: str, email: str, display_name: str):
        self.user_id = user_id
        self.subject_id = subject_id
        self.email = email
        self.display_name = display_name


class IdentityProfile:
    """User profile from identity provider."""

    def __init__(self, subject_id: str, email: str, display_name: str, is_active: bool):
        self.subject_id = subject_id
        self.email = email
        self.display_name = display_name
        self.is_active = is_active


class IdentityProviderAdapter:
    """Identity provider adapter for authentication.

    Demo mode: authenticates against seed users with bcrypt-hashed passwords.
    Production mode: would integrate with enterprise SSO or managed identity service.
    """

    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, username: str, password: str) -> IdentityClaims | None:
        """Authenticate user credentials.

        Args:
            username: Username or email
            password: Plain-text password

        Returns:
            IdentityClaims if authentication succeeds, None otherwise
        """
        # Demo mode: authenticate against database users
        user = self.db.query(User).filter(User.email == username, User.is_active).first()

        if not user:
            return None

        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
            return None

        return IdentityClaims(
            user_id=user.id,
            subject_id=user.subject_id,
            email=user.email,
            display_name=user.display_name,
        )

    def get_user_profile(self, subject_id: str) -> IdentityProfile | None:
        """Get user profile by subject ID.

        Args:
            subject_id: Subject ID from identity provider

        Returns:
            IdentityProfile if found, None otherwise
        """
        user = self.db.query(User).filter(User.subject_id == subject_id).first()

        if not user:
            return None

        return IdentityProfile(
            subject_id=user.subject_id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
        )
