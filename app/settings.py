import os
from decouple import Csv, config
from urllib.parse import quote_plus

# Core Settings
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# MySQL config
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT'))
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD' )
POSTGRES_NAME = os.getenv('POSTGRES_NAME')
POSTGRES_POOL_SIZE = config('POSTGRES_POOL_SIZE', default=5, cast=int)
POSTGRES_MAX_OVERFLOW = config('POSTGRES_MAX_OVERFLOW', default=10, cast=int)


JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES'))

# AWS Config
OPEN_API_KEY = os.getenv('OPEN_API_KEY')
OPEN_API_MODEL = os.getenv('OPEN_API_MODEL')

# Logging Configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] [{process}] [{levelname}] {module}.{funcName}:{lineno} - {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",  # Note: this handler will only emit INFO and higher messages.
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # The root logger; using an empty string "" applies it to all modules
        "": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
    },
}