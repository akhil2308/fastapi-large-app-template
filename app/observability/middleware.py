from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import record_request_end, record_request_start


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to record HTTP request metrics.

    Records:
    - Request count
    - Request duration
    - Error count (5xx responses)
    - In-flight requests (via observable gauge)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record start time and increment in-flight counter
        start = record_request_start()

        # Normalize route to avoid high-cardinality
        # Use scope route path when available, fallback to URL path
        route = None
        try:
            route_obj = request.scope.get("route")
            route = getattr(route_obj, "path", None) or request.url.path
        except Exception:
            route = request.url.path

        try:
            response: Response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            status = 500
            raise
        finally:
            # Ensure route is a stable shape (e.g., "/users/{user_id}")
            safe_route = route if isinstance(route, str) else str(route)
            record_request_end(start, request.method, safe_route, status)
