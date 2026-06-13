import json
import logging

from app.core.context import correlation_id_ctx
from app.core.enums import Environment
from app.core.settings import settings


class CorrelationIdFilter(logging.Filter):
    """Inject correlation_id, trace_id, and span_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get("") or "-"
        try:
            from opentelemetry import trace

            ctx = trace.get_current_span().get_span_context()
            record.trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else "-"
            record.span_id = format(ctx.span_id, "016x") if ctx.is_valid else "-"
        except Exception:
            record.trace_id = "-"
            record.span_id = "-"
        return True


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for log aggregation (Loki / CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "pid": record.process,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "trace_id": getattr(record, "trace_id", "-"),
            "span_id": getattr(record, "span_id", "-"),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


# Use JSON formatter for non-local environments so logs are machine-parseable.
_is_local = settings.app.environment == Environment.LOCAL
_formatter = "standard" if _is_local else "json"

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": "app.core.logging_config.CorrelationIdFilter",
        },
    },
    "formatters": {
        "standard": {
            "format": "[{asctime}] [{process}] [{levelname}] [{correlation_id}] [{trace_id}] {module}.{funcName}:{lineno} - {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
            "style": "{",
        },
        "json": {
            "()": "app.core.logging_config.JsonFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.app.log_level,
            "formatter": _formatter,
            "filters": ["correlation_id"],
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "level": settings.app.log_level,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": settings.app.log_level,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": settings.app.log_level,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": settings.app.log_level,
            "propagate": False,
        },
    },
}
