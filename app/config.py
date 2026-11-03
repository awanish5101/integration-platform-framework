"""
Application configuration for the Integration Platform Framework.
"""
import os
from pydantic import BaseModel
from typing import Optional


class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "Integration Platform Framework")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.4.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    API_V2_PREFIX: str = os.getenv("API_V2_PREFIX", "/api/v2")
    
    # Platform Limits & Zero KTLO Defaults
    RATE_LIMIT_DEFAULT_RPM: int = int(os.getenv("RATE_LIMIT_DEFAULT_RPM", "600"))
    RATE_LIMIT_BURST_CAPACITY: int = int(os.getenv("RATE_LIMIT_BURST_CAPACITY", "50"))
    IDEMPOTENCY_TTL_SECONDS: int = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "86400"))
    
    # Webhook & DLQ Resilience
    WEBHOOK_MAX_RETRIES: int = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
    WEBHOOK_BACKOFF_BASE_SECONDS: float = float(os.getenv("WEBHOOK_BACKOFF_BASE_SECONDS", "0.5"))
    WEBHOOK_TIMEOUT_SECONDS: float = float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "5.0"))
    
    # Observability
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
