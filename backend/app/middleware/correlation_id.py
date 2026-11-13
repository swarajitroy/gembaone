"""Correlation ID middleware."""
import secrets
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate correlation IDs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Generate correlation ID and add to request state and response headers."""
        # Generate correlation ID
        correlation_id = f"corr-{secrets.token_hex(4)}"

        # Add to request state
        request.state.correlation_id = correlation_id

        # Call next middleware/route
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def get_correlation_id(request: Request) -> str | None:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)
