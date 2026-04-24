from decouple import Csv, config

from app.core.enums import Environment


# APP CONFIGURATION
class AppConfig:
    """
    Application-level configuration including environment and debug settings.

    Environment is determined by ENV env var (default: local)
    DEBUG can be explicitly set via DEBUG env var or inferred from environment.
    """

    # Environment configuration
    ENV = config("ENV", default="local").lower()
    ENVIRONMENT = Environment.from_string(ENV)

    # Debug configuration
    # Priority: Explicit DEBUG env var > Environment inference
    _explicit_debug = config("DEBUG", default="").lower()

    if _explicit_debug in ("true", "1", "yes"):
        DEBUG = True
    elif _explicit_debug in ("false", "0", "no"):
        DEBUG = False
    else:
        # Infer from environment
        DEBUG = ENVIRONMENT in (Environment.LOCAL, Environment.DEV)

    # Logging level - can be overridden via LOG_LEVEL env var
    # Default varies by environment when not explicitly set
    _explicit_log_level = config("LOG_LEVEL", default="")

    if _explicit_log_level:
        LOG_LEVEL = _explicit_log_level.upper()
    else:
        # Default LOG_LEVEL based on environment
        DEFAULT_LOG_LEVELS = {
            Environment.LOCAL: "DEBUG",
            Environment.DEV: "DEBUG",
            Environment.STAGE: "INFO",
            Environment.PROD: "WARNING",
        }
        LOG_LEVEL = DEFAULT_LOG_LEVELS.get(ENVIRONMENT, "INFO")


# CORE SETTINGS
class CoreConfig:
    ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
    CORS_ORIGINS = config(
        "CORS_ORIGINS",
        default="http://localhost:3000,http://localhost:8000",
        cast=Csv(),
    )
    # Use LOG_LEVEL from AppConfig
    LOG_LEVEL = AppConfig.LOG_LEVEL


# DATABASE SETTINGS
class DBConfig:
    HOST = config("POSTGRES_HOST", default="localhost")
    PORT = config("POSTGRES_PORT", default=5432, cast=int)
    USER = config("POSTGRES_USER", default="postgres")
    PASSWORD = config("POSTGRES_PASSWORD", default="password")
    NAME = config("POSTGRES_NAME", default="postgres")

    POOL_SIZE = config("POSTGRES_POOL_SIZE", default=5, cast=int)
    MAX_OVERFLOW = config("POSTGRES_MAX_OVERFLOW", default=10, cast=int)

    # Async URL (app runtime)
    ASYNC_URL = (f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}").rstrip(
        "/"
    )

    # Sync URL (alembic migrations)
    SYNC_URL = (f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}").rstrip(
        "/"
    )


# JWT / AUTH SETTINGS
class JWTConfig:
    SECRET_KEY = config("JWT_SECRET_KEY", default=None)
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set")
    ALGORITHM = config("JWT_ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MIN = config("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)


# REDIS SETTINGS
class RedisConfig:
    HOST = config("REDIS_HOST", default="localhost")
    PORT = config("REDIS_PORT", default=6379, cast=int)
    PASSWORD = config("REDIS_PASSWORD", default=None)
    DB = config("REDIS_DB", default=0, cast=int)

    MAX_CONNECTIONS = config("REDIS_MAX_CONNECTIONS", default=10, cast=int)
    CONNECTION_TIMEOUT = config("REDIS_CONNECTION_TIMEOUT", default=5, cast=int)
    HEALTH_CHECK_INTERVAL = config("REDIS_HEALTH_CHECK_INTERVAL", default=30, cast=int)

    URL = (
        f"redis://:{PASSWORD}@{HOST}:{PORT}/{DB}"
        if PASSWORD
        else f"redis://{HOST}:{PORT}/{DB}"
    )


# RATE LIMIT SETTINGS
class RateLimitConfig:
    READ_PER_MIN = config("READ_RATE_LIMITING_PER_MIN", default=60, cast=int)
    WRITE_PER_MIN = config("WRITE_RATE_LIMITING_PER_MIN", default=10, cast=int)

