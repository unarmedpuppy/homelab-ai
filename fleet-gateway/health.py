"""Health monitoring for Agent Gateway."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from models import (
    Agent,
    AgentConfig,
    AgentHealth,
    AgentStatus,
    AgentType,
    FleetStats,
    GatewayConfig,
)

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Background health monitor that polls agent /health endpoints.

    Handles graceful offline detection:
    - Timeout → increment failure count
    - Consecutive failures >= threshold → mark offline
    - No crashes on unreachable agents
    """

    def __init__(self, config: GatewayConfig):
        self.config = config
        self.agents: dict[str, Agent] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False

        # Initialize agents from config
        for agent_id, agent_config in config.agents.items():
            self.agents[agent_id] = Agent(
                id=agent_id,
                name=agent_config.name,
                description=agent_config.description,
                endpoint=agent_config.endpoint,
                agent_type=agent_config.agent_type,
                expected_online=agent_config.expected_online,
                tags=agent_config.tags,
                health=AgentHealth(),
            )

        logger.info(f"HealthMonitor initialized with {len(self.agents)} agents")

    async def start(self):
        """Start the background health check loop."""
        if self._running:
            logger.warning("HealthMonitor already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(
            f"HealthMonitor started (interval={self.config.health_check.interval_seconds}s)"
        )

    async def stop(self):
        """Stop the background health check loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("HealthMonitor stopped")

    async def _health_check_loop(self):
        """Background loop that checks all agents periodically."""
        # Run initial check immediately
        await self._check_all_agents()

        while self._running:
            await asyncio.sleep(self.config.health_check.interval_seconds)
            if self._running:
                await self._check_all_agents()

    async def _check_all_agents(self):
        """Check health of all agents concurrently. Skips CLI agents."""
        tasks = [
            self._check_agent(agent_id)
            for agent_id, agent in self.agents.items()
            if agent.agent_type == AgentType.SERVER
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_agent(self, agent_id: str):
        """
        Check health of a single agent.

        Handles:
        - Successful response → online, reset failures
        - Timeout → increment failures, mark offline if threshold reached
        - Connection error → increment failures, mark offline if threshold reached
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return

        now = datetime.now(timezone.utc)
        timeout = self.config.health_check.timeout_seconds

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(f"{agent.endpoint}/health")
                end_time = asyncio.get_event_loop().time()
                response_time_ms = (end_time - start_time) * 1000

                if response.status_code == 200:
                    # Success
                    data = response.json()
                    agent.health = AgentHealth(
                        status=AgentStatus.ONLINE,
                        last_check=now,
                        last_success=now,
                        response_time_ms=response_time_ms,
                        consecutive_failures=0,
                        error=None,
                        version=data.get("version"),
                    )
                    logger.debug(
                        f"Agent {agent_id} healthy ({response_time_ms:.0f}ms)"
                    )
                else:
                    # Non-200 response
                    await self._mark_failure(
                        agent,
                        now,
                        f"HTTP {response.status_code}",
                    )

        except httpx.TimeoutException:
            await self._mark_failure(agent, now, "Timeout")

        except httpx.ConnectError as e:
            await self._mark_failure(agent, now, f"Connection failed: {e}")

        except Exception as e:
            await self._mark_failure(agent, now, f"Unexpected error: {e}")
            logger.exception(f"Unexpected error checking agent {agent_id}")

    async def _mark_failure(self, agent: Agent, now: datetime, error: str):
        """Mark a health check failure and update status accordingly."""
        failures = agent.health.consecutive_failures + 1
        threshold = self.config.health_check.failure_threshold

        # Determine status based on failure count
        if failures >= threshold:
            status = AgentStatus.OFFLINE
        elif failures > 0:
            status = AgentStatus.DEGRADED
        else:
            status = AgentStatus.UNKNOWN

        agent.health = AgentHealth(
            status=status,
            last_check=now,
            last_success=agent.health.last_success,
            response_time_ms=None,
            consecutive_failures=failures,
            error=error,
            version=agent.health.version,
        )

        logger.debug(
            f"Agent {agent.id} failure #{failures}: {error} (status={status.value})"
        )

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a single agent by ID."""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> list[Agent]:
        """Get all agents with current health status."""
        return list(self.agents.values())

    def get_stats(self) -> FleetStats:
        """Calculate fleet-wide statistics. Only server agents count for health stats."""
        agents = self.get_all_agents()
        server_agents = [a for a in agents if a.agent_type == AgentType.SERVER]

        online = [a for a in server_agents if a.health.status == AgentStatus.ONLINE]
        offline = [a for a in server_agents if a.health.status == AgentStatus.OFFLINE]
        degraded = [a for a in server_agents if a.health.status == AgentStatus.DEGRADED]
        unknown = [a for a in server_agents if a.health.status == AgentStatus.UNKNOWN]

        expected_online = [a for a in server_agents if a.expected_online]
        unexpected_offline = [
            a for a in expected_online
            if a.health.status in (AgentStatus.OFFLINE, AgentStatus.UNKNOWN)
        ]

        response_times = [
            a.health.response_time_ms
            for a in online
            if a.health.response_time_ms is not None
        ]
        avg_response_time = (
            sum(response_times) / len(response_times)
            if response_times
            else None
        )

        return FleetStats(
            total_agents=len(agents),
            online_count=len(online),
            offline_count=len(offline),
            degraded_count=len(degraded),
            unknown_count=len(unknown),
            expected_online_count=len(expected_online),
            unexpected_offline_count=len(unexpected_offline),
            avg_response_time_ms=avg_response_time,
            last_updated=datetime.now(timezone.utc),
        )

    async def check_now(self, agent_id: Optional[str] = None):
        """
        Force an immediate health check.

        Args:
            agent_id: If provided, check only this agent. Otherwise check all.
        """
        if agent_id:
            await self._check_agent(agent_id)
        else:
            await self._check_all_agents()
