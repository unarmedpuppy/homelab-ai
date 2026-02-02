"""Agent Gateway - FastAPI application for fleet monitoring."""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import load_config
from health import HealthMonitor
from models import Agent, AgentDetails, FleetStats, GatewayConfig

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
