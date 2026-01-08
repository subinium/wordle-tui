from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/wordle"
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"
    environment: str = "development"

    # GitHub OAuth (optional - for device flow login)
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None

    # Admin API (set a strong secret key!)
    admin_secret_key: str = "change-this-admin-secret-key"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
