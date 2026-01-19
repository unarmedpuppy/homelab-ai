"""Beads CLI wrapper for the dashboard API.

Provides async functions to interact with the beads task management system.
Supports two modes:
1. CLI mode: Uses `bd` CLI tool when available (local development)
2. JSONL mode: Reads directly from issues.jsonl (server deployment)

The mode is auto-detected based on whether `bd` is available.
"""

import asyncio
import json
import os
import logging
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Beads directory location - can be overridden via environment variable
BEADS_DIR = Path(os.getenv("BEADS_DIR", "/data/beads"))
JSONL_PATH = BEADS_DIR / "issues.jsonl"

# Check if bd CLI is available
BD_CLI_AVAILABLE = shutil.which("bd") is not None


class BeadsError(Exception):
    """Error from beads operations."""
    pass


# =============================================================================
# JSONL-based operations (for server deployment without bd CLI)
# =============================================================================

def _load_issues_from_jsonl() -> list[dict]:
    """Load all issues from the JSONL file.

    Returns:
        List of issue dictionaries
    """
    issues = []
    if not JSONL_PATH.exists():
        logger.warning(f"JSONL file not found: {JSONL_PATH}")
        return issues

    try:
        with open(JSONL_PATH, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    issue = json.loads(line)
                    issues.append(issue)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num}: {e}")
    except Exception as e:
        logger.error(f"Failed to read JSONL file: {e}")
        raise BeadsError(f"Failed to read beads data: {e}")

    return issues


