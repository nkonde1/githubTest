# backend/app/core/config.py
"""
Application configuration settings.
"""

import os
import json
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str = "Finance AI Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    ALLOWED_HOSTS: str = "*"  # Will be parsed as list in __init__
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "generate-a-secure-key-for-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")) # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Mobile Money (Zambia)
    MOMO_SUBSCRIPTION_KEY: str = os.getenv("MOMO_SUBSCRIPTION_KEY", "")
    AIRTEL_CLIENT_ID: str = os.getenv("AIRTEL_CLIENT_ID", "")
    AIRTEL_CLIENT_SECRET: str = os.getenv("AIRTEL_CLIENT_SECRET", "")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(levelprefix)s | %(asctime)s | %(message)s")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    JSON_LOGS: bool = os.getenv("JSON_LOGS", "False").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_MAX_RETRIES: int = int(os.getenv("REDIS_MAX_RETRIES", "3"))
    REDIS_RETRY_INTERVAL: int = int(os.getenv("REDIS_RETRY_INTERVAL", "5"))

    # Shopify
    SHOPIFY_ACCESS_TOKEN: str = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
    SHOPIFY_SHOP_DOMAIN: str = os.getenv("SHOPIFY_SHOP_DOMAIN", "")
    SHOPIFY_API_VERSION: str = "2023-10"

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")

    # QuickBooks
    QUICKBOOKS_BASE_URL: str = os.getenv("QUICKBOOKS_BASE_URL", "https://quickbooks.api.intuit.com")
    QUICKBOOKS_ACCESS_TOKEN: str = os.getenv("QUICKBOOKS_ACCESS_TOKEN", "")

    # Sync controls
    MIN_SYNC_INTERVAL: int = int(os.getenv("MIN_SYNC_INTERVAL", "300"))  # seconds between full syncs

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    CELERY_TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"

    # LLAMA Settings
    LLAMA_ENDPOINT: str = os.getenv("LLAMA_ENDPOINT", "http://localhost:11434")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL", "llama3.2")
    LLAMA_MAX_TOKENS: int = int(os.getenv("LLAMA_MAX_TOKENS", "2048"))
    LLAMA_TEMPERATURE: float = float(os.getenv("LLAMA_TEMPERATURE", "0.7"))
    LLAMA_TOP_P: float = float(os.getenv("LLAMA_TOP_P", "0.9"))

    # Session settings
    SESSION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse ALLOWED_HOSTS from string to list
        if self.ALLOWED_HOSTS == "*":
            self._allowed_hosts_list = ["*"]
        else:
            try:
                # Try to parse as JSON first
                self._allowed_hosts_list = json.loads(self.ALLOWED_HOSTS)
            except json.JSONDecodeError:
                # Fall back to comma-separated string
                self._allowed_hosts_list = [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get ALLOWED_HOSTS as a list"""
        return self._allowed_hosts_list

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get async database URI"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    @property
    def has_shopify_config(self) -> bool:
        """Check if Shopify is properly configured"""
        return bool(self.SHOPIFY_ACCESS_TOKEN and self.SHOPIFY_SHOP_DOMAIN)

# Initialize settings
settings = Settings()