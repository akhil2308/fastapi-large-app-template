import time
from logging import getLogger

from opentelemetry import metrics

logger = getLogger(__name__)

# Flag to track if metrics have been initialized
_metrics_initialized = False

# Metrics instruments (will be created lazily)
http_requests_counter = None
http_errors_counter = None
http_duration_hist = None
_in_flight = {"v": 0}
_inflight_callback = None
db_query_hist = None
db_query_counter = None
redis_cmd_counter = None
redis_cmd_hist = None
ratelimit_allowed = None
ratelimit_rejected = None
ratelimit_degraded = None
instrumentation_failures = None
todos_created = None
users_registered = None


def create_metrics():
    """
    Create all metric instruments. Must be called AFTER init_telemetry()
    sets the meter provider, otherwise metrics will be NoOp.
    """
    global _metrics_initialized

    # Prevent double initialization
    if _metrics_initialized:
        return

    meter = metrics.get_meter(__name__)

    global http_requests_counter, http_errors_counter, http_duration_hist
    global db_query_hist, db_query_counter
    global redis_cmd_counter, redis_cmd_hist
    global ratelimit_allowed, ratelimit_rejected, ratelimit_degraded
    global instrumentation_failures
    global todos_created, users_registered

    # HTTP metrics
    http_requests_counter = meter.create_counter(
        "app.http.requests_total", description="Total number of HTTP requests"
    )
    http_errors_counter = meter.create_counter(
        "app.http.errors_total", description="Total number of HTTP errors (5xx)"
    )
    http_duration_hist = meter.create_histogram(
        "app.http.request_duration_ms",
        description="HTTP request duration in milliseconds",
        unit="ms",
    )

    # In-flight requests observable (simple in-memory counter)
    def _inflight_callback(options):
        """Callback for observable gauge - returns current in-flight request count."""
        from app.observability.telemetry import get_environment

        yield _in_flight["v"], {"env": get_environment()}

    meter.create_observable_gauge(
        name="app.http.in_flight_requests",
        callbacks=[_inflight_callback],
        description="Current number in-flight HTTP requests",
    )

    # DB metrics
    db_query_hist = meter.create_histogram(
        "app.db.query_duration_ms", description="DB query duration ms", unit="ms"
    )
    db_query_counter = meter.create_counter(
        "app.db.query_count", description="DB queries executed"
    )

    # Redis metrics
    redis_cmd_counter = meter.create_counter(
        "app.redis.commands_total", description="Redis commands executed"
    )
    redis_cmd_hist = meter.create_histogram(
        "app.redis.command_duration_ms",
        description="Redis command duration ms",
        unit="ms",
    )

    # Rate limiter metrics
    ratelimit_allowed = meter.create_counter(
        "app.ratelimiter.allowed_total", description="Rate limiter allowed count"
    )
    ratelimit_rejected = meter.create_counter(
        "app.ratelimiter.rejected_total", description="Rate limiter rejected count"
    )
    ratelimit_degraded = meter.create_counter(
        "app.ratelimiter.degraded_total",
        description="Rate limiter degraded count (Redis failures)",
    )
    instrumentation_failures = meter.create_counter(
        "app.instrumentation.failures_total", description="Instrumentation failures"
    )

    # Business metrics (examples)
    todos_created = meter.create_counter(
        "app.todos.created_total", description="Total todos created"
    )
    users_registered = meter.create_counter(
        "app.users.registered_total", description="Total users registered"
    )

    _metrics_initialized = True


def _get_env() -> str:
    """Get environment label for metrics."""
    from app.observability.telemetry import get_environment

    return get_environment()


def _safe_add(counter, value, labels):
    """Safely add to a counter, catching any exceptions."""
    try:
        if counter is not None:
            counter.add(value, labels)
    except Exception:
        pass  # Never let metrics crash requests


def _safe_record(histogram, value, labels):
    """Safely record to a histogram, catching any exceptions."""
    try:
        if histogram is not None:
            histogram.record(value, labels)
    except Exception:
        pass  # Never let metrics crash requests


# Helpers for HTTP middleware
def record_request_start() -> float:
    """Record the start of an HTTP request and return the start time in nanoseconds."""
    _in_flight["v"] += 1
    return time.time_ns()


def record_request_end(start_ns: float, method: str, route: str, status_code: int):
    """
    Record the end of an HTTP request with duration and status code.

    Args:
        start_ns: Start time in nanoseconds (from record_request_start)
        method: HTTP method (GET, POST, etc.)
        route: Normalized route path (e.g., /users/{user_id})
        status_code: HTTP status code
    """
    duration_ms = (time.time_ns() - start_ns) / 1e6
    labels = {
        "http.method": method,
        "http.route": route,
        "http.status_code": str(status_code),
        "env": _get_env(),
    }

    # Safely record metrics (never let them crash requests)
    _safe_add(http_requests_counter, 1, labels)
    _safe_record(http_duration_hist, duration_ms, labels)
    if status_code >= 500:
        _safe_add(http_errors_counter, 1, labels)

    _in_flight["v"] -= 1


# Helpers for DB
def record_db_query(name: str, duration_ms: float, operation: str = "query"):
    """
    Record a database query execution.

    Args:
        name: Name/statement identifier for the query
        duration_ms: Query duration in milliseconds
        operation: Type of operation (select, insert, update, delete)
    """
    labels = {
        "db.system": "postgresql",
        "db.statement_name": name,
        "db.operation": operation,
        "env": _get_env(),
    }
    _safe_record(db_query_hist, duration_ms, labels)
    _safe_add(db_query_counter, 1, labels)


# Helpers for Redis
def record_redis_command(command: str, duration_ms: float):
    """
    Record a Redis command execution.

    Args:
        command: Redis command name (GET, SET, etc.)
        duration_ms: Command duration in milliseconds
    """
    labels = {"redis.command": command.upper(), "env": _get_env()}
    _safe_add(redis_cmd_counter, 1, labels)
    _safe_record(redis_cmd_hist, duration_ms, labels)


# Helpers for rate limiter
def record_ratelimit_decision(allowed: bool, service: str):
    """
    Record a rate limiter decision.

    Args:
        allowed: True if request was allowed, False if rejected
        service: Service name for the rate limit bucket
    """
    labels = {"service": service, "env": _get_env()}
    if allowed:
        _safe_add(ratelimit_allowed, 1, labels)
    else:
        _safe_add(ratelimit_rejected, 1, labels)


def record_ratelimit_degraded(service: str):
    """
    Record rate limiter fail-open (Redis unavailable).

    Args:
        service: Service name for the rate limit bucket
    """
    labels = {"service": service, "env": _get_env()}
    _safe_add(ratelimit_degraded, 1, labels)


def record_instrumentation_failure(component: str):
    """
    Record instrumentation failure for a component.

    Args:
        component: Name of the component (e.g., 'sqlalchemy', 'redis')
    """
    labels = {"component": component, "env": _get_env()}
    _safe_add(instrumentation_failures, 1, labels)
