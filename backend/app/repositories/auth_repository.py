"""Authentication repository."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.auth import User, UserSession


class AuthRepository:
    """Repository for auth operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_active_user_by_email(self, email: str) -> User | None:
        """Get active user by email."""
        return self.db.query(User).filter(User.email == email, User.is_active).first()

    def create_session(
        self,
        user_id: int,
        refresh_token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
        client_metadata: str | None = None,
    ) -> UserSession:
        """Create user session."""
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            issued_at_utc=issued_at,
            expires_at_utc=expires_at,
            last_activity_at_utc=issued_at,
            client_metadata_json=client_metadata,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session_activity(self, session_id: int) -> None:
        """Update session last activity time."""
        self.db.query(UserSession).filter(UserSession.id == session_id).update(
            {"last_activity_at_utc": datetime.now(timezone.utc)}
        )
        self.db.commit()

    def revoke_session(self, session_id: int) -> None:
        """Revoke session."""
        self.db.query(UserSession).filter(UserSession.id == session_id).update(
            {"revoked_at_utc": datetime.now(timezone.utc)}
        )
        self.db.commit()

    def get_session_by_refresh_token_hash(self, token_hash: str) -> UserSession | None:
        """Get session by refresh token hash."""
        return self.db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()
