from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


class BotConfig:
    def __init__(self, name: str, token_env: str, default_channel: str = "town-square"):
        self.name = name
        self.token_env = token_env
        self.default_channel = default_channel

    @property
    def token(self) -> str | None:
        return os.getenv(self.token_env)

    def is_configured(self) -> bool:
        return self.token is not None


BOT_REGISTRY: dict[str, BotConfig] = {
    "tayne": BotConfig(
        name="tayne",
        token_env="MATTERMOST_BOT_TAYNE_TOKEN",
        default_channel="general",
    ),
    "server-monitor": BotConfig(
        name="server-monitor",
        token_env="MATTERMOST_BOT_MONITOR_TOKEN",
        default_channel="alerts",
    ),
    "trading-bot": BotConfig(
        name="trading-bot",
        token_env="MATTERMOST_BOT_TRADING_TOKEN",
        default_channel="trading",
    ),
}


class Settings(BaseSettings):
    mattermost_url: str = Field(default="mattermost.server.unarmedpuppy.com")
    mattermost_scheme: str = Field(default="https")
    mattermost_port: int = Field(default=443)

    gateway_port: int = Field(default=8000)
    gateway_log_level: str = Field(default="INFO")
    default_channel: str = Field(default="town-square")

    channel_cache_ttl: int = Field(default=300)

    # Local AI Router settings (for Tayne bot)
    local_ai_url: str = Field(default="http://local-ai-router:8000")
    local_ai_api_key: str = Field(default="")
    tayne_webhook_token: str = Field(default="")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_bot(name: str) -> BotConfig | None:
    return BOT_REGISTRY.get(name)


def get_configured_bots() -> list[str]:
    return [name for name, bot in BOT_REGISTRY.items() if bot.is_configured()]
