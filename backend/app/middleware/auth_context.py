"""Authentication context middleware."""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
from app.services.auth_service import AuthService

security = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from bearer token.

    Use this as a dependency in protected routes:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials

    auth_service = AuthService(db)
    user = auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


def get_correlation_id(request: Request) -> str | None:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)
