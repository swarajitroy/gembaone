"""Common schemas."""
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail schema."""
    detail: str
    status_code: int = 400