def _filter_issues(
    issues: list[dict],
    status: Optional[str] = None,
    label: Optional[str] = None,
    priority: Optional[int] = None,
    task_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Filter issues based on criteria.

    Args:
        issues: List of all issues
        status: Filter by status (open, in_progress, closed)
        label: Filter by label
        priority: Filter by priority (0-3)
        task_type: Filter by type (task, bug, feature, epic, chore)
        limit: Maximum number of results

    Returns:
        Filtered list of issues
    """
    filtered = issues

    if status:
        filtered = [i for i in filtered if i.get("status") == status]

    if label:
        filtered = [i for i in filtered if label in i.get("labels", [])]

    if priority is not None:
        filtered = [i for i in filtered if i.get("priority") == priority]

    if task_type:
        filtered = [i for i in filtered if i.get("issue_type") == task_type]

    # Sort by priority (ascending) then by created_at (descending)
    filtered.sort(key=lambda x: (
        x.get("priority", 2),
        -(datetime.fromisoformat(x.get("created_at", "2000-01-01").replace("Z", "+00:00")).timestamp()
          if x.get("created_at") else 0)
    ))

    if limit:
        filtered = filtered[:limit]

    return filtered


# =============================================================================
# CLI-based operations (for local development with bd CLI)
# =============================================================================

async def bd_command(*args, json_output: bool = True, cwd: Optional[Path] = None) -> dict | list | str:
    """Execute bd command and return parsed output.

    Args:
        *args: Command arguments to pass to bd
        json_output: Whether to request and parse JSON output
        cwd: Working directory for the command (defaults to BEADS_DIR parent)

    Returns:
        Parsed JSON if json_output=True, otherwise raw stdout string

    Raises:
        BeadsError: If the command fails
    """
    if not BD_CLI_AVAILABLE:
        raise BeadsError("bd command not available - server is in read-only JSONL mode")

    cmd = ["bd"] + list(args)
    if json_output:
        cmd.append("--json")

    working_dir = cwd or BEADS_DIR.parent

    env = os.environ.copy()
    env["BEADS_DIR"] = str(BEADS_DIR)

    logger.debug(f"Running bd command: {' '.join(cmd)} in {working_dir}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(working_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip() or f"Command failed with code {proc.returncode}"
            raise BeadsError(error_msg)

        output = stdout.decode().strip()

        if json_output and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON output: {e}")
                # Return empty list for list commands that returned no results
                if args and args[0] in ("list", "ready"):
                    return []
                raise BeadsError(f"Invalid JSON output: {output[:200]}")

        return output

    except FileNotFoundError:
        raise BeadsError("bd command not found. Is beads-cli installed?")
    except Exception as e:
        if isinstance(e, BeadsError):
            raise
        raise BeadsError(f"Failed to execute bd command: {e}")


# =============================================================================
# Public API - auto-detects CLI vs JSONL mode
# =============================================================================

async def list_tasks(
    status: Optional[str] = None,
    label: Optional[str] = None,
    priority: Optional[int] = None,
    task_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """List all tasks with optional filters.

    Args:
        status: Filter by status (open, in_progress, closed)
        label: Filter by label
        priority: Filter by priority (0-3)
        task_type: Filter by type (task, bug, feature, epic, chore)
        limit: Maximum number of tasks to return (default: 100)

    Returns:
        List of task dictionaries
    """
    if BD_CLI_AVAILABLE:
        args = ["list"]
        if status:
            args.extend(["--status", status])
        if label:
            args.extend(["--label", label])
        if priority is not None:
            args.extend(["--priority", str(priority)])
        if task_type:
            args.extend(["--type", task_type])
        if limit is not None:
            args.extend(["--limit", str(limit)])
        result = await bd_command(*args)
        return result if isinstance(result, list) else []
    else:
        # JSONL mode
        issues = _load_issues_from_jsonl()
        return _filter_issues(issues, status, label, priority, task_type, limit or 100)


async def get_ready_tasks(label: Optional[str] = None) -> list[dict]:
    """Get tasks that are ready to work on (open and not blocked).

    Args:
        label: Filter by label

    Returns:
        List of ready task dictionaries
    """
    if BD_CLI_AVAILABLE:
        args = ["ready"]
        if label:
            args.extend(["--label", label])
        result = await bd_command(*args)
        return result if isinstance(result, list) else []
    else:
        # JSONL mode - get open tasks that aren't blocked
        issues = _load_issues_from_jsonl()
        ready = []
        for issue in issues:
            if issue.get("status") != "open":
                continue
            if label and label not in issue.get("labels", []):
                continue
            # Check if blocked
            blocked_by = issue.get("blocked_by", [])
            dependency_count = issue.get("dependency_count", 0)
            if not blocked_by and dependency_count == 0:
                ready.append(issue)

        # Sort by priority
        ready.sort(key=lambda x: x.get("priority", 2))
        return ready


async def get_task(task_id: str) -> Optional[dict]:
    """Get a specific task by ID.

    Args:
        task_id: The task ID

    Returns:
        Task dictionary or None if not found
    """
    if BD_CLI_AVAILABLE:
        try:
            result = await bd_command("show", task_id)
            # bd show returns an array even for a single task
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            elif isinstance(result, dict):
                return result
            return None
        except BeadsError as e:
            if "not found" in str(e).lower():
                return None
            raise
    else:
        # JSONL mode
        issues = _load_issues_from_jsonl()
        for issue in issues:
            if issue.get("id") == task_id:
                return issue
        return None


async def claim_task(task_id: str) -> str:
    """Claim a task (set status to in_progress).

    Args:
        task_id: The task ID

    Returns:
        Success message
    """
    if not BD_CLI_AVAILABLE:
        raise BeadsError("Write operations not supported in JSONL-only mode. Use bd CLI locally.")

    result = await bd_command("claim", task_id, json_output=False)
    return result or f"Task {task_id} claimed"


async def close_task(task_id: str) -> str:
    """Close a task (set status to closed).

    Args:
        task_id: The task ID

    Returns:
        Success message
    """
    if not BD_CLI_AVAILABLE:
        raise BeadsError("Write operations not supported in JSONL-only mode. Use bd CLI locally.")

    result = await bd_command("close", task_id, json_output=False)
    return result or f"Task {task_id} closed"


async def create_task(
    title: str,
    priority: int = 2,
    task_type: str = "task",
    labels: Optional[list[str]] = None,
    description: Optional[str] = None,
    blocked_by: Optional[list[str]] = None,
) -> dict:
    """Create a new task.

    Args:
        title: Task title
        priority: Priority 0-3 (0=critical, 1=high, 2=medium, 3=low)
        task_type: Task type (task, bug, feature, epic, chore)
        labels: List of labels (should include at least one repo:* label)
        description: Optional markdown description
        blocked_by: Optional list of blocking task IDs

    Returns:
        Created task dictionary
    """
    if not BD_CLI_AVAILABLE:
        raise BeadsError("Write operations not supported in JSONL-only mode. Use bd CLI locally.")

    args = ["create", title]

    args.extend(["-p", str(priority)])
    args.extend(["-t", task_type])

    if labels:
        for label in labels:
            args.extend(["-l", label])

    if blocked_by:
        for blocker in blocked_by:
            args.extend(["-b", blocker])

    # Create the task first
    result = await bd_command(*args, json_output=False)

    # Extract task ID from result (format: "Created task: ID")
    task_id = None
    if result and ":" in result:
        parts = result.split(":")
        if len(parts) >= 2:
            task_id = parts[-1].strip()

    # If we have a description and task ID, update the task
    if description and task_id:
        try:
            await bd_command("edit", task_id, "--description", description, json_output=False)
        except BeadsError as e:
            logger.warning(f"Failed to set description: {e}")

    # Return the created task
    if task_id:
        task = await get_task(task_id)
        if task:
            return task

    # Fallback: return minimal task info
    return {
        "id": task_id or "unknown",
        "title": title,
        "priority": priority,
        "issue_type": task_type,
        "labels": labels or [],
        "status": "open",
    }


async def update_task(
    task_id: str,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    labels_add: Optional[list[str]] = None,
    labels_remove: Optional[list[str]] = None,
) -> dict:
    """Update an existing task.

    Args:
        task_id: The task ID
        status: New status (open, in_progress, closed)
        priority: New priority (0-3)
        labels_add: Labels to add
        labels_remove: Labels to remove

    Returns:
        Updated task dictionary
    """
    if not BD_CLI_AVAILABLE:
        raise BeadsError("Write operations not supported in JSONL-only mode. Use bd CLI locally.")

    if status:
        if status == "in_progress":
            await claim_task(task_id)
        elif status == "closed":
            await close_task(task_id)
        elif status == "open":
            # Reopen task
            await bd_command("reopen", task_id, json_output=False)

    if priority is not None:
        await bd_command("edit", task_id, "--priority", str(priority), json_output=False)

    if labels_add:
        for label in labels_add:
            await bd_command("edit", task_id, "--add-label", label, json_output=False)

    if labels_remove:
        for label in labels_remove:
            await bd_command("edit", task_id, "--remove-label", label, json_output=False)

    # Return updated task
    task = await get_task(task_id)
    if not task:
        raise BeadsError(f"Task {task_id} not found after update")
    return task


async def get_labels() -> list[str]:
    """Get all unique labels from tasks.

    Returns:
        List of unique labels
    """
    tasks = await list_tasks(limit=1000)
    labels = set()
    for task in tasks:
        task_labels = task.get("labels", [])
        if isinstance(task_labels, list):
            labels.update(task_labels)
    return sorted(labels)


async def get_stats() -> dict:
    """Get aggregated beads statistics.

    Returns:
        Dictionary with task statistics
    """
    all_tasks = await list_tasks(limit=1000)

    stats = {
        "total_tasks": len(all_tasks),
        "backlog_count": 0,  # open + unblocked
        "in_progress_count": 0,
        "done_count": 0,
        "blocked_count": 0,
        "by_label": {},
        "by_priority": {0: 0, 1: 0, 2: 0, 3: 0},
        "by_type": {},
    }

    for task in all_tasks:
        status = task.get("status", "open")
        priority = task.get("priority", 2)
        task_type = task.get("issue_type", "task")
        labels = task.get("labels", [])
        blocked_by = task.get("blocked_by", [])
        dependency_count = task.get("dependency_count", 0)

        # Count by status
        if status == "closed":
            stats["done_count"] += 1
        elif status == "in_progress":
            stats["in_progress_count"] += 1
        else:  # open
            # Check if blocked
            if blocked_by or dependency_count > 0:
                stats["blocked_count"] += 1
            else:
                stats["backlog_count"] += 1

        # Count by priority
        if priority in stats["by_priority"]:
            stats["by_priority"][priority] += 1

        # Count by label
        if isinstance(labels, list):
            for label in labels:
                stats["by_label"][label] = stats["by_label"].get(label, 0) + 1

        # Count by type
        stats["by_type"][task_type] = stats["by_type"].get(task_type, 0) + 1

    return stats


async def sync_beads() -> str:
    """Sync beads database (pull and push changes).

    Returns:
        Sync result message
    """
    if not BD_CLI_AVAILABLE:
        return "Sync not available in JSONL-only mode. Beads data is synced via git."

    try:
        result = await bd_command("sync", json_output=False)
        return result or "Sync completed"
    except BeadsError as e:
        logger.warning(f"Sync warning: {e}")
        return f"Sync completed with warnings: {e}"


def compute_age_days(created_at: str) -> int:
    """Compute the age of a task in days.

    Args:
        created_at: ISO format datetime string

    Returns:
        Number of days since creation
    """
    try:
        # Handle timezone-aware strings
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
        return (now - created).days
    except Exception:
        return 0
