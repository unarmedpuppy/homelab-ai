"""Markdown-based task management CLI for the dashboard API.

Provides async functions to interact with tasks defined in a single tasks.md file.
Replaces the beads task management system with a simpler, git-tracked markdown format.

Task format in tasks.md:
    ## Epic: Epic Name

    ---

    ### [STATUS] Task Title {#task-id}
    | priority | repo | labels |
    |----------|------|--------|
    | P1 | polyjuiced | health, api |

    Task description here.

    #### Verification
    ```bash
    verification commands
    ```

    ---
"""

import asyncio
import re
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Tasks file location - can be overridden via environment variable
TASKS_FILE = Path(os.getenv("TASKS_FILE", "/workspace/home-server/tasks.md"))
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "/workspace"))


class TasksError(Exception):
    """Error from tasks operations."""
    pass


def _parse_status(status_str: str) -> str:
    """Convert markdown status to API status."""
    status_map = {
        "OPEN": "open",
        "IN_PROGRESS": "in_progress",
        "CLOSED": "closed",
    }
    return status_map.get(status_str.upper(), "open")


def _status_to_markdown(status: str) -> str:
    """Convert API status to markdown status."""
    status_map = {
        "open": "OPEN",
        "in_progress": "IN_PROGRESS",
        "closed": "CLOSED",
    }
    return status_map.get(status.lower(), "OPEN")


def _parse_priority(priority_str: str) -> int:
    """Convert P0-P3 to 0-3."""
    if priority_str.startswith("P"):
        try:
            return int(priority_str[1])
        except ValueError:
            return 2
    return 2


def _priority_to_markdown(priority: int) -> str:
    """Convert 0-3 to P0-P3."""
    return f"P{priority}"


def _parse_task_block(block: str, current_epic: Optional[str] = None) -> Optional[dict]:
    """Parse a single task block from markdown.

    Args:
        block: The task block text starting with ### [STATUS]
        current_epic: The current epic name (if any)

    Returns:
        Task dictionary or None if parsing fails
    """
    lines = block.strip().split('\n')
    if not lines:
        return None

    # Parse header: ### [STATUS] Title {#id}
    header_match = re.match(
        r'^###\s+\[(\w+)\]\s+(.+?)\s*\{#([\w-]+)\}\s*$',
        lines[0].strip()
    )
    if not header_match:
        return None

    status_str, title, task_id = header_match.groups()

    # Default values
    priority = 2
    repo = ""
    labels = []
    description_lines = []
    verification_lines = []
    in_verification = False
    in_code_block = False
    completed_at = None

    # Parse the rest of the block
    i = 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines at the start
        if not stripped and not description_lines:
            i += 1
            continue

        # Check for metadata table
        if stripped.startswith('| priority') or stripped.startswith('|---'):
            i += 1
            continue

        # Parse metadata row: | P1 | polyjuiced | health, api |
        if stripped.startswith('|') and not stripped.startswith('|---') and 'priority' not in stripped.lower():
            parts = [p.strip() for p in stripped.split('|')[1:-1]]  # Remove empty first/last
            if len(parts) >= 3:
                priority = _parse_priority(parts[0])
                repo = parts[1].strip()
                labels = [l.strip() for l in parts[2].split(',') if l.strip()]
            i += 1
            continue

        # Check for verification section
        if stripped.startswith('#### Verification'):
            in_verification = True
            i += 1
            continue

        # Track code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            if in_verification:
                verification_lines.append(line)
            else:
                description_lines.append(line)
            i += 1
            continue

        # Check for completed marker
        if stripped.startswith('*Completed:'):
            # Extract completion date: *Completed: 2026-01-19 - reason*
            completed_match = re.match(r'\*Completed:\s*([\d-]+)', stripped)
            if completed_match:
                completed_at = completed_match.group(1)
            description_lines.append(line)
            i += 1
            continue

        # Add to appropriate section
        if in_verification:
            verification_lines.append(line)
        else:
            description_lines.append(line)

        i += 1

    # Build description (strip trailing empty lines)
    description = '\n'.join(description_lines).strip()
    verification = '\n'.join(verification_lines).strip()

    # Include verification in description for API compatibility
    if verification:
        description = f"{description}\n\n#### Verification\n{verification}"

    # Calculate age (assume created today if no better info)
    created_at = datetime.now(timezone.utc).isoformat()
    age_days = 0

    return {
        "id": task_id,
        "title": title,
        "status": _parse_status(status_str),
        "priority": priority,
        "issue_type": "task",  # Simplified - no issue types
        "repo": repo,
        "labels": labels,
        "description": description,
        "epic": current_epic,
        "created_at": created_at,
        "updated_at": created_at,
        "completed_at": completed_at,
        "age_days": age_days,
        "blocked_by": [],  # No dependency tracking
        "dependency_count": 0,
    }


