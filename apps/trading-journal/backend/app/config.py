"""
Configuration management for Trading Journal backend.

Uses Pydantic Settings for environment variable management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import cached_property


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # API Configuration
    api_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # External API Keys
    alpha_vantage_api_key: str = ""
    coingecko_api_key: str = ""
    polygon_api_key: str = ""
    
    # CORS (comma-separated string from env)
    cors_origins: str = "http://localhost:8101"
    
    # Environment
    environment: str = "production"
    debug: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Map environment variable names
        env_prefix="",
    )
    
    @cached_property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins if isinstance(self.cors_origins, list) else []


# Create global settings instance
settings = Settings()

