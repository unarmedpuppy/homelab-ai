"""Agent Gateway - FastAPI application for fleet monitoring."""
import base64
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_config
from health import HealthMonitor
from models import (
    Agent, AgentDetails, AgentStatus, FleetStats, Job, JobCreateRequest, JobListResponse, JobStatus,
    TraceEventPayload, TraceSession, TraceSessionDetail, TraceStatsResponse,
)
import traces as trace_db


class ContextResponse(BaseModel):
    """Response model for agent context."""
    content: str
    last_modified: Optional[str] = None
    size_bytes: int = 0


class ContextUpdateRequest(BaseModel):
    """Request model for updating agent context."""
    content: str


class SessionInfo(BaseModel):
    """Single session info."""
    id: str
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    status: str
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    turns: int = 0
    tokens_used: Optional[int] = None


class SessionsResponse(BaseModel):
    """Response model for agent sessions."""
    sessions: list[SessionInfo]
    total: int = 0
    has_more: bool = False

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global health monitor
health_monitor: Optional[HealthMonitor] = None


TRACES_DB_PATH = os.getenv("TRACES_DB_PATH", "/app/data/traces.db")
CLAUDE_SESSIONS_PATH = os.getenv("CLAUDE_SESSIONS_PATH", "/claude-sessions")

# Gitea knowledge base config
GITEA_URL = os.getenv("GITEA_URL", "https://gitea.server.unarmedpuppy.com")
GITEA_TOKEN = os.getenv("GITEA_TOKEN", "")
KNOWLEDGE_REPO = os.getenv("KNOWLEDGE_REPO", "homelab/agent-memory")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources on app startup/shutdown."""
    global health_monitor

    # Load configuration
    try:
        config = load_config()
        logger.info(f"Loaded config with {len(config.agents)} agents")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    # Initialize traces DB
    try:
        os.makedirs(os.path.dirname(TRACES_DB_PATH), exist_ok=True)
        await trace_db.init_db(TRACES_DB_PATH)
        logger.info(f"Traces DB initialized at {TRACES_DB_PATH}")
    except Exception as e:
        logger.warning(f"Failed to initialize traces DB: {e}")

    # Start health monitor
    health_monitor = HealthMonitor(config)
    await health_monitor.start()
    logger.info("Health monitor started")

    yield

    # Shutdown
    if health_monitor:
        await health_monitor.stop()
        logger.info("Health monitor stopped")


app = FastAPI(
    title="Agent Gateway",
    description="Fleet status aggregator for Claude Code agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://homelab-ai.server.unarmedpuppy.com",
        "https://local-ai-dashboard.server.unarmedpuppy.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Agent Gateway",
        "version": "1.0.0",
        "description": "Fleet status aggregator for Claude Code agents",
        "endpoints": {
            "health": "/health",
            "agents": "/api/agents",
            "agent_detail": "/api/agents/{id}",
            "agent_context": "/api/agents/{id}/context",
            "agent_check": "/api/agents/{id}/check",
            "stats": "/api/agents/stats",
            "jobs": "/api/jobs",
            "job_detail": "/api/jobs/{id}",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for the gateway itself."""
    if not health_monitor:
        return {
            "status": "unhealthy",
            "error": "Health monitor not initialized",
        }

    stats = health_monitor.get_stats()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agents_monitored": stats.total_agents,
        "agents_online": stats.online_count,
    }


@app.get("/api/agents", response_model=list[Agent])
async def list_agents(
    status: Optional[str] = None,
    tag: Optional[str] = None,
):
    """
    List all agents with their current status.

    Query Parameters:
        status: Filter by status (online, offline, degraded, unknown)
        tag: Filter by tag
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agents = health_monitor.get_all_agents()

    # Filter by status if provided
    if status:
        agents = [a for a in agents if a.health.status.value == status]

    # Filter by tag if provided
    if tag:
        agents = [a for a in agents if tag in a.tags]

    return agents


@app.get("/api/agents/stats", response_model=FleetStats)
async def get_fleet_stats():
    """
    Get fleet-wide statistics.

    Returns counts of agents by status, response time averages, etc.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    return health_monitor.get_stats()


