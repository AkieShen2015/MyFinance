from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Personal Finance Analytics API"
    app_env: str = "development"
    app_secret_key: str = Field(default="development-only-change-me-please", min_length=32)
    database_url: str = "sqlite:///./finance.db"
    frontend_origin: str = "http://localhost:5173"
    session_cookie_secure: bool = False
    demo_user_email: str = "demo@example.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
