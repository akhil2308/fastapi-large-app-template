import os
from decouple import Csv, config

# quote_plus can be used to encode the password in the connection string (to not have issues with special characters)
# from urllib.parse import quote_plus 

# Core Settings
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
CORS_ORIGINS = config("CORS_ORIGINS", default="*", cast=Csv())

# MySQL config
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT'))
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD' )
POSTGRES_NAME = os.getenv('POSTGRES_NAME')
POSTGRES_POOL_SIZE = config('POSTGRES_POOL_SIZE', default=5, cast=int)
POSTGRES_MAX_OVERFLOW = config('POSTGRES_MAX_OVERFLOW', default=10, cast=int)

# JWT Config
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES'))

# Redis Config
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_DB = os.getenv('REDIS_DB')
REDIS_MAX_CONNECTIONS = config('REDIS_MAX_CONNECTIONS', default=10, cast=int)
REDIS_CONNECTION_TIMEOUT = config('REDIS_CONNECTION_TIMEOUT', default=5, cast=int)
REDIS_HEALTH_CHECK_INTERVAL = config('REDIS_HEALTH_CHECK_INTERVAL', default=30, cast=int)

# Rate Limiter Config
READ_RATE_LIMITING_PER_MIN = config('READ_RATE_LIMITING_PER_MIN', default=60, cast=int)
WRITE_RATE_LIMITING_PER_MIN = config('WRITE_RATE_LIMITING_PER_MIN', default=10, cast=int)

# OPENAI Config
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_MODEL = os.getenv('OPENAI_API_MODEL')


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
        # Explicitly override Uvicorn loggers
        "uvicorn": {"handlers": ["console"],"level": "INFO","propagate": False},
        "uvicorn.access": {"handlers": ["console"],"level": "INFO","propagate": False},
        "uvicorn.error": {"handlers": ["console"],"level": "INFO","propagate": False}
    },
}