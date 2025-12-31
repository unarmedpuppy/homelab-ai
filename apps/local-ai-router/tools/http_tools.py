"""HTTP tools for API interactions.

Tools:
- http_get: Make GET requests to APIs
- http_post: Make POST requests (webhooks, APIs)
- http_head: Check if URL exists (HEAD request)
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

from .registry import register_tool

# =============================================================================
# Configuration
# =============================================================================

# Timeout for HTTP requests
HTTP_TIMEOUT = int(os.getenv("AGENT_HTTP_TIMEOUT", "30"))

# Maximum response size to return (prevent memory issues)
MAX_RESPONSE_SIZE = int(os.getenv("AGENT_HTTP_MAX_SIZE", "100000"))  # 100KB

# Blocked URL patterns (security)
BLOCKED_URL_PATTERNS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.",  # Link-local
    "10.",       # Private
    "172.16.",   # Private
    "172.17.",   # Docker default
    "172.18.",   # Docker
    "172.19.",   # Docker
    "192.168.",  # Private
]

# Allow internal network if explicitly enabled
ALLOW_INTERNAL = os.getenv("AGENT_HTTP_ALLOW_INTERNAL", "true").lower() == "true"


# =============================================================================
# Helpers
# =============================================================================

def _validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a URL for safety.
    
    Returns:
        (is_valid, error_or_normalized_url)
    """
    if not url:
        return False, "URL is required"
    
    # Parse URL
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"Invalid URL: {e}"
    
    # Require http or https
    if parsed.scheme not in ("http", "https"):
        return False, f"URL scheme must be http or https, got: {parsed.scheme}"
    
    # Check for blocked patterns (unless internal allowed)
    if not ALLOW_INTERNAL:
        hostname = parsed.hostname or ""
        for pattern in BLOCKED_URL_PATTERNS:
            if pattern in hostname:
                return False, f"Access to internal/private URLs is blocked: {hostname}"
    
    return True, url


def _make_request(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    data: Optional[str] = None,
    timeout: int = HTTP_TIMEOUT
) -> tuple[int, dict, str]:
    """
    Make an HTTP request.
    
    Returns:
        (status_code, response_headers, body)
    """
    req = urllib.request.Request(url, method=method)
    
    # Set headers
    req.add_header("User-Agent", "LocalAI-Agent/1.0")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    # Set body for POST/PUT
    if data:
        if isinstance(data, str):
            req.data = data.encode("utf-8")
        elif isinstance(data, bytes):
            req.data = data
        else:
            req.data = str(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            resp_headers = dict(response.headers)
            body = response.read(MAX_RESPONSE_SIZE).decode("utf-8", errors="replace")
            return status, resp_headers, body
            
    except urllib.error.HTTPError as e:
        body = e.read(MAX_RESPONSE_SIZE).decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers), body
        
    except urllib.error.URLError as e:
        raise Exception(f"Connection failed: {e.reason}")


# =============================================================================
# HTTP GET Tool
# =============================================================================

def _http_get(arguments: dict, working_dir: str) -> str:
    """Make an HTTP GET request."""
    url = arguments.get("url", "")
    headers = arguments.get("headers", {})
    timeout = arguments.get("timeout", HTTP_TIMEOUT)
    
    # Validate URL
    valid, result = _validate_url(url)
    if not valid:
        return f"Error: {result}"
    
    try:
        status, resp_headers, body = _make_request(
            url,
            method="GET",
            headers=headers,
            timeout=timeout
        )
        
        # Format response
        content_type = resp_headers.get("Content-Type", "")
        
        # Try to pretty-print JSON
        if "application/json" in content_type:
            try:
                parsed = json.loads(body)
                body = json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                pass
        
        # Truncate if too long
        if len(body) > MAX_RESPONSE_SIZE:
            body = body[:MAX_RESPONSE_SIZE] + "\n... (truncated)"
        
        return f"Status: {status}\nContent-Type: {content_type}\n\n{body}"
        
    except Exception as e:
        return f"Error: {e}"


