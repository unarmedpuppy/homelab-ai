"""
Task Coordination Tools for MCP Server

Provides tools for agents to register, claim, update, and query tasks across all agents.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server


# Paths for task coordination
TASKS_DIR = project_root / "agents" / "tasks"
REGISTRY_PATH = TASKS_DIR / "registry.md"


def _ensure_tasks_dir():
    """Ensure tasks directory exists."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        # Create initial registry if it doesn't exist
        REGISTRY_PATH.write_text("""# Task Registry

Central registry of all tasks across all agents.

## Task Status Legend
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

## Tasks

| Task ID | Title | Description | Status | Assignee | Priority | Dependencies | Project | Created | Updated |
|---------|-------|-------------|--------|----------|----------|--------------|---------|---------|---------|
| - | - | - | - | - | - | - | - | - | - |

---

**Last Updated**: {date}
**Total Tasks**: 0
""".format(date=datetime.now().strftime("%Y-%m-%d")))


def _parse_registry() -> List[Dict[str, str]]:
    """Parse the registry markdown file and return list of tasks."""
    _ensure_tasks_dir()
    
    if not REGISTRY_PATH.exists():
        return []
    
    content = REGISTRY_PATH.read_text()
    tasks = []
    
    # Find the tasks table
    in_table = False
    for line in content.splitlines():
        if "| Task ID |" in line:
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table and line.strip().startswith("|"):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 10 and parts[0] != "-":  # Skip empty row
                tasks.append({
                    "task_id": parts[0],
                    "title": parts[1],
                    "description": parts[2],
                    "status": parts[3],
                    "assignee": parts[4],
                    "priority": parts[5],
                    "dependencies": parts[6],
                    "project": parts[7],
                    "created": parts[8],
                    "updated": parts[9]
                })
        if in_table and not line.strip().startswith("|"):
            break  # End of table
    
    return tasks


def _write_registry(tasks: List[Dict[str, str]]):
    """Write tasks back to registry markdown file."""
    _ensure_tasks_dir()
    
    header = """# Task Registry

Central registry of all tasks across all agents.

## Task Status Legend
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

## Tasks

| Task ID | Title | Description | Status | Assignee | Priority | Dependencies | Project | Created | Updated |
|---------|-------|-------------|--------|----------|----------|--------------|---------|---------|---------|
"""
    
    # Add task rows
    rows = []
    for task in tasks:
        row = f"| {task['task_id']} | {task['title']} | {task['description']} | {task['status']} | {task['assignee']} | {task['priority']} | {task['dependencies']} | {task['project']} | {task['created']} | {task['updated']} |"
        rows.append(row)
    
    # If no tasks, add empty row
    if not rows:
        rows.append("| - | - | - | - | - | - | - | - | - | - |")
    
    footer = f"""

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Tasks**: {len(tasks)}
"""
    
    REGISTRY_PATH.write_text(header + "\n".join(rows) + footer)


def _generate_task_id(project: str, existing_tasks: List[Dict[str, str]]) -> str:
    """Generate a unique task ID for a project."""
    # Extract project number from existing tasks
    project_tasks = [t for t in existing_tasks if t.get('project') == project]
    
    if not project_tasks:
        # First task for this project
        return f"T1.1"
    
    # Find max task number for this project
    max_num = 0
    for task in project_tasks:
        task_id = task.get('task_id', '')
        match = re.match(r'T(\d+)\.(\d+)', task_id)
        if match:
            project_num = int(match.group(1))
            task_num = int(match.group(2))
            # Use project number from first match, increment task number
            if project_num > max_num:
                max_num = project_num
    
    # Find highest task number for this project number
    task_nums = []
    for task in project_tasks:
        task_id = task.get('task_id', '')
        match = re.match(r'T(\d+)\.(\d+)', task_id)
        if match:
            if int(match.group(1)) == max_num:
                task_nums.append(int(match.group(2)))
    
    next_task_num = max(task_nums) + 1 if task_nums else 1
    return f"T{max_num}.{next_task_num}"


def register_task_coordination_tools(server: Server):
    """Register task coordination tools with MCP server."""
    _ensure_tasks_dir()
    
    @server.tool()
    async def register_task(
        title: str,
        description: str,
        project: str,
        priority: str = "medium",
        dependencies: Optional[str] = None,
        created_by: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Register a new task in the central task registry.
        
        Args:
            title: Short title for the task
            description: Detailed description of the task
            project: Project name (e.g., "trading-journal", "media-download")
            priority: Task priority (low, medium, high, critical)
            dependencies: Comma-separated list of task IDs this task depends on (e.g., "T1.1,T1.2")
            created_by: Agent ID or name creating this task
        
        Returns:
            Dictionary with status, task_id, and message
        """
        _ensure_tasks_dir()
        
        # Parse existing tasks
        existing_tasks = _parse_registry()
        
        # Generate task ID
        task_id = _generate_task_id(project, existing_tasks)
        
        # Create new task
        new_task = {
            "task_id": task_id,
            "title": title[:100],  # Limit title length
            "description": description[:500],  # Limit description length
            "status": "pending",
            "assignee": "-",
            "priority": priority.lower(),
            "dependencies": dependencies if dependencies else "-",
            "project": project,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to tasks list
        existing_tasks.append(new_task)
        
        # Write back to registry
        _write_registry(existing_tasks)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": f"Task {task_id} registered successfully",
            "task": new_task
        }
    
    @server.tool()
    async def query_tasks(
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        priority: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Query tasks from the central registry with filters.
        
        Args:
            status: Filter by status (pending, claimed, in_progress, blocked, review, completed, cancelled)
            assignee: Filter by assignee (agent ID or "-" for unassigned)
            project: Filter by project name
            priority: Filter by priority (low, medium, high, critical)
            search_text: Search in title and description
            limit: Maximum number of results
        
        Returns:
            Dictionary with status, count, and list of matching tasks
        """
        _ensure_tasks_dir()
        
        # Parse existing tasks
        all_tasks = _parse_registry()
        
        # Filter tasks
        filtered_tasks = []
        for task in all_tasks:
            # Skip empty placeholder row
            if task.get('task_id') == '-':
                continue
            
            match = True
            
            # Filter by status
            if status and task.get('status', '').lower() != status.lower():
                match = False
            
            # Filter by assignee
            if assignee:
                if assignee == "unassigned" and task.get('assignee', '-') != '-':
                    match = False
                elif assignee != "unassigned" and task.get('assignee', '').lower() != assignee.lower():
                    match = False
            
            # Filter by project
            if project and task.get('project', '').lower() != project.lower():
                match = False
            
            # Filter by priority
            if priority and task.get('priority', '').lower() != priority.lower():
                match = False
            
            # Search in title and description
            if search_text:
                search_lower = search_text.lower()
                title = task.get('title', '').lower()
                description = task.get('description', '').lower()
                if search_lower not in title and search_lower not in description:
                    match = False
            
            if match:
                filtered_tasks.append(task)
        
        # Limit results
        filtered_tasks = filtered_tasks[:limit]
        
        return {
            "status": "success",
            "count": len(filtered_tasks),
            "tasks": filtered_tasks
        }

