"""
API Authentication
==================

Authentication utilities for API key validation.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

# API Key header security
api_key_header = APIKeyHeader(
    name=settings.api.api_key_header,
    auto_error=False
)


def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Validate API key from header
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key or None if auth disabled
        
    Raises:
        HTTPException: If authentication is required and key is invalid
    """
    # If authentication is disabled, allow all requests
    if not settings.api.auth_enabled:
        return None
    
    # If auth is enabled but no key provided, reject
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide API key in X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate key
    valid_keys = settings.api.api_keys
    if not valid_keys:
        logger.warning("API authentication enabled but no valid keys configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication misconfigured",
        )
    
    if api_key not in valid_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


def require_api_key(api_key: Optional[str] = Security(get_api_key)) -> str:
    """
    Dependency that requires valid API key
    
    Use this in route dependencies for endpoints that require authentication:
    
    @router.get("/protected")
    async def protected_endpoint(api_key: str = Depends(require_api_key)):
        ...
    """
    if settings.api.auth_enabled and not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    return api_key or ""


def optional_api_key(api_key: Optional[str] = Security(get_api_key)) -> Optional[str]:
    """
    Dependency that optionally validates API key
    
    Use this for endpoints that work with or without authentication:
    
    @router.get("/public")
    async def public_endpoint(api_key: Optional[str] = Depends(optional_api_key)):
        ...
    """
    return api_key

