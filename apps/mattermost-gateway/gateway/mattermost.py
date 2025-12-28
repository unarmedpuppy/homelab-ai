from __future__ import annotations

import logging
from typing import Any

from mattermostdriver import Driver  # type: ignore[import-untyped]

from .config import BotConfig, get_settings

logger = logging.getLogger(__name__)


class MattermostClientError(Exception):
    pass


class MattermostClient:
    def __init__(self, bot: BotConfig):
        self.bot = bot
        self._driver: Any = None
        self._channel_cache: dict[str, str] = {}

    @property
    def driver(self) -> Any:
        if self._driver is None:
            settings = get_settings()
            token = self.bot.token
            if not token:
                raise MattermostClientError(
                    f"Bot '{self.bot.name}' has no token configured"
                )

            self._driver = Driver({
                "url": settings.mattermost_url,
                "scheme": settings.mattermost_scheme,
                "port": settings.mattermost_port,
                "token": token,
                "verify": True,
            })
            self._driver.login()

        return self._driver

    def _resolve_channel_id(self, channel: str) -> str:
        if channel in self._channel_cache:
            return self._channel_cache[channel]

        if len(channel) == 26 and channel.isalnum():
            return channel

        try:
            team = self.driver.teams.get_teams()[0]
            channel_info = self.driver.channels.get_channel_by_name(
                team["id"], channel
            )
            channel_id = channel_info["id"]
            self._channel_cache[channel] = channel_id
            return channel_id
        except Exception as e:
            logger.warning(f"Could not resolve channel '{channel}': {e}")
            raise MattermostClientError(f"Channel '{channel}' not found") from e

    def post_message(
        self,
        channel: str,
        message: str,
        props: dict | None = None,
        thread_id: str | None = None,
    ) -> dict:
        channel_id = self._resolve_channel_id(channel)

        post_data: dict[str, Any] = {
            "channel_id": channel_id,
            "message": message,
        }

        if props:
            post_data["props"] = props
        if thread_id:
            post_data["root_id"] = thread_id

        try:
            result = self.driver.posts.create_post(post_data)
            logger.info(
                f"Posted message to {channel} as {self.bot.name}: {message[:50]}..."
            )
            return result
        except Exception as e:
            logger.error(f"Failed to post message: {e}")
            raise MattermostClientError(f"Failed to post message: {e}") from e

    def add_reaction(self, post_id: str, emoji: str) -> dict:
        try:
            user_id = self.driver.users.get_user("me")["id"]
            result = self.driver.reactions.create_reaction({
                "user_id": user_id,
                "post_id": post_id,
                "emoji_name": emoji,
            })
            logger.info(f"Added reaction :{emoji}: to post {post_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            raise MattermostClientError(f"Failed to add reaction: {e}") from e

    def check_connection(self) -> bool:
        try:
            self.driver.users.get_user("me")
            return True
        except Exception:
            return False


_client_cache: dict[str, MattermostClient] = {}


def get_client(bot: BotConfig) -> MattermostClient:
    if bot.name not in _client_cache:
        _client_cache[bot.name] = MattermostClient(bot)
    return _client_cache[bot.name]


def clear_client_cache():
    _client_cache.clear()