@app.get("/api/agents/{agent_id}", response_model=AgentDetails)
async def get_agent(agent_id: str):
    """
    Get details for a specific agent.

    Always returns agent info even if offline - status field indicates health.
    This endpoint does NOT return 404 for offline agents.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    return AgentDetails(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        endpoint=agent.endpoint,
        agent_type=agent.agent_type,
        expected_online=agent.expected_online,
        tags=agent.tags,
        health=agent.health,
    )


@app.post("/api/agents/{agent_id}/check")
async def force_health_check(agent_id: str):
    """
    Force an immediate health check for an agent.

    Useful for verifying status after deployment or recovery.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    await health_monitor.check_now(agent_id)

    # Return updated agent status
    agent = health_monitor.get_agent(agent_id)
    return {
        "agent_id": agent_id,
        "status": agent.health.status.value,
        "last_check": agent.health.last_check.isoformat() if agent.health.last_check else None,
        "error": agent.health.error,
    }


@app.get("/api/agents/{agent_id}/context", response_model=ContextResponse)
async def get_agent_context(agent_id: str):
    """
    Fetch the CONTEXT.md content from an agent.

    Proxies the request to the agent's /v1/memory/context endpoint.
    Requires agent to be online.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    if agent.health.status != AgentStatus.ONLINE:
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{agent_id}' is offline. Cannot fetch context.",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{agent.endpoint}/v1/memory/context")

            if response.status_code == 200:
                data = response.json()
                return ContextResponse(
                    content=data.get("content", ""),
                    last_modified=data.get("last_modified"),
                    size_bytes=data.get("size_bytes", len(data.get("content", ""))),
                )
            elif response.status_code == 404:
                # No CONTEXT.md file exists yet
                return ContextResponse(
                    content="",
                    last_modified=None,
                    size_bytes=0,
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent returned error: {response.text}",
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to agent timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to agent")
    except Exception as e:
        logger.exception(f"Error fetching context from agent {agent_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/agents/{agent_id}/context", response_model=ContextResponse)
async def update_agent_context(agent_id: str, request: ContextUpdateRequest):
    """
    Update the CONTEXT.md content on an agent.

    Proxies the request to the agent's /v1/memory/context endpoint.
    Requires agent to be online.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    if agent.health.status != AgentStatus.ONLINE:
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{agent_id}' is offline. Cannot update context.",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.put(
                f"{agent.endpoint}/v1/memory/context",
                json={"content": request.content},
            )

            if response.status_code == 200:
                data = response.json()
                return ContextResponse(
                    content=data.get("content", request.content),
                    last_modified=data.get("last_modified"),
                    size_bytes=data.get("size_bytes", len(request.content)),
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent returned error: {response.text}",
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to agent timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to agent")
    except Exception as e:
        logger.exception(f"Error updating context on agent {agent_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/sessions", response_model=SessionsResponse)
async def get_agent_sessions(
    agent_id: str,
    limit: int = 20,
    offset: int = 0,
):
    """
    Fetch session history from an agent.

    Proxies the request to the agent's /v1/sessions endpoint.
    Requires agent to be online.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    if agent.health.status != AgentStatus.ONLINE:
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{agent_id}' is offline. Cannot fetch sessions.",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{agent.endpoint}/v1/sessions",
                params={"limit": limit, "offset": offset},
            )

            if response.status_code == 200:
                data = response.json()
                sessions = [
                    SessionInfo(
                        id=s.get("id", ""),
                        started_at=s.get("started_at", ""),
                        ended_at=s.get("ended_at"),
                        duration_seconds=s.get("duration_seconds"),
                        status=s.get("status", "unknown"),
                        task_id=s.get("task_id"),
                        task_title=s.get("task_title"),
                        turns=s.get("turns", 0),
                        tokens_used=s.get("tokens_used"),
                    )
                    for s in data.get("sessions", [])
                ]
                return SessionsResponse(
                    sessions=sessions,
                    total=data.get("total", len(sessions)),
                    has_more=data.get("has_more", False),
                )
            elif response.status_code == 404:
                # No sessions endpoint or no data
                return SessionsResponse(sessions=[], total=0, has_more=False)
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent returned error: {response.text}",
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to agent timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to agent")
    except Exception as e:
        logger.exception(f"Error fetching sessions from agent {agent_id}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Job Proxy Endpoints
# =============================================================================


@app.post("/api/jobs", response_model=Job)
async def create_job(request: JobCreateRequest):
    """
    Create a new job on an agent.

    Proxies the request to the agent's /v1/jobs endpoint.
    Requires agent to be online.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agent = health_monitor.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{request.agent_id}' not found in registry"
        )

    if agent.health.status != AgentStatus.ONLINE:
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{request.agent_id}' is offline. Cannot create job.",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{agent.endpoint}/v1/jobs",
                json={
                    "prompt": request.prompt,
                    "model": request.model,
                    "working_directory": request.working_directory,
                    "allowed_tools": request.allowed_tools,
                    "max_turns": request.max_turns,
                },
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                return Job(
                    job_id=data.get("job_id", ""),
                    agent_id=request.agent_id,
                    prompt=request.prompt,
                    model=request.model,
                    status=JobStatus(data.get("status", "pending")),
                    created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    result=data.get("result"),
                    error=data.get("error"),
                    turns=data.get("turns", 0),
                    tokens_used=data.get("tokens_used"),
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent returned error: {response.text}",
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to agent timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to agent")
    except Exception as e:
        logger.exception(f"Error creating job on agent {request.agent_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs", response_model=JobListResponse)
async def list_jobs(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """
    List jobs across all agents or filter by agent.

    Queries each online agent's /v1/jobs endpoint and aggregates results.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    all_jobs: list[Job] = []
    agents = health_monitor.get_all_agents()

    # Filter by agent_id if provided
    if agent_id:
        agents = [a for a in agents if a.id == agent_id]
        if not agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_id}' not found in registry"
            )

    # Query each online agent
    async with httpx.AsyncClient(timeout=10) as client:
        for agent in agents:
            if agent.health.status != AgentStatus.ONLINE:
                continue

            try:
                params = {"limit": limit}
                if status:
                    params["status"] = status

                response = await client.get(
                    f"{agent.endpoint}/v1/jobs",
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    jobs_data = data.get("jobs", [])
                    for job_data in jobs_data:
                        all_jobs.append(Job(
                            job_id=job_data.get("job_id", ""),
                            agent_id=agent.id,
                            prompt=job_data.get("prompt", ""),
                            model=job_data.get("model", ""),
                            status=JobStatus(job_data.get("status", "pending")),
                            created_at=job_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                            started_at=job_data.get("started_at"),
                            completed_at=job_data.get("completed_at"),
                            result=job_data.get("result"),
                            error=job_data.get("error"),
                            turns=job_data.get("turns", 0),
                            tokens_used=job_data.get("tokens_used"),
                        ))

            except Exception as e:
                logger.warning(f"Failed to fetch jobs from agent {agent.id}: {e}")
                continue

    # Sort by created_at descending
    all_jobs.sort(key=lambda j: j.created_at, reverse=True)

    # Apply limit
    all_jobs = all_jobs[:limit]

    return JobListResponse(jobs=all_jobs, total=len(all_jobs))


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, agent_id: Optional[str] = None):
    """
    Get job status by ID.

    If agent_id is provided, queries that agent directly.
    Otherwise, searches all online agents.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agents = health_monitor.get_all_agents()

    # If agent_id provided, only check that agent
    if agent_id:
        agents = [a for a in agents if a.id == agent_id]
        if not agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_id}' not found in registry"
            )

    async with httpx.AsyncClient(timeout=10) as client:
        for agent in agents:
            if agent.health.status != AgentStatus.ONLINE:
                continue

            try:
                response = await client.get(
                    f"{agent.endpoint}/v1/jobs/{job_id}",
                )

                if response.status_code == 200:
                    data = response.json()
                    return Job(
                        job_id=data.get("job_id", job_id),
                        agent_id=agent.id,
                        prompt=data.get("prompt", ""),
                        model=data.get("model", ""),
                        status=JobStatus(data.get("status", "pending")),
                        created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                        started_at=data.get("started_at"),
                        completed_at=data.get("completed_at"),
                        result=data.get("result"),
                        error=data.get("error"),
                        turns=data.get("turns", 0),
                        tokens_used=data.get("tokens_used"),
                    )

            except Exception as e:
                logger.debug(f"Job {job_id} not found on agent {agent.id}: {e}")
                continue

    raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str, agent_id: Optional[str] = None):
    """
    Cancel a job by ID.

    If agent_id is provided, sends cancel to that agent directly.
    Otherwise, searches all online agents for the job.
    """
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    agents = health_monitor.get_all_agents()

    # If agent_id provided, only check that agent
    if agent_id:
        agents = [a for a in agents if a.id == agent_id]
        if not agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_id}' not found in registry"
            )

    async with httpx.AsyncClient(timeout=10) as client:
        for agent in agents:
            if agent.health.status != AgentStatus.ONLINE:
                continue

            try:
                response = await client.delete(
                    f"{agent.endpoint}/v1/jobs/{job_id}",
                )

                if response.status_code == 200:
                    return {
                        "job_id": job_id,
                        "agent_id": agent.id,
                        "status": "cancelled",
                        "message": "Job cancelled successfully",
                    }

            except Exception as e:
                logger.debug(f"Failed to cancel job {job_id} on agent {agent.id}: {e}")
                continue

    raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")


