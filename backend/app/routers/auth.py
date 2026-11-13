"""Authentication router."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_context import get_correlation_id, get_current_user
from app.models.auth import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login endpoint with rate limiting and audit logging."""
    correlation_id = get_correlation_id(request)

    auth_service = AuthService(db)
    permission_service = PermissionService(db)

    # Authenticate and issue tokens
    access_token, refresh_token, user = auth_service.login(
        username=request_data.email,
        password=request_data.password,
        client_metadata=None,
        correlation_id=correlation_id,
    )

    # Get user roles
    role_codes = permission_service.get_user_roles(user.id)

    # Build user response
    user_response = UserResponse(
        id=user.id,
        subject_id=user.subject_id,
        display_name=user.display_name,
        email=user.email,
        role_codes=role_codes,
        is_asp="asp_user" in role_codes,
        is_active=user.is_active,
        created_at_utc=user.created_at_utc.isoformat(),
        updated_at_utc=user.updated_at_utc.isoformat(),
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=1440 * 60,  # 1440 minutes in seconds
        user=user_response,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user information."""
    permission_service = PermissionService(db)

    # Get user roles
    role_codes = permission_service.get_user_roles(user.id)

    return UserResponse(
        id=user.id,
        subject_id=user.subject_id,
        display_name=user.display_name,
        email=user.email,
        role_codes=role_codes,
        is_asp="asp_user" in role_codes,
        is_active=user.is_active,
        created_at_utc=user.created_at_utc.isoformat(),
        updated_at_utc=user.updated_at_utc.isoformat(),
    )
