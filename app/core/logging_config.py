from app.core.settings import CoreConfig

# Logging Configuration
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] [{process}] [{levelname}] {module}.{funcName}:{lineno} - {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": CoreConfig.LOG_LEVEL,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # The root logger; using an empty string "" applies it to all modules
        "": {"level": CoreConfig.LOG_LEVEL, "handlers": ["console"], "propagate": False},
        # Explicitly override Uvicorn loggers
        "uvicorn": {"handlers": ["console"], "level": CoreConfig.LOG_LEVEL, "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": CoreConfig.LOG_LEVEL, "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": CoreConfig.LOG_LEVEL, "propagate": False}
    },
}