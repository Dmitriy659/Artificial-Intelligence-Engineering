import logging
from pathlib import Path

import pydantic
import pydantic_settings

BASE_DIR = Path(__file__).resolve().parents[2]


class BaseSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=BASE_DIR / "configs" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )


class LoggerSettings(BaseSettings):
    LOG_LEVEL: str = pydantic.Field(default=logging.getLevelName(logging.DEBUG))

    @pydantic.field_validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed_values = set(logging.getLevelNamesMapping())
        if v in allowed_values:
            return v
        raise ValueError(f"Invalid status {v}. Must be one of {sorted(allowed_values)}")


class UvicornSettings(BaseSettings):
    HOST: str = pydantic.Field(default="0.0.0.0", alias="HOST")
    PORT: pydantic.PositiveInt = pydantic.Field(default=80, alias="PORT")


class DatabaseSettings(BaseSettings):
    DATABASE_URL: pydantic.PostgresDsn

    @property
    def get_database_url_str(self):
        return str(self.DATABASE_URL)


class SecuritySettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str


class S3Settings(BaseSettings):
    AWS_KEY_ID: str
    AWS_SECRET_KEY: str
    REGION: str
    S3_URL: str
    S3_BUCKET: str
