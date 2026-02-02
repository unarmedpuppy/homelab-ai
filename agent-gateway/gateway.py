"""Agent Gateway - FastAPI application for fleet monitoring."""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_config
from health import HealthMonitor
from models import Agent, AgentDetails, AgentStatus, FleetStats


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

    # Convert to AgentDetails (currently same as Agent, but allows for extension)
    return AgentDetails(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        endpoint=agent.endpoint,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
