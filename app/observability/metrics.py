from logging import getLogger

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram

logger = getLogger(__name__)


class _Instruments:
    """Holds all OTel metric instruments; populated once by create_metrics()."""

    db_query_hist: Histogram | None = None
    db_query_counter: Counter | None = None
    redis_cmd_counter: Counter | None = None
    redis_cmd_hist: Histogram | None = None
    ratelimit_allowed: Counter | None = None
    ratelimit_rejected: Counter | None = None
    ratelimit_degraded: Counter | None = None
    instrumentation_failures: Counter | None = None
    todos_created: Counter | None = None
    users_registered: Counter | None = None


_m = _Instruments()


def create_metrics():
    """Create all metric instruments — must be called after init_telemetry()."""
    if _m.db_query_hist is not None:
        return

    meter = metrics.get_meter(__name__)

    _m.db_query_hist = meter.create_histogram(
        "app.db.query_duration_ms", description="DB query duration ms", unit="ms"
    )
    _m.db_query_counter = meter.create_counter(
        "app.db.query_count", description="DB queries executed"
    )
    _m.redis_cmd_counter = meter.create_counter(
        "app.redis.commands_total", description="Redis commands executed"
    )
    _m.redis_cmd_hist = meter.create_histogram(
        "app.redis.command_duration_ms",
        description="Redis command duration ms",
        unit="ms",
    )
    _m.ratelimit_allowed = meter.create_counter(
        "app.ratelimiter.allowed_total", description="Rate limiter allowed count"
    )
    _m.ratelimit_rejected = meter.create_counter(
        "app.ratelimiter.rejected_total", description="Rate limiter rejected count"
    )
    _m.ratelimit_degraded = meter.create_counter(
        "app.ratelimiter.degraded_total",
        description="Rate limiter degraded count (Redis failures)",
    )
    _m.instrumentation_failures = meter.create_counter(
        "app.instrumentation.failures_total", description="Instrumentation failures"
    )
    _m.todos_created = meter.create_counter(
        "app.todos.created_total", description="Total todos created"
    )
    _m.users_registered = meter.create_counter(
        "app.users.registered_total", description="Total users registered"
    )


def _safe_add(counter, value, labels):
    try:
        if counter is not None:
            counter.add(value, labels)
    except Exception:
        pass  # never let metrics crash requests


def _safe_record(histogram, value, labels):
    try:
        if histogram is not None:
            histogram.record(value, labels)
    except Exception:
        pass  # never let metrics crash requests


def record_db_query(name: str, duration_ms: float, operation: str = "query"):
    labels = {
        "db.system": "postgresql",
        "db.statement_name": name,
        "db.operation": operation,
    }
    _safe_record(_m.db_query_hist, duration_ms, labels)
    _safe_add(_m.db_query_counter, 1, labels)


def record_redis_command(command: str, duration_ms: float):
    labels = {"redis.command": command.upper()}
    _safe_add(_m.redis_cmd_counter, 1, labels)
    _safe_record(_m.redis_cmd_hist, duration_ms, labels)


def record_ratelimit_decision(allowed: bool, service: str):
    labels = {"ratelimit_service": service}
    if allowed:
        _safe_add(_m.ratelimit_allowed, 1, labels)
    else:
        _safe_add(_m.ratelimit_rejected, 1, labels)


def record_ratelimit_degraded(service: str):
    labels = {"ratelimit_service": service}
    _safe_add(_m.ratelimit_degraded, 1, labels)


def record_instrumentation_failure(component: str):
    labels = {"component": component}
    _safe_add(_m.instrumentation_failures, 1, labels)


def record_todo_created(user_id: str):
    _safe_add(_m.todos_created, 1, {"user_id": user_id})


def record_user_registered():
    _safe_add(_m.users_registered, 1, {})
