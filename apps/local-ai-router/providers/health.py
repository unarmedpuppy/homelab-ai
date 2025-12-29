"""
Health Checker - Background task for monitoring provider health.
"""
import asyncio
import logging
import time
from typing import Optional, Dict
import httpx

from .models import Provider, ProviderType

logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Result of a health check."""

    def __init__(self, provider_id: str, is_healthy: bool, response_time_ms: Optional[float] = None, error: Optional[str] = None):
        self.provider_id = provider_id
        self.is_healthy = is_healthy
        self.response_time_ms = response_time_ms
        self.error = error
        self.timestamp = time.time()


class HealthChecker:
    """
    Background health checker for providers.

    Features:
    - Periodic health checks based on provider configuration
    - Consecutive failure tracking
    - Health cache with timestamps
    - Automatic provider status updates
    """

    def __init__(self, provider_manager, check_interval: Optional[int] = None):
        """
        Initialize the health checker.

        Args:
            provider_manager: ProviderManager instance to check and update
            check_interval: Override check interval in seconds (for testing)
        """
        self.provider_manager = provider_manager
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._health_cache: Dict[str, HealthCheckResult] = {}
        self._consecutive_failures: Dict[str, int] = {}

        # Thresholds
        self.max_consecutive_failures = 3  # Mark unhealthy after 3 failures

    async def start(self):
        """Start the background health checker."""
        if self._running:
            logger.warning("HealthChecker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_health_checks())
        logger.info("HealthChecker started")

    async def stop(self):
        """Stop the background health checker."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HealthChecker stopped")

    async def _run_health_checks(self):
        """Main loop for running health checks."""
        while self._running:
            try:
                await self._check_all_providers()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)

            # Use the configured check interval or default to 30s
            interval = self.check_interval or 30
            await asyncio.sleep(interval)

    async def _check_all_providers(self):
        """Check health of all enabled providers."""
        providers = self.provider_manager.get_all_providers()

        # Create tasks for all providers
        tasks = []
        for provider in providers:
            if not provider.enabled:
                continue

            # Check if we need to check this provider based on its interval
            if self._should_check_provider(provider):
                tasks.append(self._check_provider_health(provider))

        # Run all health checks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Health check exception: {result}")
                elif isinstance(result, HealthCheckResult):
                    self._process_health_result(result)

    def _should_check_provider(self, provider: Provider) -> bool:
        """
        Determine if a provider should be checked based on its health check interval.

        Args:
            provider: Provider to check

        Returns:
            True if provider should be checked now
        """
        # If no cached result, always check
        if provider.id not in self._health_cache:
            return True

        # Check if enough time has passed since last check
        last_check = self._health_cache[provider.id].timestamp
        interval = provider.health_check_interval
        return (time.time() - last_check) >= interval

    async def _check_provider_health(self, provider: Provider) -> HealthCheckResult:
        """
        Perform health check for a single provider.

        Args:
            provider: Provider to check

        Returns:
            HealthCheckResult with check outcome
        """
        start_time = time.time()

        try:
            # Build health check URL
            health_url = f"{provider.endpoint.rstrip('/')}{provider.health_check_path}"

            # Perform health check
            timeout = httpx.Timeout(provider.health_check_timeout)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(health_url)

                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000

                # Check if response is healthy (2xx status code)
                is_healthy = response.status_code // 100 == 2

                if is_healthy:
                    logger.debug(f"Provider {provider.id} health check passed ({response_time_ms:.0f}ms)")
                    return HealthCheckResult(
                        provider_id=provider.id,
                        is_healthy=True,
                        response_time_ms=response_time_ms
                    )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    logger.warning(f"Provider {provider.id} health check failed: {error_msg}")
                    return HealthCheckResult(
                        provider_id=provider.id,
                        is_healthy=False,
                        response_time_ms=response_time_ms,
                        error=error_msg
                    )

        except httpx.TimeoutException:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {response_time_ms:.0f}ms"
            logger.warning(f"Provider {provider.id} health check timeout: {error_msg}")
            return HealthCheckResult(
                provider_id=provider.id,
                is_healthy=False,
                response_time_ms=response_time_ms,
                error=error_msg
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Provider {provider.id} health check error: {error_msg}")
            return HealthCheckResult(
                provider_id=provider.id,
                is_healthy=False,
                response_time_ms=response_time_ms,
                error=error_msg
            )

    def _process_health_result(self, result: HealthCheckResult):
        """
        Process health check result and update provider status.

        Args:
            result: HealthCheckResult to process
        """
        # Cache the result
        self._health_cache[result.provider_id] = result

        # Get provider from manager
        provider = self.provider_manager.get_provider(result.provider_id)
        if not provider:
            logger.warning(f"Provider {result.provider_id} not found in manager")
            return

        # Update consecutive failures
        if result.is_healthy:
            # Reset consecutive failures on success
            self._consecutive_failures[result.provider_id] = 0

            # Mark provider as healthy
            if not provider.is_healthy:
                logger.info(f"Provider {result.provider_id} is now healthy")
                provider.is_healthy = True

        else:
            # Increment consecutive failures
            failures = self._consecutive_failures.get(result.provider_id, 0) + 1
            self._consecutive_failures[result.provider_id] = failures

            # Mark provider as unhealthy if threshold exceeded
            if failures >= self.max_consecutive_failures and provider.is_healthy:
                logger.warning(
                    f"Provider {result.provider_id} marked unhealthy after "
                    f"{failures} consecutive failures (last error: {result.error})"
                )
                provider.is_healthy = False
                provider.consecutive_failures = failures
            else:
                provider.consecutive_failures = failures

        # Update last health check timestamp
        provider.last_health_check = result.timestamp

    def get_health_status(self, provider_id: str) -> Optional[HealthCheckResult]:
        """
        Get cached health status for a provider.

        Args:
            provider_id: Provider ID to get status for

        Returns:
            HealthCheckResult or None if no cached result
        """
        return self._health_cache.get(provider_id)

    def get_all_health_status(self) -> Dict[str, HealthCheckResult]:
        """
        Get all cached health statuses.

        Returns:
            Dict mapping provider_id to HealthCheckResult
        """
        return dict(self._health_cache)

    async def force_check(self, provider_id: str) -> Optional[HealthCheckResult]:
        """
        Force an immediate health check for a provider.

        Args:
            provider_id: Provider ID to check

        Returns:
            HealthCheckResult or None if provider not found
        """
        provider = self.provider_manager.get_provider(provider_id)
        if not provider:
            logger.warning(f"Provider {provider_id} not found")
            return None

        result = await self._check_provider_health(provider)
        self._process_health_result(result)
        return result
