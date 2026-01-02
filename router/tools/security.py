"""Security module for agent tools.

Handles:
- Path validation and sandboxing
- Command blocklists
- SSH host allowlists
- Audit logging
- Permission checks
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration (from environment or defaults)
# =============================================================================

# Paths the agent is allowed to access
ALLOWED_PATHS = os.getenv(
    "AGENT_ALLOWED_PATHS", 
    "/tmp,/home"
).split(",")

# Additional paths to allow (working directory always allowed)
EXTRA_ALLOWED_PATHS = os.getenv("AGENT_EXTRA_PATHS", "").split(",")

# SSH hosts the agent can connect to (configure via environment variable)
SSH_ALLOWED_HOSTS = os.getenv(
    "AGENT_SSH_HOSTS",
    "server"
).split(",")

# Git repos the agent can operate on (empty = all under allowed paths)
GIT_ALLOWED_REPOS = os.getenv("AGENT_GIT_REPOS", "").split(",")

# Shell command timeout
SHELL_TIMEOUT = int(os.getenv("AGENT_SHELL_TIMEOUT", "30"))

# =============================================================================
# Dangerous Command Patterns
# =============================================================================

# Commands that are ALWAYS blocked (catastrophic)
BLOCKED_COMMANDS = [
    r"rm\s+-rf\s+/(?!\w)",      # rm -rf / (but allow rm -rf /tmp/foo)
    r"rm\s+-rf\s+/\*",          # rm -rf /*
    r"mkfs\.",                   # Format filesystem
    r">\s*/dev/sd",             # Overwrite disk
    r"dd\s+if=.*/dev/",         # dd to device
    r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
    r"chmod\s+-R\s+777\s+/",    # Chmod 777 root
    r"chown\s+-R.*\s+/(?!\w)",  # Chown root
    r">\s*/etc/passwd",         # Overwrite passwd
    r">\s*/etc/shadow",         # Overwrite shadow
    r"curl.*\|\s*sh",           # Pipe curl to shell
    r"wget.*\|\s*sh",           # Pipe wget to shell
    r"curl.*\|\s*bash",         # Pipe curl to bash
    r"wget.*\|\s*bash",         # Pipe wget to bash
]

# Commands that require explicit permission (risky but sometimes needed)
RISKY_COMMANDS = [
    r"sudo\s+",                 # Sudo commands
    r"docker\s+rm\s+-f",        # Force remove container
    r"docker\s+system\s+prune", # Prune docker
    r"git\s+push\s+.*--force",  # Force push
    r"git\s+reset\s+--hard",    # Hard reset
    r"reboot",                  # Reboot system
    r"shutdown",                # Shutdown system
    r"systemctl\s+stop",        # Stop services
    r"systemctl\s+disable",     # Disable services
]

# Compiled patterns for performance
_BLOCKED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCKED_COMMANDS]
_RISKY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in RISKY_COMMANDS]

# =============================================================================
# Audit Logging
# =============================================================================

class AuditLog:
    """Simple audit logger for tool executions."""
    
    def __init__(self):
        self.log_file = os.getenv("AGENT_AUDIT_LOG", "/tmp/agent-audit.log")
        
    def log(
        self,
        tool_name: str,
        arguments: dict,
        result: str,
        success: bool,
        working_dir: str,
        duration_ms: Optional[float] = None
    ):
        """Log a tool execution."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args": arguments,
            "working_dir": working_dir,
            "success": success,
            "result_preview": result[:200] if result else None,
            "duration_ms": duration_ms
        }
        
        # Log to file
        try:
            with open(self.log_file, "a") as f:
                import json
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")
        
        # Also log to standard logger
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"AUDIT: {tool_name} success={success} dir={working_dir}"
        )

# Singleton audit logger
audit = AuditLog()

# =============================================================================
# Path Validation
# =============================================================================

def validate_path(path: str, working_dir: str) -> tuple[bool, str]:
    """
    Validate that a path is allowed and resolve it.
    
    Args:
        path: The path to validate (can be relative)
        working_dir: The working directory for relative paths
        
    Returns:
        (is_valid, resolved_path_or_error)
    """
    try:
        # Resolve the path
        if not os.path.isabs(path):
            path = os.path.join(working_dir, path)
        resolved = os.path.realpath(path)
        
        # Build list of allowed paths
        all_allowed = []
        for p in ALLOWED_PATHS + EXTRA_ALLOWED_PATHS:
            p = p.strip()
            if p:
                all_allowed.append(os.path.realpath(p))
        
        # Always allow working directory
        all_allowed.append(os.path.realpath(working_dir))
        
        # Check if path is under any allowed directory
        allowed = False
        for allowed_path in all_allowed:
            if resolved.startswith(allowed_path):
                allowed = True
                break
        
        if not allowed:
            return False, f"Path {resolved} is not in allowed directories: {all_allowed}"
        
        return True, resolved
        
    except Exception as e:
        return False, f"Invalid path: {e}"


