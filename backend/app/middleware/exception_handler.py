"""Global exception handler middleware."""
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for global exception handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions and return standardized error responses."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Get correlation ID if available
            correlation_id = getattr(request.state, "correlation_id", None)

            # Log exception
            logger.error(
                "Unhandled exception",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                },
                exc_info=True,
            )

            # Return standardized error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "correlation_id": correlation_id,
                },
            )
