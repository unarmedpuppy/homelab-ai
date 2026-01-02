"""
Model State Tracker - Track warm/cold model states for providers.

Tracks which models are currently loaded in GPU memory (warm) vs need to be
loaded from disk (cold). This enables:
- UI feedback during model warmup ("Loading model...")
- Intelligent routing to prefer warm models
- Estimated wait time display
"""
import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ModelLoadState(str, Enum):
    """Model load state enum."""
    COLD = "cold"       # Model not loaded, needs warmup
    WARMING = "warming"  # Model currently loading
    WARM = "warm"       # Model loaded and ready


@dataclass
class ModelState:
    """State information for a specific model on a provider."""
    model_id: str
    provider_id: str
    state: ModelLoadState = ModelLoadState.COLD
    last_used: Optional[float] = None  # Unix timestamp of last request
    last_warmup_time_ms: Optional[float] = None  # Last observed warmup duration
    estimated_warmup_time_ms: float = 5000.0  # Default estimate (5 seconds)
    warmup_started_at: Optional[float] = None  # When warmup began
    request_count: int = 0  # Total requests to this model
    
    def is_warm(self, timeout_seconds: float = 300.0) -> bool:
        """
        Check if model is considered warm (loaded in memory).
        
        A model is warm if:
        1. It's explicitly in WARM state, AND
        2. It was used within the timeout period
        
        Args:
            timeout_seconds: How long a model stays warm without use (default 5 min)
            
        Returns:
            True if model is likely still loaded in GPU memory
        """
        if self.state != ModelLoadState.WARM:
            return False
        if self.last_used is None:
            return False
        return (time.time() - self.last_used) < timeout_seconds


