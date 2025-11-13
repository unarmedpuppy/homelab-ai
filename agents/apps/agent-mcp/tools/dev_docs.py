"""
Dev Docs Tools for MCP Server

Provides tools for creating and managing dev docs (plan, context, tasks) to prevent
agents from losing track during long sessions, especially after auto-compaction.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


# Paths
AGENTS_DIR = project_root / "agents"
ACTIVE_DIR = AGENTS_DIR / "active"


def _ensure_agent_dev_docs_dir(agent_id: str) -> Path:
    """Ensure agent dev docs directory exists."""
    agent_dir = ACTIVE_DIR / agent_id
    dev_docs_dir = agent_dir / "dev-docs"
    dev_docs_dir.mkdir(parents=True, exist_ok=True)
    return dev_docs_dir


def _get_dev_doc_path(agent_id: str, task_name: str, doc_type: str) -> Path:
    """Get path to a dev doc file."""
    dev_docs_dir = _ensure_agent_dev_docs_dir(agent_id)
    return dev_docs_dir / f"{task_name}-{doc_type}.md"


def register_dev_docs_tools(server: Server):
    """Register dev docs tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def create_dev_docs(
        agent_id: str,
        task_name: str,
        plan_content: str,
        context_content: str = "",
        initial_tasks: str = ""
    ) -> Dict[str, Any]:
        """
        Create dev docs (plan, context, tasks) for a major task.
        
        This prevents agents from losing track during long sessions, especially
        after auto-compaction. Dev docs provide structured context that persists
        across sessions.
        
        Args:
            agent_id: Your agent ID
            task_name: Task name (kebab-case, e.g., "deploy-trading-bot")
            plan_content: The approved plan content (markdown)
            context_content: Initial context (key files, decisions, next steps)
            initial_tasks: Initial task checklist (markdown list)
        
        Returns:
            Paths to created dev doc files
        
        Example:
            create_dev_docs(
                agent_id="agent-001",
                task_name="deploy-trading-bot",
                plan_content="# Plan\n\n1. Setup database...",
                context_content="Key files: apps/trading-bot/docker-compose.yml",
                initial_tasks="- [ ] Setup database\n- [ ] Configure API"
            )
        """
        dev_docs_dir = _ensure_agent_dev_docs_dir(agent_id)
        
        # Create plan file
        plan_path = _get_dev_doc_path(agent_id, task_name, "plan")
        plan_content_full = f"""# {task_name.replace('-', ' ').title()} - Plan

**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Agent**: {agent_id}
**Status**: Active

---

{plan_content}

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        plan_path.write_text(plan_content_full)
        
        # Create context file
        context_path = _get_dev_doc_path(agent_id, task_name, "context")
        context_content_full = f"""# {task_name.replace('-', ' ').title()} - Context

**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Agent**: {agent_id}
**Status**: Active

---

## Key Files

{context_content if context_content else "To be filled as work progresses"}

---

## Decisions Made

(Record important decisions here)

---

## Next Steps

(Update with current progress and next steps)

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        context_path.write_text(context_content_full)
        
        # Create tasks file
        tasks_path = _get_dev_doc_path(agent_id, task_name, "tasks")
        tasks_content_full = f"""# {task_name.replace('-', ' ').title()} - Tasks

**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Agent**: {agent_id}
**Status**: Active

---

## Task Checklist

{initial_tasks if initial_tasks else "- [ ] Task 1\n- [ ] Task 2"}

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        tasks_path.write_text(tasks_content_full)
        
        return {
            "status": "success",
            "message": f"Dev docs created for task '{task_name}'",
            "files": {
                "plan": str(plan_path.relative_to(project_root)),
                "context": str(context_path.relative_to(project_root)),
                "tasks": str(tasks_path.relative_to(project_root))
            },
            "instructions": f"Read these files at the start of each session: {', '.join([str(p.relative_to(project_root)) for p in [plan_path, context_path, tasks_path]])}"
        }
    
    @server.tool()
    @with_automatic_logging()
    async def update_dev_docs(
        agent_id: str,
        task_name: str,
        context_updates: str = "",
        completed_tasks: str = "",
        new_tasks: str = "",
        next_steps: str = ""
    ) -> Dict[str, Any]:
        """
        Update dev docs with current progress, especially before compaction.
        
        Use this before compacting conversation or starting a new session to
        preserve context and progress.
        
        Args:
            agent_id: Your agent ID
            task_name: Task name (must match existing dev docs)
            context_updates: New context to add (key files, decisions, findings)
            completed_tasks: Comma-separated list of completed task IDs/descriptions
            new_tasks: New tasks to add (markdown list)
            next_steps: Next steps to record
        
        Returns:
            Updated file paths
        
        Example:
            update_dev_docs(
                agent_id="agent-001",
                task_name="deploy-trading-bot",
                context_updates="Database configured, API key set",
                completed_tasks="Setup database, Configure API",
                next_steps="Deploy frontend, test integration"
            )
        """
        # Get existing files
        plan_path = _get_dev_doc_path(agent_id, task_name, "plan")
        context_path = _get_dev_doc_path(agent_id, task_name, "context")
        tasks_path = _get_dev_doc_path(agent_id, task_name, "tasks")
        
        if not plan_path.exists():
            return {
                "status": "error",
                "message": f"Dev docs not found for task '{task_name}'. Create them first using create_dev_docs()."
            }
        
        # Update context file
        if context_path.exists():
            context_content = context_path.read_text()
            
            # Update "Next Steps" section
            if "## Next Steps" in context_content:
                # Replace existing next steps
                parts = context_content.split("## Next Steps")
                if len(parts) >= 2:
                    before = parts[0]
                    after_parts = parts[1].split("---", 1)
                    new_next_steps = next_steps if next_steps else "Continue with current work"
                    context_content = f"""{before}## Next Steps

