from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/wordle"
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"
    environment: str = "development"

    # Google OAuth (for localhost redirect login)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Admin settings
    admin_secret_key: str = "change-this-admin-secret-key"
    admin_emails: str = ""  # Comma-separated admin emails (e.g., "admin@gmail.com,user@gmail.com")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