class ModelStateTracker:
    """
    Tracks model load states across all providers.
    
    Features:
    - Track warm/cold state per model per provider
    - Estimate warmup time based on historical data
    - Automatic state transitions based on usage patterns
    - Configurable warmth timeout
    
    Usage:
        tracker = ModelStateTracker(warmth_timeout=300)
        
        # Before making request
        if not tracker.is_model_loaded("provider-1", "qwen2.5-14b"):
            estimated_time = tracker.estimate_warmup_time("provider-1", "qwen2.5-14b")
            # Show "Loading model..." UI
            
        # After successful response
        tracker.mark_model_used("provider-1", "qwen2.5-14b", first_token_time_ms=1500)
    """
    
    # Default warmup time estimates by model size (in GB VRAM)
    WARMUP_ESTIMATES_MS = {
        "tiny": 2000,      # < 2B params, ~1-2GB VRAM
        "small": 5000,     # 2-7B params, ~4-8GB VRAM
        "medium": 10000,   # 7-14B params, ~8-16GB VRAM
        "large": 20000,    # 14-30B params, ~16-24GB VRAM
        "xlarge": 40000,   # 30B+ params, >24GB VRAM
    }
    
    def __init__(
        self,
        warmth_timeout: float = 300.0,  # 5 minutes default
        default_warmup_ms: float = 5000.0,  # 5 seconds default
    ):
        """
        Initialize the model state tracker.
        
        Args:
            warmth_timeout: Seconds before a warm model is considered cold
            default_warmup_ms: Default warmup time estimate in milliseconds
        """
        self.warmth_timeout = warmth_timeout
        self.default_warmup_ms = default_warmup_ms
        self._states: Dict[Tuple[str, str], ModelState] = {}  # (provider_id, model_id) -> ModelState
        
    def _get_key(self, provider_id: str, model_id: str) -> Tuple[str, str]:
        """Get the cache key for a provider/model combination."""
        return (provider_id, model_id)
    
    def _get_or_create_state(self, provider_id: str, model_id: str) -> ModelState:
        """Get existing state or create new one."""
        key = self._get_key(provider_id, model_id)
        if key not in self._states:
            self._states[key] = ModelState(
                model_id=model_id,
                provider_id=provider_id,
                estimated_warmup_time_ms=self.default_warmup_ms,
            )
        return self._states[key]
    
    def is_model_loaded(self, provider_id: str, model_id: str) -> bool:
        """
        Check if a model is currently loaded (warm) on a provider.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            True if model is likely loaded in GPU memory
        """
        state = self._get_or_create_state(provider_id, model_id)
        return state.is_warm(self.warmth_timeout)
    
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
        state = self._get_or_create_state(provider_id, model_id)
        
        # If we have historical data, use it
        if state.last_warmup_time_ms is not None:
            return int(state.last_warmup_time_ms)
        
        # Use model size hint if provided
        if model_size_hint and model_size_hint in self.WARMUP_ESTIMATES_MS:
            return self.WARMUP_ESTIMATES_MS[model_size_hint]
        
        # Infer size from model ID (heuristic)
        model_lower = model_id.lower()
        if any(x in model_lower for x in ["70b", "72b", "65b"]):
            return self.WARMUP_ESTIMATES_MS["xlarge"]
        if any(x in model_lower for x in ["30b", "32b", "34b"]):
            return self.WARMUP_ESTIMATES_MS["large"]
        if any(x in model_lower for x in ["13b", "14b", "20b"]):
            return self.WARMUP_ESTIMATES_MS["medium"]
        if any(x in model_lower for x in ["7b", "8b"]):
            return self.WARMUP_ESTIMATES_MS["small"]
        if any(x in model_lower for x in ["1b", "2b", "3b"]):
            return self.WARMUP_ESTIMATES_MS["tiny"]
        
        # Default fallback
        return int(state.estimated_warmup_time_ms)
    
    def get_model_state(self, provider_id: str, model_id: str) -> ModelState:
        """
        Get full state information for a model.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            ModelState with current state information
        """
        return self._get_or_create_state(provider_id, model_id)
    
    def mark_warmup_started(self, provider_id: str, model_id: str) -> None:
        """
        Mark that a model is starting to warm up.
        
        Called when we detect a cold start (e.g., first request after timeout).
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
        """
        state = self._get_or_create_state(provider_id, model_id)
        state.state = ModelLoadState.WARMING
        state.warmup_started_at = time.time()
        logger.info(f"Model warmup started: {provider_id}/{model_id}")
    
    def mark_model_used(
        self,
        provider_id: str,
        model_id: str,
        first_token_time_ms: Optional[float] = None,
    ) -> None:
        """
        Mark that a model was successfully used.
        
        Updates state to WARM and records usage timestamp.
        If first_token_time_ms is provided and model was cold, updates
        warmup time estimate.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            first_token_time_ms: Time to first token (for warmup estimation)
        """
        state = self._get_or_create_state(provider_id, model_id)
        was_warming = state.state == ModelLoadState.WARMING
        
        # Update state
        state.state = ModelLoadState.WARM
        state.last_used = time.time()
        state.request_count += 1
        
        # Update warmup time estimate if we were warming up
        if was_warming and state.warmup_started_at is not None:
            actual_warmup_ms = (time.time() - state.warmup_started_at) * 1000
            # Update estimate using exponential moving average
            alpha = 0.3  # Weight for new observation
            if state.last_warmup_time_ms is not None:
                state.estimated_warmup_time_ms = (
                    alpha * actual_warmup_ms + (1 - alpha) * state.estimated_warmup_time_ms
                )
            else:
                state.estimated_warmup_time_ms = actual_warmup_ms
            state.last_warmup_time_ms = actual_warmup_ms
            state.warmup_started_at = None
            logger.info(
                f"Model warmup complete: {provider_id}/{model_id} "
                f"({actual_warmup_ms:.0f}ms, estimate now {state.estimated_warmup_time_ms:.0f}ms)"
            )
        elif first_token_time_ms is not None and not state.is_warm(self.warmth_timeout):
            # Cold start detected from first token time
            alpha = 0.3
            if state.last_warmup_time_ms is not None:
                state.estimated_warmup_time_ms = (
                    alpha * first_token_time_ms + (1 - alpha) * state.estimated_warmup_time_ms
                )
            else:
                state.estimated_warmup_time_ms = first_token_time_ms
            state.last_warmup_time_ms = first_token_time_ms
    
    def mark_model_cold(self, provider_id: str, model_id: str) -> None:
        """
        Explicitly mark a model as cold (unloaded).
        
        Called when we know a model has been unloaded (e.g., provider restart).
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
        """
        state = self._get_or_create_state(provider_id, model_id)
        state.state = ModelLoadState.COLD
        state.warmup_started_at = None
        logger.info(f"Model marked cold: {provider_id}/{model_id}")
    
    def mark_provider_cold(self, provider_id: str) -> None:
        """
        Mark all models on a provider as cold.
        
        Called when a provider goes offline or restarts.
        
        Args:
            provider_id: Provider ID
        """
        for key, state in self._states.items():
            if state.provider_id == provider_id:
                state.state = ModelLoadState.COLD
                state.warmup_started_at = None
        logger.info(f"All models on provider {provider_id} marked cold")
    
    def get_warm_models(self, provider_id: Optional[str] = None) -> Dict[str, ModelState]:
        """
        Get all currently warm models.
        
        Args:
            provider_id: Optional filter by provider
            
        Returns:
            Dict of (provider_id, model_id) -> ModelState for warm models
        """
        result = {}
        for key, state in self._states.items():
            if provider_id and state.provider_id != provider_id:
                continue
            if state.is_warm(self.warmth_timeout):
                result[f"{state.provider_id}/{state.model_id}"] = state
        return result
    
    def get_all_states(self) -> Dict[str, ModelState]:
        """
        Get all tracked model states.
        
        Returns:
            Dict of "provider_id/model_id" -> ModelState
        """
        return {
            f"{state.provider_id}/{state.model_id}": state
            for state in self._states.values()
        }