{new_next_steps}

---

{after_parts[-1] if len(after_parts) > 1 else ''}"""
            
            # Add context updates
            if context_updates:
                if "## Decisions Made" in context_content:
                    # Add to decisions section
                    context_content = context_content.replace(
                        "## Decisions Made",
                        f"## Decisions Made\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {context_updates}\n"
                    )
                else:
                    # Add new section
                    context_content = context_content.replace(
                        "---",
                        f"---\n\n## Decisions Made\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {context_updates}\n\n---"
                    )
            
            # Update timestamp
            context_content = context_content.replace(
                "**Last Updated**:",
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            context_path.write_text(context_content)
        
        # Update tasks file
        if tasks_path.exists():
            tasks_content = tasks_path.read_text()
            
            # Mark completed tasks
            if completed_tasks:
                completed_list = [t.strip() for t in completed_tasks.split(",")]
                for task in completed_list:
                    # Find and mark as complete
                    tasks_content = tasks_content.replace(
                        f"- [ ] {task}",
                        f"- [x] {task}"
                    )
                    tasks_content = tasks_content.replace(
                        f"- [ ] {task.strip()}",
                        f"- [x] {task.strip()}"
                    )
            
            # Add new tasks
            if new_tasks:
                if "## Task Checklist" in tasks_content:
                    # Add to checklist
                    tasks_content = tasks_content.replace(
                        "## Task Checklist",
                        f"## Task Checklist\n\n{new_tasks}\n"
                    )
            
            # Update timestamp
            tasks_content = tasks_content.replace(
                "**Last Updated**:",
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            tasks_path.write_text(tasks_content)
        
        return {
            "status": "success",
            "message": f"Dev docs updated for task '{task_name}'",
            "files": {
                "context": str(context_path.relative_to(project_root)),
                "tasks": str(tasks_path.relative_to(project_root))
            }
        }
    
    @server.tool()
    @with_automatic_logging()
    async def list_active_dev_docs(agent_id: str) -> Dict[str, Any]:
        """
        List all active dev docs for an agent.
        
        Use this at the start of a session to see what tasks you're working on.
        
        Args:
            agent_id: Your agent ID
        
        Returns:
            List of active dev docs with their status
        """
        dev_docs_dir = ACTIVE_DIR / agent_id / "dev-docs"
        
        if not dev_docs_dir.exists():
            return {
                "status": "success",
                "message": "No dev docs found",
                "dev_docs": []
            }
        
        # Find all dev doc files
        dev_docs = {}
        for file_path in dev_docs_dir.glob("*-plan.md"):
            task_name = file_path.stem.replace("-plan", "")
            
            # Check if all three files exist
            plan_path = _get_dev_doc_path(agent_id, task_name, "plan")
            context_path = _get_dev_doc_path(agent_id, task_name, "context")
            tasks_path = _get_dev_doc_path(agent_id, task_name, "tasks")
            
            if plan_path.exists() and context_path.exists() and tasks_path.exists():
                # Get last updated time
                last_updated = datetime.fromtimestamp(plan_path.stat().st_mtime)
                
                dev_docs[task_name] = {
                    "task_name": task_name,
                    "plan": str(plan_path.relative_to(project_root)),
                    "context": str(context_path.relative_to(project_root)),
                    "tasks": str(tasks_path.relative_to(project_root)),
                    "last_updated": last_updated.strftime("%Y-%m-%d %H:%M:%S")
                }
        
        return {
            "status": "success",
            "message": f"Found {len(dev_docs)} active dev doc(s)",
            "dev_docs": list(dev_docs.values())
        }
    
    @server.tool()
    @with_automatic_logging()
    async def read_dev_docs(agent_id: str, task_name: str) -> Dict[str, Any]:
        """
        Read all dev docs for a specific task.
        
        Use this at the start of a session to refresh context on a task.
        
        Args:
            agent_id: Your agent ID
            task_name: Task name to read docs for
        
        Returns:
            Complete dev docs content
        """
        plan_path = _get_dev_doc_path(agent_id, task_name, "plan")
        context_path = _get_dev_doc_path(agent_id, task_name, "context")
        tasks_path = _get_dev_doc_path(agent_id, task_name, "tasks")
        
        if not plan_path.exists():
            return {
                "status": "error",
                "message": f"Dev docs not found for task '{task_name}'"
            }
        
        plan_content = plan_path.read_text() if plan_path.exists() else ""
        context_content = context_path.read_text() if context_path.exists() else ""
        tasks_content = tasks_path.read_text() if tasks_path.exists() else ""
        
        return {
            "status": "success",
            "task_name": task_name,
            "plan": plan_content,
            "context": context_content,
            "tasks": tasks_content,
            "files": {
                "plan": str(plan_path.relative_to(project_root)),
                "context": str(context_path.relative_to(project_root)),
                "tasks": str(tasks_path.relative_to(project_root))
            }
        }