register_tool(
    name="http_get",
    description="Make an HTTP GET request to fetch data from an API or URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to request"
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include (e.g., {'Authorization': 'Bearer xxx'})"
            },
            "timeout": {
                "type": "integer",
                "description": f"Request timeout in seconds (default: {HTTP_TIMEOUT})"
            }
        },
        "required": ["url"]
    },
    handler=_http_get
)


# =============================================================================
# HTTP POST Tool
# =============================================================================

def _http_post(arguments: dict, working_dir: str) -> str:
    """Make an HTTP POST request."""
    url = arguments.get("url", "")
    body = arguments.get("body", "")
    headers = arguments.get("headers", {})
    content_type = arguments.get("content_type", "application/json")
    timeout = arguments.get("timeout", HTTP_TIMEOUT)
    
    # Validate URL
    valid, result = _validate_url(url)
    if not valid:
        return f"Error: {result}"
    
    # Set content type
    if "Content-Type" not in headers:
        headers["Content-Type"] = content_type
    
    # Serialize body if dict
    if isinstance(body, dict):
        if "json" in content_type:
            body = json.dumps(body)
        else:
            body = urllib.parse.urlencode(body)
    
    try:
        status, resp_headers, response_body = _make_request(
            url,
            method="POST",
            headers=headers,
            data=body,
            timeout=timeout
        )
        
        # Format response
        resp_content_type = resp_headers.get("Content-Type", "")
        
        # Try to pretty-print JSON
        if "application/json" in resp_content_type:
            try:
                parsed = json.loads(response_body)
                response_body = json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                pass
        
        # Truncate if too long
        if len(response_body) > MAX_RESPONSE_SIZE:
            response_body = response_body[:MAX_RESPONSE_SIZE] + "\n... (truncated)"
        
        return f"Status: {status}\nContent-Type: {resp_content_type}\n\n{response_body}"
        
    except Exception as e:
        return f"Error: {e}"


register_tool(
    name="http_post",
    description="Make an HTTP POST request to send data to an API or webhook.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to POST to"
            },
            "body": {
                "type": ["string", "object"],
                "description": "Request body (string or object for JSON)"
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include"
            },
            "content_type": {
                "type": "string",
                "description": "Content-Type header (default: application/json)"
            },
            "timeout": {
                "type": "integer",
                "description": f"Request timeout in seconds (default: {HTTP_TIMEOUT})"
            }
        },
        "required": ["url"]
    },
    handler=_http_post
)


# =============================================================================
# HTTP HEAD Tool
# =============================================================================

def _http_head(arguments: dict, working_dir: str) -> str:
    """Make an HTTP HEAD request to check URL status."""
    url = arguments.get("url", "")
    headers = arguments.get("headers", {})
    timeout = arguments.get("timeout", HTTP_TIMEOUT)
    
    # Validate URL
    valid, result = _validate_url(url)
    if not valid:
        return f"Error: {result}"
    
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", "LocalAI-Agent/1.0")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            resp_headers = dict(response.headers)
            
            # Format key headers
            info = {
                "status": status,
                "content_type": resp_headers.get("Content-Type", ""),
                "content_length": resp_headers.get("Content-Length", "unknown"),
                "last_modified": resp_headers.get("Last-Modified", ""),
                "server": resp_headers.get("Server", ""),
            }
            
            return json.dumps(info, indent=2)
            
    except urllib.error.HTTPError as e:
        return f"Status: {e.code} ({e.reason})"
    except urllib.error.URLError as e:
        return f"Error: Connection failed - {e.reason}"
    except Exception as e:
        return f"Error: {e}"


register_tool(
    name="http_head",
    description="Make an HTTP HEAD request to check if a URL exists and get headers (no body).",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to check"
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include"
            },
            "timeout": {
                "type": "integer",
                "description": f"Request timeout in seconds (default: {HTTP_TIMEOUT})"
            }
        },
        "required": ["url"]
    },
    handler=_http_head
)
