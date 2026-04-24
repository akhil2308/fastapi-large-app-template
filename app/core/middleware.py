import uuid

from fastapi import Request

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.context import correlation_id_ctx


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Read or generate a correlation ID and echo it on the response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id_ctx.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
