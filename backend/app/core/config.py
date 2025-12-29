# backend/app/core/config.py
import os
from functools import lru_cache
from typing import List, Optional, Any

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application-wide settings.
    
    Uses pydantic-settings to load configuration from environment variables
    and/or a .env file.
    """

    # --- Core Application Settings ---
    PROJECT_NAME: str = "EasyFlow Finance API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str

    # --- CORS Settings ---
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://easyflow-ai-agent-844280192170.us-central1.run.app",
    ]

    # --- Database Settings (PostgreSQL) ---
    SQLALCHEMY_DATABASE_URI: Optional[str] = None  # Changed from PostgresDsn to str

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str) and v:
            return v
        # Build from individual components
        user = os.getenv("POSTGRES_USER", "user")
        password = os.getenv("POSTGRES_PASSWORD", "password")
        host = os.getenv("POSTGRES_HOST", "db")
        db = os.getenv("POSTGRES_DB", "finance_db")
        
        # Handle Cloud SQL Unix socket connections
        if host.startswith("/cloudsql/"):
            return f"postgresql+asyncpg://{user}:{password}@/{db}?host={host}"
        else:
            return f"postgresql+asyncpg://{user}:{password}@{host}/{db}"

    # --- Redis Settings ---
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    @property
    def REDIS_URL(self) -> str:  # Changed from RedisDsn to str
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- Celery (Background Task Queue) Settings ---
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    # --- AI Agent & Other Microservices ---
    AI_AGENT_URL: Optional[AnyHttpUrl] = None

    # --- Third-Party API Keys ---
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_API_VERSION: str = "2023-10"
    STRIPE_API_KEY: Optional[str] = None

    # --- Access Token Settings ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days


    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()