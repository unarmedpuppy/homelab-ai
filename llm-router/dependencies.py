"""
FastAPI dependencies for request tracking and metrics logging.
"""
import os
import time
import logging
from typing import Optional
from fastapi import Request, BackgroundTasks, HTTPException, Depends
from datetime import datetime, timezone

from database import init_database
from memory import create_conversation, add_message, get_conversation, generate_conversation_id
from metrics import log_metric
from models import ConversationCreate, MessageCreate, MetricCreate, MessageRole
import prometheus_metrics as prom
# auth is imported here (not vice-versa) so no circular dependency
from auth import validate_api_key_header, ApiKey

logger = logging.getLogger(__name__)

# Feature flags
ENABLE_MEMORY = bool(int(os.getenv("ENABLE_MEMORY", "1")))
ENABLE_METRICS = bool(int(os.getenv("ENABLE_METRICS", "1")))

# Initialize database on import
if ENABLE_MEMORY or ENABLE_METRICS:
    try:
        init_database()
        logger.info("Database initialized for memory/metrics")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


class RequestTracker:
    """Tracks request metadata and timing."""

    def __init__(self, request: Request):
        self.request = request
        self.start_time = time.time()
        self.conversation_id = request.headers.get("X-Conversation-ID")
        self.session_id = request.headers.get("X-Session-ID")
        self.user_id = request.headers.get("X-User-ID")
        self.project = request.headers.get("X-Project")
        self.username = request.headers.get("X-Username")
        self.source = request.headers.get("X-Source")
        self.display_name = request.headers.get("X-Display-Name")
        self.enable_memory = request.headers.get("X-Enable-Memory", "").lower() == "true"

    def get_duration_ms(self) -> int:
        """Get request duration in milliseconds."""
        return int((time.time() - self.start_time) * 1000)


async def get_request_tracker(
    request: Request,
    api_key: ApiKey = Depends(validate_api_key_header),
) -> RequestTracker:
    """Dependency to create a request tracker.

    Applies memory defaults from API key metadata when X-* headers are absent,
    then validates that X-User-ID is present if memory is enabled.

    FastAPI deduplicates validate_api_key_header — it won't be called twice
    even if the route handler also depends on it.
    """
    tracker = RequestTracker(request)

    # Apply memory defaults from API key metadata (fills in missing X-* headers)
    if api_key and api_key.metadata:
        defaults = api_key.metadata.get("memory_defaults", {})
        if defaults:
            if not tracker.enable_memory and defaults.get("enable_memory"):
                tracker.enable_memory = True
            if not tracker.user_id:
                tracker.user_id = defaults.get("user_id")
            if not tracker.source:
                tracker.source = defaults.get("source")
            if not tracker.project:
                tracker.project = defaults.get("project")
            if not tracker.display_name:
                tracker.display_name = defaults.get("display_name")

    # Require X-User-ID when memory is enabled
    if tracker.enable_memory and not tracker.user_id:
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header is required when X-Enable-Memory is true. "
                   "This ensures all stored conversations have proper user attribution."
        )

    return tracker


def _extract_text_content(content) -> Optional[str]:
    """Normalize OpenAI message content to a plain string.

    Handles both plain strings and structured content arrays
    (e.g. [{type: "text", text: "..."}, {type: "image_url", ...}]).
    """
    if content is None:
        return None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        return "".join(parts) or None
    return str(content)


