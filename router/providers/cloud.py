"""
Cloud provider utilities for API requests.

Handles endpoint URL construction and authentication for cloud providers
like Z.ai and Anthropic.
"""
import os
import logging
from typing import Dict, Optional

from .models import Provider, ProviderType, AuthType

logger = logging.getLogger(__name__)


def get_api_key(provider: Provider) -> Optional[str]:
    """
    Get API key for a cloud provider from environment.
    
    Returns None if provider doesn't require auth or key not found.
    """
    if not provider.auth_type or provider.auth_type == AuthType.NONE:
        return None
    
    if not provider.auth_secret:
        logger.warning(f"Provider {provider.id} has auth_type but no auth_secret configured")
        return None
    
    api_key = os.getenv(provider.auth_secret)
    if not api_key:
        logger.warning(f"API key not found in env var: {provider.auth_secret}")
    return api_key


def get_auth_headers(provider: Provider) -> Dict[str, str]:
    """
    Build authentication headers for a provider.
    
    Returns empty dict for local providers or if no auth configured.
    """
    if provider.type == ProviderType.LOCAL:
        return {}
    
    api_key = get_api_key(provider)
    if not api_key:
        return {}
    
    if provider.auth_type == AuthType.BEARER:
        return {"Authorization": f"Bearer {api_key}"}
    elif provider.auth_type == AuthType.API_KEY:
        return {"X-API-Key": api_key}
    
    return {}


def build_chat_completions_url(provider: Provider) -> str:
    """
    Build the chat completions endpoint URL for a provider.
    
    - Local providers (vLLM): /v1/chat/completions
    - Cloud providers (Z.ai): /chat/completions (Z.ai base includes /api/paas/v4)
    """
    base_url = provider.endpoint.rstrip('/')
    
    if provider.type == ProviderType.CLOUD:
        return f"{base_url}/chat/completions"
    else:
        return f"{base_url}/v1/chat/completions"


def build_request_headers(provider: Provider, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Build complete request headers for a provider.
    
    Includes Content-Type and auth headers.
    """
    headers = {"Content-Type": "application/json"}
    headers.update(get_auth_headers(provider))
    
    if extra_headers:
        headers.update(extra_headers)
    
    return headers
