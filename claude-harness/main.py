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
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
import re

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://homelab-ai.server.unarmedpuppy.com",
        "https://local-ai-dashboard.server.unarmedpuppy.com",  # Legacy alias
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",   # Common dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    # Validate working directory exists
    if not os.path.isdir(working_directory):
        logger.error(f"Working directory does not exist: {working_directory}")
        raise HTTPException(
            status_code=400,
            detail=f"Working directory does not exist: {working_directory}"
        )

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


# ============================================================================
# Ralph Wiggum - Autonomous Task Loop
# ============================================================================

# Ralph Wiggum multi-instance configuration
TASKS_DIR = "/workspace/home-server"  # Where tasks.md lives
RALPH_REGISTRY_FILE = Path("/workspace/.ralph-processes.json")


@dataclass
class RalphInstance:
    """Tracks a running Ralph Wiggum instance."""
    label: str
    pid: int
    started_at: str
    status_file: str
    control_file: str
    log_file: str
    process: Optional[asyncio.subprocess.Process] = None  # Not serialized

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization (excludes process)."""
        return {
            "label": self.label,
            "pid": self.pid,
            "started_at": self.started_at,
            "status_file": self.status_file,
            "control_file": self.control_file,
            "log_file": self.log_file,
        }


# In-memory tracking of Ralph processes (keyed by label)
ralph_processes: Dict[str, RalphInstance] = {}


def sanitize_label(label: str) -> str:
    """Sanitize label for use in filenames."""
    # Replace colons with dashes, remove other unsafe chars
    safe = re.sub(r'[^a-zA-Z0-9_-]', '-', label)
    # Collapse multiple dashes
    safe = re.sub(r'-+', '-', safe)
    # Remove leading/trailing dashes
    return safe.strip('-').lower()


def get_instance_paths(label: str) -> tuple:
    """Generate file paths for a Ralph instance."""
    label_safe = sanitize_label(label)
    status_file = f"/workspace/.ralph-{label_safe}-status.json"
    control_file = f"/workspace/.ralph-{label_safe}-control"
    log_file = f"/workspace/.ralph-{label_safe}.log"
    return status_file, control_file, log_file


def save_ralph_registry():
    """Persist Ralph process registry to disk."""
    try:
        data = {label: inst.to_dict() for label, inst in ralph_processes.items()}
        with open(RALPH_REGISTRY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved Ralph registry with {len(data)} instances")
    except Exception as e:
        logger.error(f"Could not save Ralph registry: {e}")


def load_ralph_registry():
    """Load and recover Ralph instances from registry file."""
    global ralph_processes

    if not RALPH_REGISTRY_FILE.exists():
        logger.info("No Ralph registry file found, starting fresh")
        return

    try:
        with open(RALPH_REGISTRY_FILE, 'r') as f:
            data = json.load(f)

        recovered = 0
        for label, info in data.items():
            pid = info.get("pid")
            if pid:
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    # Process still running, restore it
                    ralph_processes[label] = RalphInstance(
                        label=info["label"],
                        pid=pid,
                        started_at=info["started_at"],
                        status_file=info["status_file"],
                        control_file=info["control_file"],
                        log_file=info["log_file"],
                        process=None,  # Can't restore asyncio process, but we have the PID
                    )
                    recovered += 1
                    logger.info(f"Recovered Ralph instance '{label}' (PID {pid})")
                except OSError:
                    # Process not running, clean up files
                    logger.info(f"Ralph instance '{label}' (PID {pid}) no longer running, cleaning up")
                    for fpath in [info.get("status_file"), info.get("control_file")]:
                        if fpath and os.path.exists(fpath):
                            try:
                                os.remove(fpath)
                            except Exception:
                                pass

        if recovered > 0:
            logger.info(f"Recovered {recovered} Ralph instance(s) from registry")
        # Save cleaned registry
        save_ralph_registry()
    except Exception as e:
        logger.error(f"Could not load Ralph registry: {e}")


class RalphStartRequest(BaseModel):
    """Request to start Ralph Wiggum."""
    label: str = Field(..., description="Label to filter tasks (e.g., 'mercury', 'trading-bot')")
    priority: Optional[int] = Field(default=None, description="Filter by priority (0=critical, 1=high, 2=medium, 3=low)")
    max_tasks: Optional[int] = Field(default=0, description="Maximum tasks to process (0=unlimited)")
    dry_run: Optional[bool] = Field(default=False, description="Preview without executing")


class RalphStatusResponse(BaseModel):
    """Ralph Wiggum status response."""
    running: bool
    status: str  # idle, running, stopping, completed
    label: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_task: Optional[str] = None
    current_task_title: Optional[str] = None
    started_at: Optional[str] = None
    last_update: Optional[str] = None
    message: Optional[str] = None


class RalphInstanceInfo(BaseModel):
    """Information about a Ralph instance."""
    label: str
    pid: int
    running: bool
    started_at: str
    status: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_task: Optional[str] = None
    current_task_title: Optional[str] = None


class RalphInstancesResponse(BaseModel):
    """Response for listing all Ralph instances."""
    instances: List[RalphInstanceInfo]
    count: int


def read_ralph_status(status_file: str) -> dict:
    """Read Ralph Wiggum status from file."""
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read Ralph status from {status_file}: {e}")
    return {
        "running": False,
        "status": "idle",
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
    }


def write_ralph_control(control_file: str, command: str):
    """Write a control command for Ralph Wiggum."""
    try:
        with open(control_file, 'w') as f:
            f.write(command)
    except Exception as e:
        logger.error(f"Could not write Ralph control to {control_file}: {e}")
        raise


def is_instance_running(instance: RalphInstance) -> bool:
    """Check if a Ralph instance is still running."""
    # First check if we have an asyncio process reference
    if instance.process is not None:
        if instance.process.returncode is None:
            return True
        else:
            return False
    # Fall back to checking PID
    if instance.pid:
        try:
            os.kill(instance.pid, 0)
            return True
        except OSError:
            return False
    return False


async def start_ralph_wiggum(label: str, priority: Optional[int], max_tasks: int, dry_run: bool):
    """Start Ralph Wiggum as a background process."""
    global ralph_processes

    # Get instance-specific file paths
    status_file, control_file, log_file = get_instance_paths(label)

    # Build command
    cmd = ["/app/ralph-wiggum.sh", "--label", label]

    if priority is not None:
        cmd.extend(["--priority", str(priority)])

    if max_tasks > 0:
        cmd.extend(["--max", str(max_tasks)])

    if dry_run:
        cmd.append("--dry-run")

    logger.info(f"Starting Ralph Wiggum for label '{label}': {' '.join(cmd)}")

    # Clear any previous control file for this instance
    if os.path.exists(control_file):
        os.remove(control_file)

    # Start the process
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd="/workspace",
        env={
            **os.environ,
            "TASKS_DIR": TASKS_DIR,
            "STATUS_FILE": status_file,
            "CONTROL_FILE": control_file,
            "LOG_FILE": log_file,
        }
    )

    # Create instance tracking object
    instance = RalphInstance(
        label=label,
        pid=process.pid,
        started_at=datetime.utcnow().isoformat() + "Z",
        status_file=status_file,
        control_file=control_file,
        log_file=log_file,
        process=process,
    )

    # Store in registry
    ralph_processes[label] = instance
    save_ralph_registry()

    logger.info(f"Ralph Wiggum '{label}' started with PID {process.pid}")


@app.post("/v1/ralph/start")
async def start_ralph(request: RalphStartRequest, background_tasks: BackgroundTasks):
    """
    Start Ralph Wiggum autonomous task loop.

    Processes tasks matching the given label filter.
    Multiple instances can run concurrently with different labels.

    Example:
        curl -X POST http://localhost:8013/v1/ralph/start \\
          -H "Content-Type: application/json" \\
          -d '{"label": "mercury"}'
    """
    global ralph_processes

    label = request.label

    # Check if an instance with this label is already running
    if label in ralph_processes:
        instance = ralph_processes[label]
        if is_instance_running(instance):
            raise HTTPException(
                status_code=409,
                detail=f"Ralph Wiggum instance for label '{label}' is already running. Use /v1/ralph/stop?label={label} first."
            )
        else:
            # Instance exists but not running, clean up
            del ralph_processes[label]
            save_ralph_registry()

    # Validate tasks.md exists
    tasks_path = os.path.join(TASKS_DIR, "tasks.md")
    if not os.path.isfile(tasks_path):
        raise HTTPException(
            status_code=500,
            detail=f"Tasks file not found at {tasks_path}"
        )

    # Start in background
    background_tasks.add_task(
        start_ralph_wiggum,
        label,
        request.priority,
        request.max_tasks or 0,
        request.dry_run or False
    )

    return {
        "message": f"Ralph Wiggum starting with label '{label}'",
        "label": label,
        "status_url": f"/v1/ralph/status?label={label}",
        "stop_url": f"/v1/ralph/stop?label={label}",
        "instances_url": "/v1/ralph/instances",
    }


@app.get("/v1/ralph/status")
async def get_ralph_status(label: Optional[str] = None):
    """
    Get Ralph Wiggum current status.

    If label is provided, returns status for that specific instance.
    If no label is provided and only one instance is running, returns that instance's status.
    If no label is provided and multiple instances are running, returns an error.

    Examples:
        curl http://localhost:8013/v1/ralph/status?label=mercury
        curl http://localhost:8013/v1/ralph/status  # Works if only one instance running
    """
    global ralph_processes

    # If label specified, get that specific instance
    if label:
        if label not in ralph_processes:
            raise HTTPException(
                status_code=404,
                detail=f"No Ralph instance found for label '{label}'"
            )
        instance = ralph_processes[label]
        status = read_ralph_status(instance.status_file)
        running = is_instance_running(instance)
        status["running"] = running
        status["label"] = label
        if not running and status.get("status") == "running":
            status["status"] = "completed"
        return RalphStatusResponse(**status)

    # No label specified - check number of instances
    running_instances = [
        (lbl, inst) for lbl, inst in ralph_processes.items()
        if is_instance_running(inst)
    ]

    if len(running_instances) == 0:
        # No instances running, return idle status
        return RalphStatusResponse(
            running=False,
            status="idle",
            message="No Ralph instances running. Use /v1/ralph/instances to list all."
        )
    elif len(running_instances) == 1:
        # Exactly one instance, return its status (backward compatible)
        lbl, instance = running_instances[0]
        status = read_ralph_status(instance.status_file)
        status["running"] = True
        status["label"] = lbl
        return RalphStatusResponse(**status)
    else:
        # Multiple instances running, require label parameter
        labels = [lbl for lbl, _ in running_instances]
        raise HTTPException(
            status_code=400,
            detail=f"Multiple Ralph instances running ({', '.join(labels)}). Specify ?label=X to get status for a specific instance, or use /v1/ralph/instances to list all."
        )


@app.post("/v1/ralph/stop")
async def stop_ralph(label: Optional[str] = None):
    """
    Request Ralph Wiggum to stop gracefully.

    Ralph will finish the current task then exit.
    Requires label parameter when multiple instances are running.

    Examples:
        curl -X POST http://localhost:8013/v1/ralph/stop?label=mercury
        curl -X POST http://localhost:8013/v1/ralph/stop  # Works if only one instance running
    """
    global ralph_processes

    # If label specified, stop that specific instance
    if label:
        if label not in ralph_processes:
            raise HTTPException(
                status_code=404,
                detail=f"No Ralph instance found for label '{label}'"
            )
        instance = ralph_processes[label]
        if not is_instance_running(instance):
            # Clean up non-running instance
            del ralph_processes[label]
            save_ralph_registry()
            return {"message": f"Ralph instance '{label}' is not running", "label": label}

        # Write stop command
        write_ralph_control(instance.control_file, "stop")
        return {
            "message": f"Stop requested for Ralph instance '{label}'. It will finish current task then exit.",
            "label": label,
            "status_url": f"/v1/ralph/status?label={label}",
        }

    # No label specified - check number of running instances
    running_instances = [
        (lbl, inst) for lbl, inst in ralph_processes.items()
        if is_instance_running(inst)
    ]

    if len(running_instances) == 0:
        return {"message": "No Ralph instances are running"}
    elif len(running_instances) == 1:
        # Exactly one instance, stop it (backward compatible)
        lbl, instance = running_instances[0]
        write_ralph_control(instance.control_file, "stop")
        return {
            "message": f"Stop requested for Ralph instance '{lbl}'. It will finish current task then exit.",
            "label": lbl,
            "status_url": f"/v1/ralph/status?label={lbl}",
        }
    else:
        # Multiple instances running, require label parameter
        labels = [lbl for lbl, _ in running_instances]
        raise HTTPException(
            status_code=400,
            detail=f"Multiple Ralph instances running ({', '.join(labels)}). Specify ?label=X to stop a specific instance."
        )


@app.get("/v1/ralph/logs")
async def get_ralph_logs(label: Optional[str] = None, lines: int = 100):
    """
    Get recent Ralph Wiggum logs.

    Requires label parameter when multiple instances exist.

    Examples:
        curl http://localhost:8013/v1/ralph/logs?label=mercury&lines=50
        curl http://localhost:8013/v1/ralph/logs?lines=50  # Works if only one instance
    """
    global ralph_processes

    # Determine which log file to read
    if label:
        if label not in ralph_processes:
            # Instance not in registry, try to find log file anyway
            _, _, log_file = get_instance_paths(label)
        else:
            log_file = ralph_processes[label].log_file
    else:
        # No label specified
        if len(ralph_processes) == 0:
            return {"logs": [], "message": "No Ralph instances found. Specify ?label=X if you know the label."}
        elif len(ralph_processes) == 1:
            # Exactly one instance, use its log file
            log_file = list(ralph_processes.values())[0].log_file
        else:
            # Multiple instances, require label parameter
            labels = list(ralph_processes.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Multiple Ralph instances ({', '.join(labels)}). Specify ?label=X to get logs for a specific instance."
            )

    if not os.path.exists(log_file):
        return {"logs": [], "message": f"No logs found at {log_file}", "label": label}

    try:
        process = await asyncio.create_subprocess_exec(
            "tail", "-n", str(lines), log_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        log_lines = stdout.decode().strip().split('\n')
        return {"logs": log_lines, "count": len(log_lines), "label": label, "log_file": log_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read logs: {e}")


@app.get("/v1/ralph/instances", response_model=RalphInstancesResponse)
async def list_ralph_instances():
    """
    List all Ralph Wiggum instances (running and recently stopped).

    Example:
        curl http://localhost:8013/v1/ralph/instances
    """
    global ralph_processes

    instances = []
    to_remove = []

    for label, instance in ralph_processes.items():
        running = is_instance_running(instance)
        status_data = read_ralph_status(instance.status_file)

        # If not running, check if we should clean it up
        if not running:
            # Keep recently stopped instances for a bit
            # but mark them as completed
            if status_data.get("status") == "running":
                status_data["status"] = "completed"

        instances.append(RalphInstanceInfo(
            label=label,
            pid=instance.pid,
            running=running,
            started_at=instance.started_at,
            status=status_data.get("status", "unknown"),
            total_tasks=status_data.get("total_tasks", 0),
            completed_tasks=status_data.get("completed_tasks", 0),
            failed_tasks=status_data.get("failed_tasks", 0),
            current_task=status_data.get("current_task"),
            current_task_title=status_data.get("current_task_title"),
        ))

    return RalphInstancesResponse(instances=instances, count=len(instances))


@app.on_event("startup")
async def startup_event():
    """Recover Ralph instances on API startup."""
    logger.info("Claude Harness starting up...")
    load_ralph_registry()
    logger.info(f"Recovered {len(ralph_processes)} Ralph instance(s)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8013)