# =============================================================================
# Trace Ingestion + Query Endpoints
# =============================================================================

_INPUT_MAX = 2000
_OUTPUT_MAX = 500


def _truncate(s: str, limit: int) -> str:
    return s[:limit] if s and len(s) > limit else s


@app.post("/traces/events", status_code=204)
async def ingest_trace_event(
    payload: TraceEventPayload,
    x_machine_id: str = Header(default="unknown"),
    x_agent_label: str = Header(default="interactive"),
):
    """Ingest a Claude Code hook event payload."""
    now = datetime.now(timezone.utc).isoformat()
    event_type = payload.type
    session_id = payload.session_id

    try:
        if event_type == "SessionStart":
            interactive = x_agent_label.lower() == "interactive"
            await trace_db.upsert_session(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                machine_id=x_machine_id,
                agent_label=x_agent_label,
                interactive=interactive,
                model=payload.model,
                cwd=payload.cwd,
                start_time=now,
            )

        elif event_type == "PreToolUse" and payload.tool_name:
            input_str = _truncate(json.dumps(payload.tool_input or {}), _INPUT_MAX)
            await trace_db.insert_span(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                tool_name=payload.tool_name,
                event_type="PreToolUse",
                input_json=input_str,
                start_time=now,
            )

        elif event_type == "PostToolUse" and payload.tool_name:
            response_str = payload.tool_response or ""
            summary = _truncate(response_str if isinstance(response_str, str) else json.dumps(response_str), _OUTPUT_MAX)
            await trace_db.update_span(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                tool_name=payload.tool_name,
                output_summary=summary,
                status="completed",
                end_time=now,
            )

        elif event_type == "PostToolUseFailure" and payload.tool_name:
            await trace_db.update_span(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                tool_name=payload.tool_name,
                output_summary=_truncate(payload.error or "unknown error", _OUTPUT_MAX),
                status="failed",
                end_time=now,
            )

        elif event_type == "SubagentStart":
            await trace_db.insert_span(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                tool_name="Agent",
                event_type="SubagentStart",
                input_json=None,
                start_time=now,
                agent_id=payload.agent_id,
                agent_transcript_path=payload.transcript_path,
            )

        elif event_type == "SubagentStop":
            await trace_db.update_span(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                tool_name="Agent",
                output_summary=None,
                status="completed",
                end_time=now,
            )

        elif event_type in ("Stop", "SessionEnd"):
            await trace_db.update_session_end(
                db_path=TRACES_DB_PATH,
                session_id=session_id,
                end_time=now,
            )

    except Exception:
        logger.exception(f"Failed to process trace event {event_type} for session {session_id}")

    return Response(status_code=204)


