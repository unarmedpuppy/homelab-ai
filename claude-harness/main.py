"""
Claude Code Harness - OpenAI-compatible API wrapper for Claude Code CLI.

This service wraps the Claude Code CLI to provide an OpenAI-compatible API endpoint,
allowing the Local AI Router to use Claude models via a Claude Max subscription.

Usage:
    uvicorn main:app --host 127.0.0.1 --port 8013
"""
import asyncio
import json
import logging
import subprocess
import time
import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Claude Code Harness",
    description="OpenAI-compatible API wrapper for Claude Code CLI",
    version="1.0.0",
)

# Available models through Claude Code
AVAILABLE_MODELS = {
    "claude-sonnet-4-20250514": {
        "id": "claude-sonnet-4-20250514",
        "object": "model",
        "created": 1700000000,
        "owned_by": "anthropic",
    },
    "claude-3-5-sonnet": {
        "id": "claude-3-5-sonnet",
        "object": "model", 
        "created": 1700000000,
        "owned_by": "anthropic",
        "alias_for": "claude-sonnet-4-20250514",
    },
    "claude-3-5-haiku": {
        "id": "claude-3-5-haiku",
        "object": "model",
        "created": 1700000000,
        "owned_by": "anthropic",
    },
}

# Default model to use
DEFAULT_MODEL = "claude-sonnet-4-20250514"


# Request/Response models
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)


def format_messages_for_claude(messages: List[Message]) -> str:
    """
    Format chat messages into a prompt for Claude Code CLI.
    
    Claude Code expects a single prompt string, so we format the conversation
    history into a readable format.
    """
    formatted_parts = []
    
    for msg in messages:
        role = msg.role.capitalize()
        if role == "System":
            # System messages become context at the start
            formatted_parts.insert(0, f"[System Context]\n{msg.content}\n")
        elif role == "User":
            formatted_parts.append(f"User: {msg.content}")
        elif role == "Assistant":
            formatted_parts.append(f"Assistant: {msg.content}")
    
    return "\n\n".join(formatted_parts)


async def call_claude_cli(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Call Claude Code CLI in headless mode and return the response.
    
    Uses `claude -p` for non-interactive mode.
    """
    # Resolve model aliases
    model_config = AVAILABLE_MODELS.get(model, {})
    actual_model = model_config.get("alias_for", model)
    
    # Build command
    # --dangerously-skip-permissions: Container is sandboxed, allow all tools including SSH
    cmd = ["claude", "-p", "--dangerously-skip-permissions", prompt]
    
    logger.info(f"Calling Claude CLI with model hint: {actual_model}")
    logger.debug(f"Prompt length: {len(prompt)} chars")
    
    try:
        # Run Claude CLI
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300.0  # 5 minute timeout
        )
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Claude CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Claude CLI error: {error_msg}")
        
        response = stdout.decode().strip()
        logger.info(f"Claude CLI response length: {len(response)} chars")
        
        return response
        
    except asyncio.TimeoutError:
        logger.error("Claude CLI timeout after 300 seconds")
        raise HTTPException(status_code=504, detail="Claude CLI timeout")
    except FileNotFoundError:
        logger.error("Claude CLI not found - is it installed?")
        raise HTTPException(status_code=500, detail="Claude CLI not found")


async def stream_claude_cli(prompt: str, model: str = DEFAULT_MODEL) -> AsyncGenerator[str, None]:
    """
    Stream response from Claude Code CLI.
    
    Note: Claude CLI doesn't natively support streaming output,
    so we simulate it by yielding chunks of the response.
    For true streaming, we'd need to capture stdout in real-time.
    """
    # For now, get full response then simulate streaming
    # TODO: Implement true streaming by reading stdout line-by-line
    
    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    
    # Send initial event
    yield f"data: {json.dumps({'id': response_id, 'object': 'chat.completion.chunk', 'created': created, 'model': model, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
    
    try:
        # Get full response
        full_response = await call_claude_cli(prompt, model)
        
        # Stream in chunks (simulate streaming)
        chunk_size = 50  # Characters per chunk
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i + chunk_size]
            data = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": chunk},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.01)  # Small delay for streaming effect
        
        # Send finish event
        data = {
            "id": response_id,
            "object": "chat.completion.chunk", 
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(data)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = {
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Verify Claude CLI is available
    try:
        process = await asyncio.create_subprocess_exec(
            "claude", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10.0)
        version = stdout.decode().strip() if stdout else "unknown"
        
        return {
            "status": "healthy",
            "claude_cli": "available",
            "version": version,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "claude_cli": "unavailable",
            "error": str(e),
        }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    return {
        "object": "list",
        "data": list(AVAILABLE_MODELS.values()),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    
    Translates the request to Claude Code CLI format and returns response.
    """
    logger.info(f"Chat completion request: model={request.model}, stream={request.stream}, messages={len(request.messages)}")
    
    # Format messages for Claude
    prompt = format_messages_for_claude(request.messages)
    
    if request.stream:
        return StreamingResponse(
            stream_claude_cli(prompt, request.model),
            media_type="text/event-stream",
        )
    
    # Non-streaming response
    response_text = await call_claude_cli(prompt, request.model)
    
    return ChatCompletionResponse(
        model=request.model,
        choices=[
            Choice(
                message=Message(role="assistant", content=response_text),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=len(prompt.split()),  # Rough estimate
            completion_tokens=len(response_text.split()),
            total_tokens=len(prompt.split()) + len(response_text.split()),
        ),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8013)
