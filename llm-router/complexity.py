"""
Request source classification for context capping.

Simplified from the original complexity classifier — routing no longer
uses complexity tiers. This module now only identifies agent vs interactive
callers so the router can apply dynamic context limits.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_3090_MODEL = os.getenv("DEFAULT_3090_MODEL", "qwopus3.5-27b-v3")

# Source headers that identify agent-like callers
_AGENT_SOURCES = {"n8n", "agent", "agent-harness", "willow"}


def is_agent_request(request, api_key=None) -> bool:
    """
    Determine if a request is from an agent (vs interactive user).

    Checks:
    1. X-Source header matches a known agent source
    2. API key name starts with 'agent-' or 'critical-'
    3. API key metadata has priority == 0
    """
    headers = getattr(request, "headers", {})

    # X-Source header
    source = headers.get("x-source", "").lower().strip()
    if source in _AGENT_SOURCES:
        return True

    # API key name prefix
    if api_key:
        name = getattr(api_key, "name", "")
        if name.lower().startswith("agent-") or name.lower().startswith("critical-"):
            return True

        # Explicit priority in metadata
        metadata = getattr(api_key, "metadata", None)
        if isinstance(metadata, dict):
            try:
                if int(metadata.get("priority", 1)) == 0:
                    return True
            except (ValueError, TypeError):
                pass

    return False
