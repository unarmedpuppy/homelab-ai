from __future__ import annotations

from pydantic import BaseModel, Field


class PostMessageRequest(BaseModel):
    bot: str = Field(..., description="Bot identity to use (must be registered)")
    channel: str = Field(..., description="Channel name or ID")
    message: str = Field(..., description="Message content (supports markdown)")
    props: dict | None = Field(default=None, description="Mattermost post props")
    thread_id: str | None = Field(default=None, description="Reply to specific thread")


class PostMessageResponse(BaseModel):
    success: bool
    post_id: str | None = None
    error: str | None = None


class ReactRequest(BaseModel):
    bot: str = Field(..., description="Bot identity to use")
    post_id: str = Field(..., description="Post ID to react to")
    emoji: str = Field(..., description="Emoji name without colons")


class ReactResponse(BaseModel):
    success: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    bots: list[str]
    mattermost: str


class Message(BaseModel):
    id: str
    user_id: str
    message: str
    create_at: int
    type: str | None = None


class MessagesResponse(BaseModel):
    success: bool
    messages: list[Message] = []
    error: str | None = None


class WebhookResponse(BaseModel):
    success: bool
    post_id: str | None = None
    error: str | None = None