def _parse_tasks_md() -> tuple[list[dict], str]:
    """Parse the tasks.md file.

    Returns:
        Tuple of (list of task dicts, raw file content)
    """
    tasks = []

    if not TASKS_FILE.exists():
        logger.warning(f"Tasks file not found: {TASKS_FILE}")
        return tasks, ""

    try:
        content = TASKS_FILE.read_text()
    except Exception as e:
        logger.error(f"Failed to read tasks file: {e}")
        raise TasksError(f"Failed to read tasks file: {e}")

    # Split by task separators
    current_epic = None

    # Find epic headers
    epic_pattern = re.compile(r'^##\s+Epic:\s*(.+)$', re.MULTILINE)

    # Split content by --- separators while tracking epics
    sections = re.split(r'\n---\n', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check for epic header in this section
        epic_match = epic_pattern.search(section)
        if epic_match:
            current_epic = epic_match.group(1).strip()
            # Remove epic header from section for task parsing
            section = epic_pattern.sub('', section).strip()

        # Check if this section contains a task
        if section.startswith('###'):
            task = _parse_task_block(section, current_epic)
            if task:
                tasks.append(task)

    return tasks, content


def _write_tasks_md(tasks: list[dict], git_commit: bool = True, commit_message: str = "") -> None:
    """Write tasks back to tasks.md file.

    Args:
        tasks: List of task dictionaries
        git_commit: Whether to commit the change
        commit_message: Commit message to use
    """
    # Group tasks by epic
    epics: dict[str, list[dict]] = {}
    no_epic: list[dict] = []

    for task in tasks:
        epic = task.get("epic")
        if epic:
            if epic not in epics:
                epics[epic] = []
            epics[epic].append(task)
        else:
            no_epic.append(task)

    # Build markdown content
    lines = ["# Tasks", ""]

    # Write tasks grouped by epic
    for epic_name, epic_tasks in epics.items():
        lines.append(f"## Epic: {epic_name}")
        lines.append("")

        for task in epic_tasks:
            lines.extend(_task_to_markdown(task))

    # Write tasks without epic
    if no_epic:
        if epics:
            lines.append("## Other Tasks")
            lines.append("")
        for task in no_epic:
            lines.extend(_task_to_markdown(task))

    content = '\n'.join(lines)

    # Write file
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(content)

    # Git commit if requested
    if git_commit and commit_message:
        _git_commit(commit_message)


def _task_to_markdown(task: dict) -> list[str]:
    """Convert a task dict to markdown lines."""
    lines = ["---", ""]

    # Header
    status = _status_to_markdown(task.get("status", "open"))
    title = task.get("title", "Untitled")
    task_id = task.get("id", "unknown")
    lines.append(f"### [{status}] {title} {{#{task_id}}}")

    # Metadata table
    priority = _priority_to_markdown(task.get("priority", 2))
    repo = task.get("repo", "")
    labels = ", ".join(task.get("labels", []))
    lines.append("| priority | repo | labels |")
    lines.append("|----------|------|--------|")
    lines.append(f"| {priority} | {repo} | {labels} |")
    lines.append("")

    # Description (may already include verification section)
    description = task.get("description", "")
    if description:
        lines.append(description)
        lines.append("")

    # Add completion note for closed tasks
    if task.get("status") == "closed":
        completed_at = task.get("completed_at") or datetime.now().strftime("%Y-%m-%d")
        if not description or "*Completed:" not in description:
            lines.append(f"*Completed: {completed_at}*")
            lines.append("")

    return lines


def _git_commit(message: str) -> None:
    """Commit changes to git."""
    import subprocess

    repo_dir = TASKS_FILE.parent

    try:
        # Add the tasks file
        subprocess.run(
            ["git", "add", str(TASKS_FILE)],
            cwd=repo_dir,
            capture_output=True,
            check=True,
        )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir,
            capture_output=True,
            check=False,  # Don't fail if nothing to commit
        )

        # Push (best effort)
        subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            check=False,
        )

    except Exception as e:
        logger.warning(f"Git commit failed: {e}")