def is_path_allowed(path: str, working_dir: str) -> bool:
    """Simple check if a path is allowed."""
    valid, _ = validate_path(path, working_dir)
    return valid


# =============================================================================
# Command Validation
# =============================================================================

def validate_command(command: str) -> tuple[bool, Optional[str]]:
    """
    Validate a shell command against blocklists.
    
    Args:
        command: The shell command to validate
        
    Returns:
        (is_allowed, error_message_if_blocked)
    """
    # Check against blocked patterns (always denied)
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(command):
            return False, f"Blocked: dangerous command pattern detected"
    
    # Check against risky patterns (log warning but allow)
    for pattern in _RISKY_PATTERNS:
        if pattern.search(command):
            logger.warning(f"RISKY COMMAND: {command[:100]}")
            # For now, allow but log. Could add permission check here.
    
    return True, None


def is_command_allowed(command: str) -> bool:
    """Simple check if a command is allowed."""
    allowed, _ = validate_command(command)
    return allowed


# =============================================================================
# SSH Host Validation
# =============================================================================

def validate_ssh_host(host: str) -> tuple[bool, Optional[str]]:
    """
    Validate an SSH host against the allowlist.
    
    Args:
        host: The hostname or IP to connect to
        
    Returns:
        (is_allowed, error_message_if_blocked)
    """
    # Normalize host (strip port if present)
    normalized = host.split(":")[0].strip().lower()
    
    # Check against allowlist
    allowed_hosts = [h.strip().lower() for h in SSH_ALLOWED_HOSTS if h.strip()]
    
    if not allowed_hosts:
        return False, "No SSH hosts configured in allowlist"
    
    if normalized in allowed_hosts:
        return True, None
    
    # Check if it's an IP that matches an allowed host
    # (simple check, could be expanded with DNS resolution)
    for allowed in allowed_hosts:
        if allowed in normalized or normalized in allowed:
            return True, None
    
    return False, f"Host '{host}' not in SSH allowlist: {allowed_hosts}"


def is_ssh_host_allowed(host: str) -> bool:
    """Simple check if an SSH host is allowed."""
    allowed, _ = validate_ssh_host(host)
    return allowed


# =============================================================================
# Git Repository Validation
# =============================================================================

def validate_git_repo(repo_path: str, working_dir: str) -> tuple[bool, str]:
    """
    Validate a git repository path.
    
    Args:
        repo_path: Path to the git repository
        working_dir: Working directory for relative paths
        
    Returns:
        (is_valid, resolved_path_or_error)
    """
    # First validate the path itself
    valid, resolved = validate_path(repo_path, working_dir)
    if not valid:
        return False, resolved
    
    # Check if it's actually a git repo
    git_dir = os.path.join(resolved, ".git")
    if not os.path.isdir(git_dir):
        return False, f"Not a git repository: {resolved}"
    
    # Check against repo allowlist (if configured)
    allowed_repos = [r.strip() for r in GIT_ALLOWED_REPOS if r.strip()]
    if allowed_repos:
        repo_allowed = False
        for allowed in allowed_repos:
            if resolved.startswith(os.path.realpath(allowed)):
                repo_allowed = True
                break
        if not repo_allowed:
            return False, f"Repository not in allowlist: {resolved}"
    
    return True, resolved


# =============================================================================
# Permission System (Future Expansion)
# =============================================================================

class Permissions:
    """
    Permission system for fine-grained control.
    
    Future: Could integrate with API keys, user roles, etc.
    """
    
    def __init__(self):
        # Default permissions (can be overridden per-request)
        self.can_read = True
        self.can_write = True
        self.can_execute = True
        self.can_ssh = True
        self.can_git_push = True
        self.can_docker = True
        self.can_deploy = True
    
    def check(self, action: str) -> bool:
        """Check if an action is permitted."""
        permission_map = {
            "read": self.can_read,
            "write": self.can_write,
            "execute": self.can_execute,
            "shell": self.can_execute,
            "ssh": self.can_ssh,
            "git_push": self.can_git_push,
            "git_write": self.can_git_push,
            "docker": self.can_docker,
            "deploy": self.can_deploy,
        }
        return permission_map.get(action, False)


# Default permissions instance
default_permissions = Permissions()
