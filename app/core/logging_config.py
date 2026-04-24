import logging

from app.core.context import correlation_id_ctx
from app.core.settings import CoreConfig


class CorrelationIdFilter(logging.Filter):
    """Inject correlation_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get("") or "-"
        return True


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
            "format": "[{asctime}] [{process}] [{levelname}] [{correlation_id}] {module}.{funcName}:{lineno} - {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": CoreConfig.LOG_LEVEL,
            "formatter": "standard",
            "filters": ["correlation_id"],
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "level": CoreConfig.LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": CoreConfig.LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": CoreConfig.LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": CoreConfig.LOG_LEVEL,
            "propagate": False,
        },
    },
}
