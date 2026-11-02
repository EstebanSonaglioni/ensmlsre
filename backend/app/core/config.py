from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    MIGRATION_DATABASE_URL: str
    JWT_SECRET: str
    CORS_ORIGINS: str
    max_body_bytes: int = 1_000_000
    request_timeout_seconds: float = 30
    max_page_size: int = 100
    PRODUCT_IMAGES_DIR: str = "var/product-images"
    PROFILE_IMAGES_DIR: str = "var/profile-images"
    LOG_FILE: str = "var/logs/app.log"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
