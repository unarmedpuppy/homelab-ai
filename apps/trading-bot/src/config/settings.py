"""
Configuration Management
========================

Centralized configuration management using Pydantic settings.
Supports environment-specific configurations and validation.
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os
from pathlib import Path

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="sqlite:///./bot.db", description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    
    class Config:
        env_prefix = "DB_"

class IBKRSettings(BaseSettings):
    """Interactive Brokers configuration"""
    host: str = Field(default="127.0.0.1", description="TWS/Gateway host")
    port: int = Field(default=7497, description="TWS/Gateway port")
    client_id: int = Field(default=9, description="Client ID")
    timeout: int = Field(default=10, description="Connection timeout in seconds")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    class Config:
        env_prefix = "IBKR_"

class UnusualWhalesSettings(BaseSettings):
    """Unusual Whales API configuration"""
    api_key: Optional[str] = Field(default=None, description="API key for Unusual Whales")
    base_url: str = Field(default="https://api.unusualwhales.com", description="Base API URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    rate_limit: int = Field(default=100, description="Requests per minute")
    
    class Config:
        env_prefix = "UW_"

class TradingSettings(BaseSettings):
    """Trading strategy configuration"""
    default_qty: int = Field(default=10, description="Default position size")
    default_entry_threshold: float = Field(default=0.005, description="Default SMA entry threshold (0.5%)")
    default_take_profit: float = Field(default=0.20, description="Default take profit (20%)")
    default_stop_loss: float = Field(default=0.10, description="Default stop loss (10%)")
    max_position_size: int = Field(default=1000, description="Maximum position size")
    max_daily_trades: int = Field(default=50, description="Maximum trades per day")
    
    @validator('default_entry_threshold', 'default_take_profit', 'default_stop_loss')
    def validate_percentages(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Percentage values must be between 0 and 1')
        return v
    
    class Config:
        env_prefix = "TRADING_"

class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format (json/text)")
    file: Optional[str] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"

class APISettings(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit: str = Field(default="100/minute", description="Rate limit per IP")
    
    class Config:
        env_prefix = "API_"

class RedisSettings(BaseSettings):
    """Redis configuration for caching and background tasks"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    
    class Config:
        env_prefix = "REDIS_"

class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    ibkr: IBKRSettings = IBKRSettings()
    unusual_whales: UnusualWhalesSettings = UnusualWhalesSettings()
    trading: TradingSettings = TradingSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    redis: RedisSettings = RedisSettings()
    
    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of {valid_envs}')
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()
