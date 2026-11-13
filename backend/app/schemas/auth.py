"""Authentication schemas."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    client_metadata: dict | None = None


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    subject_id: str
    display_name: str
    email: str
    role_codes: list[str]
    is_asp: bool
    is_active: bool
    created_at_utc: str
    updated_at_utc: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse
