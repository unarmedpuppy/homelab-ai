"""
Claude Code Harness - OpenAI-compatible API wrapper for Claude Code CLI.

This service wraps the Claude Code CLI to provide an OpenAI-compatible API endpoint,
allowing the Local AI Router to use Claude models via a Claude Max subscription.

Features:
- OpenAI-compatible /v1/chat/completions endpoint (sync, up to 30 min timeout)
- Async job queue /v1/jobs for fire-and-forget long-running tasks
- YOLO mode enabled by default (--dangerously-skip-permissions)

Usage:
    uvicorn main:app --host 127.0.0.1 --port 8013
"""
import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Claude Code Harness",
    description="OpenAI-compatible API wrapper for Claude Code CLI with async job support",
    version="2.0.0",
)

# Configuration
SYNC_TIMEOUT = int(os.environ.get("CLAUDE_SYNC_TIMEOUT", 1800))  # 30 min default
ASYNC_TIMEOUT = int(os.environ.get("CLAUDE_ASYNC_TIMEOUT", 7200))  # 2 hour default for async jobs

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
    "claude-opus-4-20250514": {
        "id": "claude-opus-4-20250514",
        "object": "model",
        "created": 1700000000,
        "owned_by": "anthropic",
    },
}

# Default model to use
DEFAULT_MODEL = "claude-sonnet-4-20250514"


# ============================================================================
# Job Queue System
# ============================================================================

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Job(BaseModel):
    id: str
    status: JobStatus
    prompt: str
    model: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    working_directory: Optional[str] = None


# In-memory job store (for single instance; use Redis for multi-instance)
jobs: Dict[str, Job] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

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


class JobCreateRequest(BaseModel):
    """Request to create an async job."""
    prompt: str = Field(..., description="The task/prompt for Claude to execute")
    model: str = Field(default=DEFAULT_MODEL, description="Model to use")
    working_directory: Optional[str] = Field(
        default="/workspace",
        description="Working directory for Claude (must be under /workspace)"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt to prepend"
    )


class JobCreateResponse(BaseModel):
    """Response when creating a job."""
    job_id: str
    status: JobStatus
    message: str
    poll_url: str


class JobStatusResponse(BaseModel):
    """Full job status response."""
    id: str
    status: JobStatus
    prompt: str
    model: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


# ============================================================================
# Core Functions
# ============================================================================

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


async def call_claude_cli(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: float = None,
    working_directory: str = "/workspace"
) -> str:
    """
    Call Claude Code CLI in headless mode and return the response.

    Uses `claude -p` for non-interactive mode with --dangerously-skip-permissions.
    """
    if timeout is None:
        timeout = SYNC_TIMEOUT

    # Resolve model aliases
    model_config = AVAILABLE_MODELS.get(model, {})
    actual_model = model_config.get("alias_for", model)

    # Build command
    # --dangerously-skip-permissions: Container is sandboxed, allow all tools including SSH
    cmd = ["claude", "-p", "--dangerously-skip-permissions", prompt]

    logger.info(f"Calling Claude CLI with model hint: {actual_model}")
    logger.info(f"Working directory: {working_directory}")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    try:
        # Run Claude CLI
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_directory,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Claude CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Claude CLI error: {error_msg}")

        response = stdout.decode().strip()
        logger.info(f"Claude CLI response length: {len(response)} chars")

        return response

    except asyncio.TimeoutError:
        logger.error(f"Claude CLI timeout after {timeout} seconds")
        raise HTTPException(status_code=504, detail=f"Claude CLI timeout after {timeout}s")
    except FileNotFoundError:
        logger.error("Claude CLI not found - is it installed?")
        raise HTTPException(status_code=500, detail="Claude CLI not found")


async def git_fetch_origin(working_directory: str):
    """Fetch latest from origin before starting work."""
    try:
        process = await asyncio.create_subprocess_exec(
            "git", "fetch", "origin", "--prune",
            cwd=working_directory,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(process.communicate(), timeout=60.0)
        logger.info(f"Fetched latest from origin in {working_directory}")
    except Exception as e:
        logger.warning(f"Git fetch failed in {working_directory}: {e}")


async def execute_job(job_id: str):
    """Execute a job in the background."""
    job = jobs.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    # Update status to running
    job.status = JobStatus.RUNNING
    job.started_at = datetime.utcnow().isoformat()

    logger.info(f"Starting job {job_id}")

    # Always fetch latest from origin before starting work
    working_dir = job.working_directory or "/workspace"
    await git_fetch_origin(working_dir)

    try:
        result = await call_claude_cli(
            prompt=job.prompt,
            model=job.model,
            timeout=ASYNC_TIMEOUT,
            working_directory=job.working_directory or "/workspace"
        )

        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.utcnow().isoformat()
        logger.info(f"Job {job_id} completed successfully")

    except asyncio.TimeoutError:
        job.status = JobStatus.TIMEOUT
        job.error = f"Job timed out after {ASYNC_TIMEOUT} seconds"
        job.completed_at = datetime.utcnow().isoformat()
        logger.error(f"Job {job_id} timed out")

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow().isoformat()
        logger.error(f"Job {job_id} failed: {e}")


async def stream_claude_cli(prompt: str, model: str = DEFAULT_MODEL) -> AsyncGenerator[str, None]:
    """
    Stream response from Claude Code CLI.

    Note: Claude CLI doesn't natively support streaming output,
    so we simulate it by yielding chunks of the response.
    """
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


# ============================================================================
# API Endpoints
# ============================================================================

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

        # Count jobs by status
        job_counts = {}
        for job in jobs.values():
            job_counts[job.status] = job_counts.get(job.status, 0) + 1

        return {
            "status": "healthy",
            "claude_cli": "available",
            "version": version,
            "config": {
                "sync_timeout": SYNC_TIMEOUT,
                "async_timeout": ASYNC_TIMEOUT,
            },
            "jobs": job_counts,
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
    Timeout: 30 minutes (configurable via CLAUDE_SYNC_TIMEOUT env var).
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


# ============================================================================
# Async Job Queue Endpoints
# ============================================================================

@app.post("/v1/jobs", response_model=JobCreateResponse)
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks):
    """
    Create an async job for long-running Claude tasks.

    Returns immediately with a job_id. Poll /v1/jobs/{job_id} for status.
    Timeout: 2 hours (configurable via CLAUDE_ASYNC_TIMEOUT env var).

    Example:
        POST /v1/jobs
        {
            "prompt": "Update the README and push changes",
            "working_directory": "/workspace/trading-bot",
            "system_prompt": "Complete all work, commit with good messages, push to git."
        }
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"

    # Build full prompt with optional system prompt
    full_prompt = request.prompt
    if request.system_prompt:
        full_prompt = f"[System Context]\n{request.system_prompt}\n\nUser: {request.prompt}"

    # Validate working directory
    working_dir = request.working_directory or "/workspace"
    if not working_dir.startswith("/workspace"):
        raise HTTPException(
            status_code=400,
            detail="working_directory must be under /workspace"
        )

    # Create job record
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        prompt=full_prompt,
        model=request.model,
        created_at=datetime.utcnow().isoformat(),
        working_directory=working_dir,
    )
    jobs[job_id] = job

    # Schedule background execution
    background_tasks.add_task(execute_job, job_id)

    logger.info(f"Created job {job_id}")

    return JobCreateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job created and queued for execution",
        poll_url=f"/v1/jobs/{job_id}",
    )


@app.get("/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of an async job.

    Returns current status, and result/error if completed.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Calculate duration if we have timing info
    duration = None
    if job.started_at:
        start = datetime.fromisoformat(job.started_at)
        end = datetime.fromisoformat(job.completed_at) if job.completed_at else datetime.utcnow()
        duration = (end - start).total_seconds()

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        prompt=job.prompt[:200] + "..." if len(job.prompt) > 200 else job.prompt,
        model=job.model,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error,
        duration_seconds=duration,
    )


@app.get("/v1/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 50,
):
    """
    List all jobs, optionally filtered by status.

    Returns most recent jobs first.
    """
    filtered_jobs = list(jobs.values())

    if status:
        filtered_jobs = [j for j in filtered_jobs if j.status == status]

    # Sort by created_at descending
    filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)

    # Limit results
    filtered_jobs = filtered_jobs[:limit]

    return {
        "jobs": [
            {
                "id": j.id,
                "status": j.status,
                "model": j.model,
                "created_at": j.created_at,
                "completed_at": j.completed_at,
            }
            for j in filtered_jobs
        ],
        "total": len(jobs),
    }


@app.delete("/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a completed or failed job from memory.

    Cannot delete running jobs.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot delete a running job")

    del jobs[job_id]

    return {"message": f"Job {job_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8013)