# =============================================================================
# Public API - matches beads_cli interface
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
        task_type: Filter by type (ignored - all are tasks)
        limit: Maximum number of tasks to return

    Returns:
        List of task dictionaries
    """
    tasks, _ = _parse_tasks_md()

    # Apply filters
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    if label:
        tasks = [t for t in tasks if label in t.get("labels", [])]

    if priority is not None:
        tasks = [t for t in tasks if t.get("priority") == priority]

    # Sort by priority (ascending) then by ID
    tasks.sort(key=lambda x: (x.get("priority", 2), x.get("id", "")))

    if limit:
        tasks = tasks[:limit]

    return tasks


async def get_ready_tasks(label: Optional[str] = None) -> list[dict]:
    """Get tasks that are ready to work on (open).

    With markdown-based tasks, there are no dependencies,
    so all open tasks are ready.

    Args:
        label: Filter by label

    Returns:
        List of ready task dictionaries
    """
    tasks = await list_tasks(status="open", label=label)
    return tasks


async def get_task(task_id: str) -> Optional[dict]:
    """Get a specific task by ID.

    Args:
        task_id: The task ID

    Returns:
        Task dictionary or None if not found
    """
    tasks, _ = _parse_tasks_md()

    for task in tasks:
        if task.get("id") == task_id:
            return task

    return None


async def claim_task(task_id: str) -> str:
    """Claim a task (set status to in_progress).

    Args:
        task_id: The task ID

    Returns:
        Success message
    """
    tasks, content = _parse_tasks_md()

    # Find and update the task
    found = False
    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "in_progress"
            found = True
            break

    if not found:
        raise TasksError(f"Task {task_id} not found")

    # Write back
    _write_tasks_md(tasks, git_commit=True, commit_message=f"claim: {task_id}")

    return f"Task {task_id} claimed"


async def close_task(task_id: str, reason: str = "") -> str:
    """Close a task (set status to closed).

    Args:
        task_id: The task ID
        reason: Optional completion reason

    Returns:
        Success message
    """
    tasks, content = _parse_tasks_md()

    # Find and update the task
    found = False
    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "closed"
            task["completed_at"] = datetime.now().strftime("%Y-%m-%d")
            if reason:
                # Append reason to description
                desc = task.get("description", "")
                task["description"] = f"{desc}\n\n*Completed: {task['completed_at']} - {reason}*"
            found = True
            break

    if not found:
        raise TasksError(f"Task {task_id} not found")

    # Write back
    _write_tasks_md(tasks, git_commit=True, commit_message=f"close: {task_id}")

    return f"Task {task_id} closed"


async def create_task(
    title: str,
    priority: int = 2,
    task_type: str = "task",
    labels: Optional[list[str]] = None,
    description: Optional[str] = None,
    blocked_by: Optional[list[str]] = None,  # Ignored - no dependencies
    repo: Optional[str] = None,
    epic: Optional[str] = None,
) -> dict:
    """Create a new task.

    Args:
        title: Task title
        priority: Priority 0-3 (0=critical, 1=high, 2=medium, 3=low)
        task_type: Task type (ignored - all are tasks)
        labels: List of labels
        description: Optional markdown description
        blocked_by: Ignored - no dependency tracking
        repo: Repository name
        epic: Epic name to group under

    Returns:
        Created task dictionary
    """
    tasks, _ = _parse_tasks_md()

    # Generate task ID
    # Use format: {repo}-{number} or task-{number}
    prefix = repo.replace("/", "-").replace(" ", "-") if repo else "task"

    # Find highest existing number for this prefix
    existing_nums = []
    for t in tasks:
        tid = t.get("id", "")
        if tid.startswith(f"{prefix}-"):
            try:
                num = int(tid.split("-")[-1])
                existing_nums.append(num)
            except ValueError:
                pass

    next_num = max(existing_nums, default=0) + 1
    task_id = f"{prefix}-{next_num:03d}"

    # Extract repo from labels if not provided
    if not repo and labels:
        for lbl in labels:
            if lbl.startswith("repo:"):
                repo = lbl.replace("repo:", "")
                break

    # Create task
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": task_id,
        "title": title,
        "status": "open",
        "priority": priority,
        "issue_type": "task",
        "repo": repo or "",
        "labels": labels or [],
        "description": description or "",
        "epic": epic,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "age_days": 0,
        "blocked_by": [],
        "dependency_count": 0,
    }

    tasks.append(task)

    # Write back
    _write_tasks_md(tasks, git_commit=True, commit_message=f"create: {task_id} - {title}")

    return task


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
    tasks, _ = _parse_tasks_md()

    # Find task
    task = None
    for t in tasks:
        if t.get("id") == task_id:
            task = t
            break

    if not task:
        raise TasksError(f"Task {task_id} not found")

    # Apply updates
    if status:
        task["status"] = status
        if status == "closed":
            task["completed_at"] = datetime.now().strftime("%Y-%m-%d")

    if priority is not None:
        task["priority"] = priority

    if labels_add:
        current = set(task.get("labels", []))
        current.update(labels_add)
        task["labels"] = list(current)

    if labels_remove:
        current = set(task.get("labels", []))
        current -= set(labels_remove)
        task["labels"] = list(current)

    task["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write back
    _write_tasks_md(tasks, git_commit=True, commit_message=f"update: {task_id}")

    return task


async def get_labels() -> list[str]:
    """Get all unique labels from tasks.

    Returns:
        List of unique labels
    """
    tasks, _ = _parse_tasks_md()
    labels = set()

    for task in tasks:
        task_labels = task.get("labels", [])
        if isinstance(task_labels, list):
            labels.update(task_labels)

    return sorted(labels)


async def get_stats() -> dict:
    """Get aggregated task statistics.

    Returns:
        Dictionary with task statistics
    """
    tasks, _ = _parse_tasks_md()

    stats = {
        "total_tasks": len(tasks),
        "backlog_count": 0,  # open
        "in_progress_count": 0,
        "done_count": 0,
        "blocked_count": 0,  # Always 0 - no dependencies
        "by_label": {},
        "by_priority": {0: 0, 1: 0, 2: 0, 3: 0},
        "by_type": {"task": len(tasks)},  # All are tasks
    }

    for task in tasks:
        status = task.get("status", "open")
        priority = task.get("priority", 2)
        labels = task.get("labels", [])

        # Count by status
        if status == "closed":
            stats["done_count"] += 1
        elif status == "in_progress":
            stats["in_progress_count"] += 1
        else:
            stats["backlog_count"] += 1

        # Count by priority
        if priority in stats["by_priority"]:
            stats["by_priority"][priority] += 1

        # Count by label
        if isinstance(labels, list):
            for label in labels:
                stats["by_label"][label] = stats["by_label"].get(label, 0) + 1

    return stats


async def sync_tasks() -> str:
    """Sync tasks (pull and push changes).

    For markdown-based tasks, this just does a git pull/push.

    Returns:
        Sync result message
    """
    import subprocess

    repo_dir = TASKS_FILE.parent

    try:
        # Pull
        subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=repo_dir,
            capture_output=True,
            check=False,
        )

        # Push
        subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            check=False,
        )

        return "Sync completed"

    except Exception as e:
        return f"Sync completed with warnings: {e}"


def compute_age_days(created_at: str) -> int:
    """Compute the age of a task in days.

    Args:
        created_at: ISO format datetime string

    Returns:
        Number of days since creation
    """
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
        return (now - created).days
    except Exception:
        return 0


# Alias for API compatibility
BeadsError = TasksError
sync_beads = sync_tasks
