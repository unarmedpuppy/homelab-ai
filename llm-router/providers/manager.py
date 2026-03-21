"""
Provider Manager - Intelligent routing with concurrency awareness.
"""
import os
import re
import yaml
import logging
import asyncio
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path
from contextlib import asynccontextmanager

from .models import (
    Provider,
    Model,
    ProviderConfig,
    ProviderSelection,
    ProviderType,
    AuthType,
    ModelCapabilities,
)
from .model_state import ModelStateTracker, ModelState, ModelLoadState

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages providers and models with intelligent routing.

    Features:
    - Load from YAML configuration
    - Environment variable overrides
    - Concurrency tracking per provider
    - Priority-based selection
    - Health status awareness
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the provider manager.

        Args:
            config_path: Path to providers.yaml (defaults to CONFIG_PATH env var)
        """
        self.config_path = config_path or os.getenv(
            "CONFIG_PATH", "/app/config/providers.yaml"
        )
        self.providers: Dict[str, Provider] = {}
        self.models: Dict[str, Model] = {}
        self.settings: Dict = {}
        self._lock = asyncio.Lock()

        # Queue state: waiters blocked on a busy provider
        self._slot_event = asyncio.Event()
        self._queue_depth = 0
        self.max_queue_depth = int(os.getenv("QUEUE_MAX_DEPTH", "20"))
        self.queue_timeout = float(os.getenv("QUEUE_TIMEOUT_SECONDS", "120"))

        # Circuit breaker: track consecutive inference failures (timeout/connect)
        # Distinct from health check failures — this fires on actual request failures.
        self._inference_failures: Dict[str, int] = {}
        self.inference_failure_threshold = int(os.getenv("INFERENCE_FAILURE_THRESHOLD", "2"))
        
        # Model state tracker for warm/cold detection
        self.model_state_tracker = ModelStateTracker(
            warmth_timeout=float(os.getenv("MODEL_WARMTH_TIMEOUT", "300")),
            default_warmup_ms=float(os.getenv("DEFAULT_WARMUP_MS", "5000")),
        )

        # Load configuration
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self):
        """Load providers and models from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return

            with open(config_file, "r") as f:
                raw_config = yaml.safe_load(f)

            raw_config = self._expand_env_vars(raw_config)

            # Parse providers
            for p in raw_config.get("providers", []):
                # Convert camelCase keys to snake_case
                provider_data = self._convert_keys(p)
                provider = Provider(**provider_data)
                self.providers[provider.id] = provider
                logger.info(f"Loaded provider: {provider.id} ({provider.name})")

            # Parse models
            for m in raw_config.get("models", []):
                model_data = self._convert_keys(m)
                # Handle nested capabilities
                if "capabilities" in model_data:
                    model_data["capabilities"] = ModelCapabilities(
                        **model_data["capabilities"]
                    )
                model = Model(**model_data)
                self.models[model.id] = model
                logger.info(f"Loaded model: {model.id} ({model.name})")

            # Store settings
            self.settings = raw_config.get("settings", {})
            logger.info(f"Loaded {len(self.providers)} providers, {len(self.models)} models")

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise

    def _convert_keys(self, data: Dict) -> Dict:
        """Convert camelCase keys to snake_case."""
        result = {}
        for key, value in data.items():
            # Convert camelCase to snake_case
            snake_key = "".join(
                ["_" + c.lower() if c.isupper() else c for c in key]
            ).lstrip("_")
            result[snake_key] = value
        return result

    def _expand_env_vars(self, value: Any) -> Any:
        """
        Recursively expand ${VAR:-default} style environment variables in values.
        
        Handles:
        - ${VAR} - replaced with env var or empty string
        - ${VAR:-default} - replaced with env var or default value
        - Nested dicts and lists
        """
        if isinstance(value, str):
            # Pattern for ${VAR} or ${VAR:-default}
            pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default = match.group(2) if match.group(2) is not None else ''
                result = os.environ.get(var_name, default)
                logger.debug(f"Expanding ${{{var_name}}}: '{result}'")
                return result
            
            return re.sub(pattern, replacer, value)
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        else:
            return value

    def _apply_env_overrides(self):
        """Apply environment variable overrides to providers."""
        for provider_id, provider in self.providers.items():
            # Endpoint override
            env_key = f"PROVIDER_{provider_id.upper().replace('-', '_')}_ENDPOINT"
            if env_endpoint := os.getenv(env_key):
                provider.endpoint = env_endpoint
                logger.info(f"Override {provider_id} endpoint: {env_endpoint}")

            # Enabled override
            env_key = f"PROVIDER_{provider_id.upper().replace('-', '_')}_ENABLED"
            if env_enabled := os.getenv(env_key):
                provider.enabled = env_enabled.lower() == "true"
                logger.info(f"Override {provider_id} enabled: {provider.enabled}")

    async def select_provider_and_model(
        self,
        requested_model: str,
        capabilities_required: Optional[Dict[str, bool]] = None,
        prefer_warm: bool = True,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> ProviderSelection:
        """
        Select the best provider and model for a request.

        Algorithm:
        1. Resolve requested model (handle aliases, "auto", etc.)
        2. Filter providers by:
           - Model availability
           - Enabled status
           - Health status
           - Required capabilities
        3. Sort providers by priority (lower number = higher priority)
        4. For each provider (in priority order):
           - Check if under concurrency limit
           - If yes, select and return
           - If no, continue to next
        5. If all providers are busy:
           - Check cloud fallback settings
           - Queue or return error

        Args:
            requested_model: Model ID, alias, or "auto"
            capabilities_required: Required model capabilities
            prefer_warm: Prefer providers with warm models
            provider_id: Optional explicit provider selection (Phase 3)
            model_id: Optional explicit model selection (Phase 3)

        Returns:
            ProviderSelection with selected provider and model

        Raises:
            ValueError: If no suitable provider/model found
        """
        async with self._lock:
            # Handle explicit provider/model selection (Phase 3)
            if provider_id and model_id:
                provider = self.providers.get(provider_id)
                if not provider:
                    raise ValueError(f"Provider not found: {provider_id}")
                # Look up model in self.models and verify it belongs to this provider
                model = self.models.get(model_id)
                if not model or model.provider_id != provider_id:
                    raise ValueError(f"Model {model_id} not found on provider {provider_id}")
                return ProviderSelection(provider=provider, model=model, reason="explicit selection")

            # "auto" routing: provider-first by priority.
            # Iterates providers in priority order, picks first healthy+available one,
            # then selects that provider's default model. This correctly handles the case
            # where the top-priority provider is unhealthy — it falls through to the next
            # tier rather than failing immediately.
            if requested_model == "auto" and not provider_id:
                result = self._select_auto(capabilities_required)
                if result:
                    model, provider = result
                    reason = (
                        f"Auto-routed to {provider.id} (priority {provider.priority}), "
                        f"{provider.current_requests}/{provider.max_concurrent} requests"
                    )
                    logger.info(f"Auto-routing: {provider.id}/{model.id}")
                    return ProviderSelection(provider=provider, model=model, reason=reason)
                raise ValueError("No healthy providers available for auto routing")

            # 1. Resolve model
            resolved_model_id = model_id or self._resolve_model(requested_model)
            if not resolved_model_id:
                raise ValueError(f"Model not found: {requested_model}")

            model = self.models.get(resolved_model_id)
            if not model:
                raise ValueError(f"Model configuration not found: {resolved_model_id}")

            # 2. Find candidate providers for this model
            candidates = self._get_candidate_providers(model, capabilities_required)

            # Filter by explicit provider if specified
            if provider_id:
                candidates = [p for p in candidates if p.id == provider_id]
                if not candidates:
                    raise ValueError(f"Provider {provider_id} not available for model {resolved_model_id}")

            if not candidates:
                raise ValueError(
                    f"No available providers for model {resolved_model_id}. "
                    f"Required capabilities: {capabilities_required}"
                )

            # 3. Sort by priority (lower = higher priority)
            candidates.sort(key=lambda p: p.priority)

            # 4. Select first available provider (not at max concurrency)
            for provider in candidates:
                if provider.current_requests < provider.max_concurrent:
                    # Found available provider
                    reason = (
                        f"Priority {provider.priority}, "
                        f"{provider.current_requests}/{provider.max_concurrent} requests"
                    )
                    return ProviderSelection(
                        provider=provider, model=model, reason=reason
                    )

            # 5. All providers at capacity — no fallback for explicit model requests
            raise ValueError(
                f"All providers for {resolved_model_id} are at capacity. "
                f"Current loads: {[(p.id, p.current_requests, p.max_concurrent) for p in candidates]}"
            )

    def _select_auto(
        self,
        capabilities_required: Optional[Dict[str, bool]] = None,
    ) -> Optional[Tuple["Model", "Provider"]]:
        """
        Provider-first auto-routing.

        Iterates providers in priority order (skipping manual-only ones with
        priority >= 99). For each provider that is enabled, healthy, and has
        an open concurrency slot, picks that provider's default model (or first
        model if no default is set). Returns the first viable (model, provider)
        pair, or None if no provider is available.

        This is the correct algorithm for "auto" — it degrades gracefully when
        any tier is unhealthy rather than failing on the first resolved model.
        """
        sorted_providers = sorted(
            [p for p in self.providers.values() if p.enabled and p.priority < 99],
            key=lambda p: p.priority,
        )

        for provider in sorted_providers:
            if not provider.is_healthy:
                logger.debug(f"Auto-routing: skipping {provider.id} (unhealthy)")
                continue
            if provider.current_requests >= provider.max_concurrent:
                logger.debug(f"Auto-routing: skipping {provider.id} (at capacity)")
                continue

            provider_models = [
                m for m in self.models.values() if m.provider_id == provider.id
            ]
            if not provider_models:
                continue

            # Check capabilities if required
            if capabilities_required:
                provider_models = [
                    m for m in provider_models
                    if all(
                        getattr(m.capabilities, cap, False)
                        for cap, required in capabilities_required.items()
                        if required
                    )
                ]
                if not provider_models:
                    continue

            model = next((m for m in provider_models if m.is_default), provider_models[0])
            return model, provider

        return None

    def _resolve_model(self, requested: str) -> Optional[str]:
        """
        Resolve model ID from request.

        Handles:
        - Direct model ID: "qwen2.5-14b-awq" -> "qwen2.5-14b-awq"
        - Alias: "fast" -> model with "fast" tag
        - Auto: "auto" -> default model
        """
        # Direct match
        if requested in self.models:
            return requested

        # Auto - return default model
        if requested == "auto":
            for model in self.models.values():
                if model.is_default:
                    return model.id
            # Fallback to first model if no default
            if self.models:
                return list(self.models.keys())[0]

        # Tag-based match (alias)
        for model in self.models.values():
            if requested in model.tags:
                return model.id

        return None

    def _get_candidate_providers(
        self,
        model: Model,
        capabilities_required: Optional[Dict[str, bool]] = None,
    ) -> List[Provider]:
        """
        Get candidate providers for a model.

        Filters by:
        - Model's provider_id
        - Enabled status
        - Health status
        - Required capabilities
        """
        candidates = []

        # Get provider for this model
        provider = self.providers.get(model.provider_id)
        if not provider:
            return []

        # Check provider status
        if not provider.enabled or not provider.is_healthy:
            return []

        # Check capabilities
        if capabilities_required:
            for cap, required in capabilities_required.items():
                if required and not getattr(model.capabilities, cap, False):
                    return []

        return [provider]

    @asynccontextmanager
    async def track_request(self, provider_id: str):
        """
        Context manager to track active requests for a provider.

        Usage:
            async with provider_manager.track_request(provider_id):
                # Make request to provider
                ...
        """
        async with self._lock:
            provider = self.providers.get(provider_id)
            if provider:
                provider.current_requests += 1
                logger.debug(
                    f"Provider {provider_id}: {provider.current_requests}/{provider.max_concurrent}"
                )

        try:
            yield
        finally:
            async with self._lock:
                provider = self.providers.get(provider_id)
                if provider and provider.current_requests > 0:
                    provider.current_requests -= 1
                    logger.debug(
                        f"Provider {provider_id}: {provider.current_requests}/{provider.max_concurrent}"
                    )
            # Pulse the slot event — wake any queued waiters
            self._slot_event.set()
            self._slot_event.clear()

    async def acquire_provider_slot(
        self,
        requested_model: str,
        *,
        priority: int = 1,
        request: Optional[Any] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> "ProviderSelection":
        """
        Select a provider slot, waiting if all providers are currently busy.

        Wraps select_provider_and_model with:
        - Immediate return if a slot is available (fast path)
        - Queue depth cap — returns 503 if queue is full
        - Slot-freed notification via asyncio.Event
        - Client disconnect detection (pass FastAPI Request as `request`)
        - Configurable timeout (QUEUE_TIMEOUT_SECONDS env, default 120s)

        Priority is informational for logging; wakeup order is not strictly
        enforced (asyncio scheduling determines which waiter wins the slot race).
        """
        timeout = timeout if timeout is not None else self.queue_timeout

        # Fast path: slot available right now
        try:
            return await self.select_provider_and_model(requested_model, **kwargs)
        except ValueError:
            pass

        # Fail fast if the model's provider is unhealthy (not just busy).
        # Only queue when providers exist and are healthy but at capacity.
        resolved = self._resolve_model(requested_model)
        if resolved:
            model = self.models.get(resolved)
            if model:
                provider = self.providers.get(model.provider_id)
                if provider and (not provider.enabled or not provider.is_healthy):
                    raise ValueError(
                        f"Provider '{provider.id}' is {'disabled' if not provider.enabled else 'unhealthy'} "
                        f"for model '{resolved}' — not queuing"
                    )
        else:
            raise ValueError(f"Model not found: {requested_model}")

        # Check queue capacity before enqueuing
        if self._queue_depth >= self.max_queue_depth:
            raise ValueError(
                f"Request queue full ({self._queue_depth}/{self.max_queue_depth}). "
                "Try again later."
            )

        self._queue_depth += 1
        logger.info(
            f"Provider busy — queuing request (priority={priority}, model={requested_model}, "
            f"depth={self._queue_depth}/{self.max_queue_depth})"
        )

        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        poll_interval = 2.0  # max seconds between retries (slot event shortens this)

        try:
            while True:
                # Check client disconnect
                if request is not None:
                    try:
                        if await request.is_disconnected():
                            raise ValueError("Client disconnected while waiting in queue")
                    except Exception:
                        pass  # is_disconnected can fail; don't abort the request

                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise ValueError(
                        f"Request timed out after {timeout}s waiting for a provider slot"
                    )

                # Wait for a slot-freed signal or poll interval, whichever comes first
                try:
                    await asyncio.wait_for(
                        self._slot_event.wait(),
                        timeout=min(remaining, poll_interval),
                    )
                except asyncio.TimeoutError:
                    pass  # poll interval elapsed; loop and retry

                # Attempt to acquire a slot now
                try:
                    selection = await self.select_provider_and_model(requested_model, **kwargs)
                    logger.info(
                        f"Queued request acquired slot "
                        f"(provider={selection.provider.id}, priority={priority}, "
                        f"waited={round(timeout - remaining, 1)}s)"
                    )
                    return selection
                except ValueError:
                    continue  # Still busy — wait for the next slot signal
        finally:
            self._queue_depth -= 1

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get provider by ID."""
        return self.providers.get(provider_id)

    def get_model(self, model_id: str) -> Optional[Model]:
        """Get model by ID."""
        return self.models.get(model_id)

    def get_all_providers(self) -> List[Provider]:
        """Get all providers."""
        return list(self.providers.values())

    def get_all_models(self) -> List[Model]:
        """Get all models."""
        return list(self.models.values())

    def get_provider_status(self) -> Dict[str, Dict]:
        """
        Get status of all providers.

        Returns:
            Dict mapping provider_id to status info
        """
        return {
            pid: {
                "name": p.name,
                "type": p.type,
                "enabled": p.enabled,
                "healthy": p.is_healthy,
                "current_requests": p.current_requests,
                "max_concurrent": p.max_concurrent,
                "priority": p.priority,
            }
            for pid, p in self.providers.items()
        }

    def get_queue_status(self) -> Dict[str, Any]:
        """Return current queue state for monitoring."""
        return {
            "depth": self._queue_depth,
            "max_depth": self.max_queue_depth,
            "timeout_seconds": self.queue_timeout,
        }

    def record_inference_failure(self, provider_id: str) -> None:
        """
        Record a consecutive inference failure (timeout or connect error) for a provider.

        After inference_failure_threshold consecutive failures the provider is marked
        unhealthy so that auto-routing falls through to the next tier immediately.
        The health checker restores is_healthy once the provider's health endpoint
        recovers, which also resets the inference failure counter.
        """
        failures = self._inference_failures.get(provider_id, 0) + 1
        self._inference_failures[provider_id] = failures

        provider = self.providers.get(provider_id)
        if not provider:
            return

        logger.warning(
            f"Inference failure on {provider_id} "
            f"({failures}/{self.inference_failure_threshold})"
        )

        if failures >= self.inference_failure_threshold and provider.is_healthy:
            logger.warning(
                f"Circuit breaker: marking {provider_id} unhealthy after "
                f"{failures} consecutive inference failures"
            )
            provider.is_healthy = False

    def record_inference_success(self, provider_id: str) -> None:
        """Reset the inference failure counter for a provider after a successful request."""
        if self._inference_failures.get(provider_id, 0) > 0:
            logger.debug(f"Inference success: resetting failure counter for {provider_id}")
            self._inference_failures[provider_id] = 0

    def reload_config(self):
        """Reload configuration from YAML file."""
        logger.info("Reloading provider configuration...")
        self._load_config()
        self._apply_env_overrides()

    def calculate_cost(
        self,
        provider_id: str,
        model_id: Optional[str],
        duration_ms: Optional[int],
        total_tokens: Optional[int],
    ) -> Optional[float]:
        """
        Calculate the cost of a request based on provider type.
        
        - Local providers: cost = (power_kw) × (duration_hours) × (electricity_rate)
        - Cloud providers: cost = (total_tokens / 1000) × (cost_per_1k_tokens)
        """
        provider = self.providers.get(provider_id)
        if not provider:
            return None

        electricity_rate = self.settings.get("electricityRateKwh", 0.166)

        if provider.type == ProviderType.LOCAL:
            if duration_ms is None or not provider.power_watts:
                return None
            power_kw = provider.power_watts / 1000.0
            duration_hours = duration_ms / 1000.0 / 3600.0
            cost = power_kw * duration_hours * electricity_rate
            return round(cost, 8)

        elif provider.type == ProviderType.CLOUD:
            model = self.models.get(model_id) if model_id else None
            if model is None or total_tokens is None:
                return None
            cost_per_1k = model.cost_per1k_tokens
            cost = (total_tokens / 1000.0) * cost_per_1k
            return round(cost, 8)

        return None

    # =========================================================================
    # Model State Tracking Methods
    # =========================================================================

    def is_model_loaded(self, provider_id: str, model_id: str) -> bool:
        """
        Check if a model is currently loaded (warm) on a provider.
        
        A warm model means it's loaded in GPU memory and ready for inference
        without startup delay.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            True if model is likely loaded in GPU memory
        """
        return self.model_state_tracker.is_model_loaded(provider_id, model_id)

    def estimate_warmup_time(
        self,
        provider_id: str,
        model_id: str,
        model_size_hint: Optional[str] = None,
    ) -> int:
        """
        Estimate warmup time for a cold model in milliseconds.
        
        Uses historical data if available, otherwise falls back to
        heuristics based on model size.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            model_size_hint: Optional size hint ("tiny", "small", "medium", "large", "xlarge")
            
        Returns:
            Estimated warmup time in milliseconds
        """
        return self.model_state_tracker.estimate_warmup_time(
            provider_id, model_id, model_size_hint
        )

    def get_model_state(self, provider_id: str, model_id: str) -> ModelState:
        """
        Get full state information for a model.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            ModelState with current state information
        """
        return self.model_state_tracker.get_model_state(provider_id, model_id)

    def mark_model_used(
        self,
        provider_id: str,
        model_id: str,
        first_token_time_ms: Optional[float] = None,
    ) -> None:
        """
        Mark that a model was successfully used.
        
        Should be called after a successful inference to update warm state.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            first_token_time_ms: Optional time to first token for warmup estimation
        """
        self.model_state_tracker.mark_model_used(
            provider_id, model_id, first_token_time_ms
        )

    def get_warm_models(self, provider_id: Optional[str] = None) -> Dict[str, ModelState]:
        """
        Get all currently warm models.
        
        Args:
            provider_id: Optional filter by provider
            
        Returns:
            Dict of "provider_id/model_id" -> ModelState for warm models
        """
        return self.model_state_tracker.get_warm_models(provider_id)
