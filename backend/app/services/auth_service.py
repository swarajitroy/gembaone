"""Authentication service - enhanced version."""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository
from app.services.audit_service import AuditService

# Simple in-memory rate limiter (will be reset on restart)
_login_attempts: dict[str, list[datetime]] = {}


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthRepository(db)
        self.audit_service = AuditService(db)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, user_id: int, email: str) -> str:
        """Create JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """Create refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=30)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    def hash_token(self, token: str) -> str:
        """Hash token for storage (SHA256 for long tokens, bcrypt for short ones)."""
        # JWT tokens are too long for bcrypt (>72 bytes), so use SHA256 instead
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def decode_token(self, token: str) -> dict:
        """Decode JWT token."""
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        except jwt.InvalidTokenError:
            return {}

    def check_rate_limit(self, identifier: str, max_attempts: int = 5, window_minutes: int = 1) -> bool:
        """Check rate limit for login attempts.

        Returns:
            True if rate limit allows, False if exceeded
        """
        # Check if rate limiting is disabled (for tests)
        if os.environ.get("RATE_LIMIT_ENABLED") == "false":
            return True

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old attempts
        if identifier in _login_attempts:
            _login_attempts[identifier] = [
                attempt for attempt in _login_attempts[identifier]
                if attempt > window_start
            ]

        # Check count
        attempts = _login_attempts.get(identifier, [])
        if len(attempts) >= max_attempts:
            return False

        # Record attempt
        _login_attempts.setdefault(identifier, []).append(now)
        return True

    def login(
        self,
        username: str,
        password: str,
        client_metadata: dict | None,
        correlation_id: str | None,
    ) -> tuple[str, str, User]:
        """Authenticate user and issue tokens.

        Returns:
            Tuple of (access_token, refresh_token, user)
        """
        # Rate limiting
        if not self.check_rate_limit(username):
            self.audit_service.record_event(
                event_type="login_rate_limited",
                actor=None,
                entity_ref=None,
                correlation_id=correlation_id,
                payload={"username": username},
            )
            raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")

        # Authenticate
        user = self.repository.get_active_user_by_email(username)
        if not user or not self.verify_password(password, user.hashed_password):
            self.audit_service.record_event(
                event_type="login_failed",
                actor=None,
                entity_ref=None,
                correlation_id=correlation_id,
                payload={"username": username},
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Issue tokens
        access_token = self.create_access_token(user.id, user.email)
        refresh_token = self.create_refresh_token(user.id)

        # Create session (hash refresh token for storage)
        refresh_token_hash = self.hash_token(refresh_token)
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(days=30)
        client_metadata_json = json.dumps(client_metadata) if client_metadata else None

        self.repository.create_session(
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            client_metadata=client_metadata_json,
        )

        # Audit success
        self.audit_service.record_event(
            event_type="login_success",
            actor=user.id,
            entity_ref=("user", str(user.id)),
            correlation_id=correlation_id,
            payload={"username": username},
        )

        return access_token, refresh_token, user

    def get_user_from_token(self, token: str) -> User | None:
        """Get user from access token."""
        payload = self.decode_token(token)
        if not payload:
            return None

        user_id = int(payload.get("sub", 0))
        if not user_id:
            return None

        return self.repository.get_user_by_id(user_id)
