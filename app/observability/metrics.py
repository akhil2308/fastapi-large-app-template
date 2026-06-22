from logging import getLogger

from opentelemetry import metrics
from opentelemetry.metrics import Counter

logger = getLogger(__name__)


class _Instruments:
    """Holds all OTel metric instruments; populated once by create_metrics()."""

    ratelimit_allowed: Counter | None = None
    ratelimit_rejected: Counter | None = None
    ratelimit_degraded: Counter | None = None
    instrumentation_failures: Counter | None = None
    todos_created: Counter | None = None
    users_registered: Counter | None = None


_m = _Instruments()


def create_metrics():
    """Create all metric instruments — must be called after init_telemetry()."""
    if _m.ratelimit_allowed is not None:
        return

    meter = metrics.get_meter(__name__)

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
