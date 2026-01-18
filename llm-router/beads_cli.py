"""Beads CLI wrapper for the dashboard API.

Provides async functions to interact with the beads task management system
through the `bd` CLI tool.
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Beads directory location - can be overridden via environment variable
BEADS_DIR = Path(os.getenv("BEADS_DIR", "/workspace/home-server/.beads"))


class BeadsError(Exception):
    """Error from beads CLI execution."""
    pass


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
        limit: Maximum number of tasks to return (default: bd default of 50)

    Returns:
        List of task dictionaries
    """
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


async def get_ready_tasks(label: Optional[str] = None) -> list[dict]:
    """Get tasks that are ready to work on (open and not blocked).

    Args:
        label: Filter by label

    Returns:
        List of ready task dictionaries
    """
    args = ["ready"]

    if label:
        args.extend(["--label", label])

    result = await bd_command(*args)
    return result if isinstance(result, list) else []


async def get_task(task_id: str) -> Optional[dict]:
    """Get a specific task by ID.

    Args:
        task_id: The task ID

    Returns:
        Task dictionary or None if not found
    """
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


async def claim_task(task_id: str) -> str:
    """Claim a task (set status to in_progress).

    Args:
        task_id: The task ID

    Returns:
        Success message
    """
    result = await bd_command("claim", task_id, json_output=False)
    return result or f"Task {task_id} claimed"


async def close_task(task_id: str) -> str:
    """Close a task (set status to closed).

    Args:
        task_id: The task ID

    Returns:
        Success message
    """
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
    tasks = await list_tasks()
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
    all_tasks = await list_tasks()

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
