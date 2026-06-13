from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import Environment

_ENV_FILE = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8", extra="ignore"
)

_DEFAULT_LOG_LEVELS = {
    Environment.LOCAL: "DEBUG",
    Environment.DEV: "DEBUG",
    Environment.STAGE: "INFO",
    Environment.PROD: "WARNING",
}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# APP CONFIGURATION
class AppSettings(BaseSettings):
    model_config = _ENV_FILE

    env: str = "local"
    # None means "infer from environment" for both of these.
    debug: bool | None = None
    log_level: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def environment(self) -> Environment:
        return Environment.from_string(self.env)

    @model_validator(mode="after")
    def _infer_from_env(self) -> "AppSettings":
        if self.debug is None:
            self.debug = self.environment in (Environment.LOCAL, Environment.DEV)
        if self.log_level is None:
            self.log_level = _DEFAULT_LOG_LEVELS.get(self.environment, "INFO")
        else:
            self.log_level = self.log_level.upper()
        return self


# CORE SETTINGS
class CoreSettings(BaseSettings):
    model_config = _ENV_FILE

    # Stored as raw CSV strings; pydantic would otherwise JSON-decode list fields from env.
    allowed_hosts_raw: str = Field(
        "127.0.0.1,localhost", validation_alias="ALLOWED_HOSTS"
    )
    cors_origins_raw: str = Field(
        "http://localhost:3000,http://localhost:8000", validation_alias="CORS_ORIGINS"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_hosts(self) -> list[str]:
        return _split_csv(self.allowed_hosts_raw)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return _split_csv(self.cors_origins_raw)


# DATABASE SETTINGS
class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", **_ENV_FILE)

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "password"
    name: str = "postgres"

    pool_size: int = 5
    max_overflow: int = 10

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


# JWT / AUTH SETTINGS
class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_", **_ENV_FILE)

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


# REDIS SETTINGS
class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", **_ENV_FILE)

    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0

    max_connections: int = 10
    connection_timeout: int = 5
    health_check_interval: int = 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


# RATE LIMIT SETTINGS
class RateLimitSettings(BaseSettings):
    model_config = _ENV_FILE

    read_per_min: int = Field(60, validation_alias="READ_RATE_LIMITING_PER_MIN")
    write_per_min: int = Field(10, validation_alias="WRITE_RATE_LIMITING_PER_MIN")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app: AppSettings = Field(default_factory=AppSettings)
    core: CoreSettings = Field(default_factory=CoreSettings)
    db: DBSettings = Field(default_factory=DBSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)  # type: ignore[arg-type]
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    @model_validator(mode="after")
    def _reject_wildcard_cors_in_prod(self) -> "Settings":
        is_wildcard = "*" in self.core.cors_origins
        if is_wildcard and self.app.environment == Environment.PROD:
            raise ValueError(
                "CORS_ORIGINS may not be '*' when credentials are enabled in prod. "
                "Set CORS_ORIGINS to an explicit list of allowed origins."
            )
        return self


settings = Settings()
