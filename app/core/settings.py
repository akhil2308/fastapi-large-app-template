import os

from decouple import Csv, config
from dotenv import load_dotenv

from app.core.enums import Environment

# quote_plus can be used to encode the password in the connection string (to not have issues with special characters)
# from urllib.parse import quote_plus

# loads envs in .env file
load_dotenv()


# APP CONFIGURATION
class AppConfig:
    """
    Application-level configuration including environment and debug settings.

    Environment is determined by ENV env var (default: local)
    DEBUG can be explicitly set via DEBUG env var or inferred from environment.
    """

    # Environment configuration
    ENV = os.getenv("ENV", "local").lower()
    ENVIRONMENT = Environment.from_string(ENV)

    # Debug configuration
    # Priority: Explicit DEBUG env var > Environment inference
    _explicit_debug = os.getenv("DEBUG", "").lower()

    if _explicit_debug in ("true", "1", "yes"):
        DEBUG = True
    elif _explicit_debug in ("false", "0", "no"):
        DEBUG = False
    else:
        # Infer from environment
        DEBUG = ENVIRONMENT in (Environment.LOCAL, Environment.DEV)

    # Logging level - can be overridden via LOG_LEVEL env var
    # Default varies by environment when not explicitly set
    _explicit_log_level = os.getenv("LOG_LEVEL", "")

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
    HOST = os.getenv("POSTGRES_HOST", "localhost")
    PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    USER = os.getenv("POSTGRES_USER", "postgres")
    PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    NAME = os.getenv("POSTGRES_NAME", "postgres")

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
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


# REDIS SETTINGS
class RedisConfig:
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", "6379"))
    PASSWORD = os.getenv("REDIS_PASSWORD")
    DB = int(os.getenv("REDIS_DB", "0"))

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


# OPENAI SETTINGS
class OpenAIConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
