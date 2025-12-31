"""
FastAPI dependencies for request tracking and metrics logging.
"""
import os
import time
import logging
from typing import Optional
from fastapi import Request, BackgroundTasks
from datetime import datetime, timezone

from database import init_database
from memory import create_conversation, add_message, get_conversation, generate_conversation_id
from metrics import log_metric
from models import ConversationCreate, MessageCreate, MetricCreate, MessageRole
import prometheus_metrics as prom

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


async def get_request_tracker(request: Request) -> RequestTracker:
    """Dependency to create a request tracker."""
    return RequestTracker(request)


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

        if response_data and not error:
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
            model_used = response_data.get("model")

            # Use actual provider from routing selection (passed via response_data)
            backend = response_data.get("provider")
            provider_name = response_data.get("provider_name")

            # Get assistant response
            choices = response_data.get("choices", [])
            if choices:
                assistant_message = choices[0].get("message", {})
                assistant_content = assistant_message.get("content")

        # Log metrics
        if ENABLE_METRICS:
            try:
                log_metric(
                    MetricCreate(
                        conversation_id=tracker.conversation_id,
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
                        tool_calls_count=0,  # TODO: Extract from response
                        user_id=tracker.user_id,
                        project=tracker.project,
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

        # Store conversation memory
        if ENABLE_MEMORY and (tracker.conversation_id or tracker.enable_memory) and not error:
            try:
                # Auto-generate conversation ID if memory enabled but no ID provided
                conversation_id = tracker.conversation_id
                if not conversation_id:
                    conversation_id = generate_conversation_id()
                    logger.info(f"Generated conversation ID: {conversation_id}")

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

                # Store only the LAST user message (the new one)
                # The messages array contains full conversation history, but we only
                # want to store the new message to avoid duplicates
                user_messages = [m for m in messages if m.get("role") == "user"]
                if user_messages:
                    last_user_msg = user_messages[-1]
                    add_message(
                        MessageCreate(
                            conversation_id=conversation_id,
                            role=MessageRole.USER,
                            content=last_user_msg.get("content"),
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

    except Exception as e:
        logger.error(f"Failed to log chat completion: {e}")
