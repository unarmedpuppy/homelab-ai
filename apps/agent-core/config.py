"""
Configuration management for Agent Core.

Loads settings from environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Local AI Router connection
    local_ai_url: str = os.getenv("LOCAL_AI_URL", "http://local-ai-router:8000")
    local_ai_api_key: str = os.getenv("LOCAL_AI_API_KEY", "")
    
    # Service configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