def log_chat_completion(
    tracker: RequestTracker,
    body: dict,
    response_data: dict,
    error: Optional[str] = None
):
    """
    Log metrics and optionally store conversation memory for chat completions.

    This function is called after the response is generated, so it has access
    to both the request body and response data.
    """
    if not (ENABLE_METRICS or ENABLE_MEMORY):
        return

    try:
        messages = body.get("messages", [])
        model_requested = body.get("model", "auto")
        streaming = body.get("stream", False)

        # Extract response data
        model_used = None
        backend = None
        provider_name = None
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        assistant_content = None

        cost_usd = None
        if response_data and not error:
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
            model_used = response_data.get("model")

            backend = response_data.get("provider")
            provider_name = response_data.get("provider_name")
            cost_usd = response_data.get("cost_usd")

            choices = response_data.get("choices", [])
            if choices:
                assistant_message = choices[0].get("message", {})
                assistant_content = assistant_message.get("content")

        # Resolve the conversation ID that will be used for both memory and metrics.
        # Memory block may auto-generate one, so we need to know it up-front so that
        # the FK reference in metrics is valid when the row is inserted.
        resolved_conversation_id = tracker.conversation_id

        # Store conversation memory first (so the row exists before metrics FK insert)
        if ENABLE_MEMORY and (tracker.conversation_id or tracker.enable_memory) and not error:
            try:
                conversation_id = tracker.conversation_id
                if not conversation_id:
                    conversation_id = generate_conversation_id()
                    logger.info(f"Generated conversation ID: {conversation_id}")

                resolved_conversation_id = conversation_id

                # Create conversation if it doesn't exist
                if not get_conversation(conversation_id):
                    create_conversation(
                        ConversationCreate(
                            id=conversation_id,
                            session_id=tracker.session_id,
                            user_id=tracker.user_id,
                            project=tracker.project,
                            username=tracker.username,
                            source=tracker.source,
                            display_name=tracker.display_name,
                        )
                    )
                    logger.info(f"Created conversation: {conversation_id}")

                # Store only the LAST user message (the new one).
                # Normalize content: OpenAI structured content arrays → plain string.
                user_messages = [m for m in messages if m.get("role") == "user"]
                if user_messages:
                    last_user_msg = user_messages[-1]
                    add_message(
                        MessageCreate(
                            conversation_id=conversation_id,
                            role=MessageRole.USER,
                            content=_extract_text_content(last_user_msg.get("content")),
                            tokens_prompt=prompt_tokens,
                            metadata={"model_requested": model_requested},
                        )
                    )

                # Store assistant response
                if assistant_content:
                    add_message(
                        MessageCreate(
                            conversation_id=conversation_id,
                            role=MessageRole.ASSISTANT,
                            content=assistant_content,
                            model_used=model_used,
                            backend=backend,
                            tokens_completion=completion_tokens,
                            metadata={"provider_name": provider_name} if provider_name else None,
                        )
                    )

                logger.debug(f"Stored conversation: {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to store conversation: {e}")

        # Log metrics — after memory block so conversation FK row exists
        if ENABLE_METRICS:
            try:
                log_metric(
                    MetricCreate(
                        conversation_id=resolved_conversation_id,
                        session_id=tracker.session_id,
                        endpoint="/v1/chat/completions",
                        model_requested=model_requested,
                        model_used=model_used,
                        backend=backend,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        duration_ms=tracker.get_duration_ms(),
                        success=error is None,
                        error=error,
                        streaming=streaming,
                        tool_calls_count=0,
                        user_id=tracker.user_id,
                        project=tracker.project,
                        cost_usd=cost_usd,
                    )
                )
                logger.debug(f"Logged metric for chat completion")
            except Exception as e:
                logger.error(f"Failed to log metric: {e}")

        # Record Prometheus metrics
        try:
            duration_seconds = tracker.get_duration_ms() / 1000.0
            status = "200" if error is None else "500"
            provider = backend or "unknown"

            prom.record_request(
                endpoint="/v1/chat/completions",
                model=model_used or model_requested,
                provider=provider,
                status=status,
                duration_seconds=duration_seconds,
                prompt_tokens=prompt_tokens or 0,
                completion_tokens=completion_tokens or 0
            )

            if error:
                prom.record_error("/v1/chat/completions", "request_failed")
        except Exception as e:
            logger.debug(f"Failed to record Prometheus metrics: {e}")

    except Exception as e:
        logger.error(f"Failed to log chat completion: {e}")
