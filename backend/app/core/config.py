from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_WEAK_SECRETS = frozenset(
    {
        "change-me",
        "changeme",
        "secret",
        "jwt_secret",
        "your-secret-here",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    MIGRATION_DATABASE_URL: str
    JWT_SECRET: str
    CORS_ORIGINS: str
    max_body_bytes: int = 1_000_000
    max_upload_bytes: int = 1_000_000
    request_timeout_seconds: float = 30
    max_page_size: int = 100
    PRODUCT_IMAGES_DIR: str = "var/product-images"
    PROFILE_IMAGES_DIR: str = "var/profile-images"
    LOG_FILE: str = "var/logs/app.log"

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_strong(cls, value: str) -> str:
        secret = value.strip()
        if len(secret) < 32 or secret.lower() in _WEAK_SECRETS:
            raise ValueError("JWT_SECRET demasiado débil")
        return secret

    @property
    def cors_origin_list(self) -> list[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