@app.get("/traces", response_model=list[TraceSession])
async def list_trace_sessions(
    machine_id: Optional[str] = Query(None),
    agent_label: Optional[str] = Query(None),
    interactive: Optional[bool] = Query(None),
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List recorded sessions with optional filters."""
    rows = await trace_db.query_sessions(
        db_path=TRACES_DB_PATH,
        machine_id=machine_id,
        agent_label=agent_label,
        interactive=interactive,
        from_time=from_time,
        to_time=to_time,
        limit=limit,
        offset=offset,
    )
    return [
        TraceSession(
            session_id=r["session_id"],
            machine_id=r["machine_id"],
            agent_label=r["agent_label"],
            interactive=bool(r["interactive"]),
            model=r.get("model"),
            cwd=r.get("cwd"),
            start_time=r["start_time"],
            end_time=r.get("end_time"),
            span_count=r.get("span_count", 0),
        )
        for r in rows
    ]


@app.get("/traces/stats", response_model=TraceStatsResponse)
async def get_trace_stats():
    """Get fleet-wide session statistics."""
    stats = await trace_db.get_stats(TRACES_DB_PATH)
    return TraceStatsResponse(
        by_machine_day=[
            {"machine_id": d["machine_id"], "day": d["day"], "count": d["count"]}
            for d in stats["by_machine_day"]
        ],
        active_sessions=stats["active_sessions"],
        sessions_today=stats["sessions_today"],
    )


@app.get("/traces/{session_id}", response_model=TraceSessionDetail)
async def get_trace_session(session_id: str):
    """Get a session with all its spans."""
    detail = await trace_db.get_session_detail(TRACES_DB_PATH, session_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    from models import TraceSpan
    return TraceSessionDetail(
        session_id=detail["session_id"],
        machine_id=detail["machine_id"],
        agent_label=detail["agent_label"],
        interactive=bool(detail["interactive"]),
        model=detail.get("model"),
        cwd=detail.get("cwd"),
        start_time=detail["start_time"],
        end_time=detail.get("end_time"),
        span_count=detail.get("span_count", 0),
        spans=[
            TraceSpan(
                span_id=s["span_id"],
                session_id=s["session_id"],
                parent_span_id=s.get("parent_span_id"),
                tool_name=s["tool_name"],
                event_type=s["event_type"],
                input_json=s.get("input_json"),
                output_summary=s.get("output_summary"),
                status=s["status"],
                start_time=s["start_time"],
                end_time=s.get("end_time"),
                agent_id=s.get("agent_id"),
                agent_transcript_path=s.get("agent_transcript_path"),
            )
            for s in detail["spans"]
        ],
    )


@app.get("/traces/{session_id}/transcript")
async def get_session_transcript(session_id: str):
    """Read the Claude Code JSONL session file and return conversation messages.

    Only available for sessions whose JSONL file is on the mounted claude-sessions volume.
    Returns 404 for sessions from other machines.
    """
    from pathlib import Path

    projects_dir = Path(CLAUDE_SESSIONS_PATH) / "projects"
    if not projects_dir.exists():
        raise HTTPException(status_code=404, detail="Transcripts not available (volume not mounted)")

    # Scan all project dirs for the session JSONL
    jsonl_file = None
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            jsonl_file = candidate
            break

    if not jsonl_file:
        raise HTTPException(status_code=404, detail="Transcript not found for this session")

    messages = []
    slug = None
    lines_read = 0
    MAX_LINES = 100_000  # safety cap for huge files
    MAX_MESSAGES = 300

    with open(jsonl_file, "r", errors="replace") as f:
        for raw_line in f:
            lines_read += 1
            if lines_read > MAX_LINES or len(messages) >= MAX_MESSAGES:
                break

            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            # Grab slug from first entry that has it
            if not slug and entry.get("slug"):
                slug = entry["slug"]

            entry_type = entry.get("type")
            if entry_type not in ("user", "assistant"):
                continue

            content = entry.get("message", {}).get("content", [])
            timestamp = entry.get("timestamp")

            if isinstance(content, str):
                text = content.strip()
                if text and not (text.startswith("[") and text.endswith("]")):
                    # Skip hook-injected skill content (PreToolUse hook stdout)
                    if text.startswith("Base directory for this skill:"):
                        continue
                    messages.append({"role": entry_type, "text": text, "tool_calls": [], "timestamp": timestamp})
                continue

            if not isinstance(content, list):
                continue

            text_parts = []
            tool_calls = []
            has_only_tool_results = all(
                b.get("type") == "tool_result" for b in content if isinstance(b, dict)
            )

            if has_only_tool_results:
                continue  # skip noise — tool results are already in spans

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    text = block.get("text", "").strip()
                    # Skip system-injected bracket messages
                    if text and not (text.startswith("[") and text.endswith("]")):
                        text_parts.append(text)
                elif btype == "tool_use":
                    tool_calls.append({"name": block.get("name", ""), "id": block.get("id", "")})
                # skip: thinking, tool_result, other

            text = "\n\n".join(text_parts)

            # Skip if nothing meaningful
            if not text and not tool_calls:
                continue

            # Skip hook-injected skill content (PreToolUse hook stdout)
            if entry_type == "user" and text.startswith("Base directory for this skill:"):
                continue

            messages.append({
                "role": entry_type,
                "text": text,
                "tool_calls": tool_calls,
                "timestamp": timestamp,
            })

    return {
        "session_id": session_id,
        "slug": slug,
        "messages": messages,
        "truncated": lines_read > MAX_LINES or len(messages) >= MAX_MESSAGES,
    }


# ---------------------------------------------------------------------------
# Knowledge base endpoints (agent-memory repo via Gitea)
# ---------------------------------------------------------------------------

class KnowledgeFile(BaseModel):
    path: str
    name: str
    kind: str  # "agents_md" | "skill"
    skill_name: Optional[str] = None


class KnowledgeFileContent(BaseModel):
    path: str
    content: str
    sha: str
    size: int


class KnowledgeUpdateRequest(BaseModel):
    path: str
    content: str
    sha: str
    message: Optional[str] = None


def _gitea_headers() -> dict:
    headers = {"Accept": "application/json"}
    if GITEA_TOKEN:
        headers["Authorization"] = f"token {GITEA_TOKEN}"
    return headers


@app.get("/api/knowledge/tree", response_model=list[KnowledgeFile])
async def get_knowledge_tree():
    """List AGENTS.md and all skills from the agent-memory repo."""
    files: list[KnowledgeFile] = []

    async with httpx.AsyncClient(timeout=15) as client:
        # Always include AGENTS.md at the top
        files.append(KnowledgeFile(path="AGENTS.md", name="AGENTS.md", kind="agents_md"))

        # List skills/ directory
        skills_url = f"{GITEA_URL}/api/v1/repos/{KNOWLEDGE_REPO}/contents/skills"
        resp = await client.get(skills_url, headers=_gitea_headers())
        if resp.status_code == 200:
            entries = resp.json()
            for entry in sorted(entries, key=lambda e: e.get("name", "")):
                if entry.get("type") == "dir":
                    skill_name = entry["name"]
                    files.append(KnowledgeFile(
                        path=f"skills/{skill_name}/SKILL.md",
                        name=f"{skill_name}",
                        kind="skill",
                        skill_name=skill_name,
                    ))
        elif resp.status_code not in (404, 200):
            logger.warning(f"Gitea skills listing returned {resp.status_code}")

    return files


@app.get("/api/knowledge/file", response_model=KnowledgeFileContent)
async def get_knowledge_file(path: str = Query(..., description="File path in repo")):
    """Fetch a file's content and SHA from the agent-memory repo."""
    url = f"{GITEA_URL}/api/v1/repos/{KNOWLEDGE_REPO}/contents/{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_gitea_headers())

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Gitea returned {resp.status_code}")

    data = resp.json()
    raw_content = data.get("content", "")
    # Gitea returns base64-encoded content with possible newlines
    decoded = base64.b64decode(raw_content.replace("\n", "")).decode("utf-8")

    return KnowledgeFileContent(
        path=path,
        content=decoded,
        sha=data.get("sha", ""),
        size=data.get("size", len(decoded)),
    )


@app.put("/api/knowledge/file", response_model=KnowledgeFileContent)
async def update_knowledge_file(req: KnowledgeUpdateRequest):
    """Commit a file update to the agent-memory repo via Gitea."""
    url = f"{GITEA_URL}/api/v1/repos/{KNOWLEDGE_REPO}/contents/{req.path}"
    message = req.message or f"Update {req.path} via fleet gateway"
    encoded_content = base64.b64encode(req.content.encode("utf-8")).decode("ascii")

    payload = {
        "message": message,
        "content": encoded_content,
        "sha": req.sha,
    }

    headers = _gitea_headers()
    headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.put(url, json=payload, headers=headers)

    if resp.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict: SHA mismatch. Reload and try again.")
    if resp.status_code not in (200, 201):
        detail = resp.text[:500] if resp.text else f"Gitea returned {resp.status_code}"
        raise HTTPException(status_code=502, detail=detail)

    data = resp.json()
    file_data = data.get("content", {})
    return KnowledgeFileContent(
        path=req.path,
        content=req.content,
        sha=file_data.get("sha", req.sha),
        size=file_data.get("size", len(req.content)),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
