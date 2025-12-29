"""
Middleware for request/response tracking, metrics logging, and memory storage.
"""
import os
import time
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from database import init_database
from memory import (
    create_conversation,
    add_message,
    get_conversation,
    generate_conversation_id,
)
from metrics import log_metric
from models import (
    ConversationCreate,
    MessageCreate,
    MetricCreate,
    MessageRole,
)

logger = logging.getLogger(__name__)

# Feature flags
ENABLE_MEMORY = bool(int(os.getenv("ENABLE_MEMORY", "1")))
ENABLE_METRICS = bool(int(os.getenv("ENABLE_METRICS", "1")))


class MemoryMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Captures request metadata (timing, headers, body)
    2. Logs metrics for all requests
    3. Stores conversation memory based on headers
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Initialize database on startup
        if ENABLE_MEMORY or ENABLE_METRICS:
            init_database()
            logger.info("Database initialized for memory/metrics")

    async def dispatch(self, request: Request, call_next):
        """Process request and response."""
        start_time = time.time()

        # Skip middleware for health/docs endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/agent/tools"]:
            return await call_next(request)

        # Extract metadata from request
        metadata = await self._extract_request_metadata(request)

        # Store original body for later
        body = None
        if request.method == "POST":
            try:
                body = await request.json()
                # Re-create request with body (FastAPI consumes it)
                from starlette.requests import Request as StarletteRequest
                async def receive():
                    return {"type": "http.request", "body": json.dumps(body).encode()}
                request = StarletteRequest(request.scope, receive)
            except Exception as e:
                logger.warning(f"Failed to parse request body: {e}")

        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log metrics and memory
            if ENABLE_METRICS or ENABLE_MEMORY:
                await self._log_request(
                    request=request,
                    body=body,
                    response=response,
                    metadata=metadata,
                    duration_ms=duration_ms,
                    error=error,
                )

        return response

    async def _extract_request_metadata(self, request: Request) -> Dict[str, Any]:
        """Extract metadata from request headers."""
        return {
            "conversation_id": request.headers.get("X-Conversation-ID"),
            "session_id": request.headers.get("X-Session-ID"),
            "user_id": request.headers.get("X-User-ID"),
            "project": request.headers.get("X-Project"),
            "enable_memory": request.headers.get("X-Enable-Memory", "").lower() == "true",
            "force_big": request.headers.get("X-Force-Big", "").lower() == "true",
        }

    async def _log_request(
        self,
        request: Request,
        body: Optional[dict],
        response: Optional[Response],
        metadata: Dict[str, Any],
        duration_ms: int,
        error: Optional[str],
    ):
        """Log metrics and optionally store memory."""
        # Only track chat completions for now
        if not (request.url.path == "/v1/chat/completions" and body):
            return

        conversation_id = metadata.get("conversation_id")
        messages = body.get("messages", [])
        model_requested = body.get("model", "auto")
        streaming = body.get("stream", False)

        # Extract response data
        response_data = None
        if response and hasattr(response, "body"):
            try:
                response_data = json.loads(response.body.decode())
            except Exception:
                pass

        # Get token counts from response
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        model_used = None
        backend = None

        if response_data:
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
            model_used = response_data.get("model")

            # Try to infer backend from model name
            if model_used:
                if "qwen" in model_used.lower() or "llama" in model_used.lower():
                    backend = "3090"
                elif "glm" in model_used.lower():
                    backend = "opencode-glm"
                elif "claude" in model_used.lower():
                    backend = "opencode-claude"

        # Log metrics
        if ENABLE_METRICS:
            try:
                log_metric(
                    MetricCreate(
                        conversation_id=conversation_id,
                        session_id=metadata.get("session_id"),
                        endpoint=request.url.path,
                        model_requested=model_requested,
                        model_used=model_used,
                        backend=backend,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        duration_ms=duration_ms,
                        success=error is None,
                        error=error,
                        streaming=streaming,
                        tool_calls_count=0,  # TODO: Extract from response
                        user_id=metadata.get("user_id"),
                        project=metadata.get("project"),
                    )
                )
                logger.debug(f"Logged metric for {request.url.path}")
            except Exception as e:
                logger.error(f"Failed to log metric: {e}")

        # Store conversation memory
        if ENABLE_MEMORY and (conversation_id or metadata.get("enable_memory")):
            try:
                # Auto-generate conversation ID if memory is enabled but no ID provided
                if not conversation_id:
                    conversation_id = generate_conversation_id()
                    logger.info(f"Generated conversation ID: {conversation_id}")

                # Create conversation if it doesn't exist
                if not get_conversation(conversation_id):
                    create_conversation(
                        ConversationCreate(
                            id=conversation_id,
                            session_id=metadata.get("session_id"),
                            user_id=metadata.get("user_id"),
                            project=metadata.get("project"),
                        )
                    )
                    logger.info(f"Created conversation: {conversation_id}")

                # Store user message(s)
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content")

                    add_message(
                        MessageCreate(
                            conversation_id=conversation_id,
                            role=MessageRole(role),
                            content=content,
                            tokens_prompt=prompt_tokens if role == "user" else None,
                        )
                    )

                # Store assistant response
                if response_data:
                    choices = response_data.get("choices", [])
                    if choices:
                        assistant_message = choices[0].get("message", {})
                        content = assistant_message.get("content")

                        add_message(
                            MessageCreate(
                                conversation_id=conversation_id,
                                role=MessageRole.ASSISTANT,
                                content=content,
                                model_used=model_used,
                                backend=backend,
                                tokens_completion=completion_tokens,
                            )
                        )

                logger.debug(f"Stored conversation: {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to store conversation: {e}")
