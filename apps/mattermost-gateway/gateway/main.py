from __future__ import annotations

import logging

from fastapi import FastAPI

from .config import get_settings
from .routes import health, messages, posts, tayne, webhooks

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.gateway_log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Mattermost Gateway",
    description="HTTP gateway for Mattermost bot interactions",
    version="1.0.0",
)

app.include_router(posts.router)
app.include_router(health.router)
app.include_router(messages.router)
app.include_router(webhooks.router)
app.include_router(tayne.router)


@app.get("/")
async def root():
    return {"service": "mattermost-gateway", "version": "1.0.0"}
