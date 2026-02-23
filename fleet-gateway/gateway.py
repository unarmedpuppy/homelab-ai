"""Agent Gateway - FastAPI application for fleet monitoring."""
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_config
from health import HealthMonitor
from models import Agent, AgentDetails, AgentStatus, FleetStats, Job, JobCreateRequest, JobListResponse, JobStatus


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
