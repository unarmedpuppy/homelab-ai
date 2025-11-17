"""
Agent Management Tools for MCP Server

Provides tools for agents to create specialized agent definitions and manage agent registry.
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


def register_agent_management_tools(server: Server):
    """Register agent management tools with MCP server."""
    
    @with_automatic_logging()

    @server.tool()
    async def create_agent_definition(
        specialization: str,
        capabilities: str,
        initial_tasks: str,
        agent_id: Optional[str] = None,
        parent_agent_id: str = "agent-001",
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new specialized agent definition.
        
        Args:
            specialization: Specialization name (e.g., "media-download", "database-optimization")
            capabilities: Comma-separated list of capabilities (skills, tools, domain knowledge)
            initial_tasks: Description of initial tasks to assign
            agent_id: Optional agent ID (auto-generated if not provided)
            parent_agent_id: ID of agent creating this agent (default: agent-001)
            template: Template to use (base-agent, server-management-agent, media-download-agent, database-agent)
        
        Returns:
            Agent definition info and file paths
        """
        # Generate agent ID if not provided
        if not agent_id:
            # Find next available agent ID
            registry_path = project_root / "agents" / "registry" / "agent-registry.md"
            existing_ids = []
            if registry_path.exists():
                content = registry_path.read_text()
                # Simple extraction of existing IDs (can be improved)
                import re
                matches = re.findall(r'agent-(\d+)', content)
                existing_ids = [int(m) for m in matches if m.isdigit()]
            
            next_id = max(existing_ids) + 1 if existing_ids else 2
            agent_id = f"agent-{next_id:03d}"
        
        # Determine template
        if not template:
            if "media" in specialization.lower() or "download" in specialization.lower():
                template = "media-download-agent"
            elif "database" in specialization.lower() or "db" in specialization.lower():
                template = "database-agent"
            elif "server" in specialization.lower() or "management" in specialization.lower():
                template = "server-management-agent"
            else:
                template = "base-agent"
        
        # Create directories
        agent_dir = project_root / "agents" / "active" / f"{agent_id}-{specialization}"
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        definitions_dir = project_root / "agents" / "registry" / "agent-definitions"
        definitions_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse capabilities
        capabilities_list = [c.strip() for c in capabilities.split(',')]
        
        # Load template
        template_path = project_root / "agents" / "registry" / "agent-templates" / f"{template}.md"
        if template_path.exists():
            template_content = template_path.read_text()
        else:
            # Fallback to base template
            base_template = project_root / "agents" / "registry" / "agent-templates" / "base-agent-template.md"
            template_content = base_template.read_text() if base_template.exists() else ""
        
        # Create agent definition
        definition_content = f"""---
agent_id: {agent_id}
specialization: {specialization}
created_by: {parent_agent_id}
created_date: {datetime.now().strftime("%Y-%m-%d")}
status: ready
parent_agent: {parent_agent_id}
template: {template}
---

# {agent_id.upper()}: {specialization.replace('-', ' ').title()}

## Your Specialization

You specialize in **{specialization.replace('-', ' ').title()}**.

## Your Purpose

You are a specialized agent created to handle tasks requiring expertise in {specialization.replace('-', ' ')}.

## Your Capabilities

### Skills
{chr(10).join(f'- {cap}' for cap in capabilities_list if any(skill in cap.lower() for skill in ['skill', 'workflow', 'troubleshoot', 'deploy']))}

### MCP Tools
{chr(10).join(f'- {cap}' for cap in capabilities_list if 'tool' in cap.lower() or 'mcp' in cap.lower())}

### Domain Knowledge
{chr(10).join(f'- {cap}' for cap in capabilities_list if not any(x in cap.lower() for x in ['skill', 'tool', 'mcp', 'workflow']))}

## Your Tasks

**Task Management**: Use Task Coordination System (`agents/tasks/registry.md`)

### Initial Tasks

{initial_tasks}

Use `query_tasks()` MCP tool to see all assigned tasks.

## Your Prompt

**Read your agent prompt to understand how to work:**
- **Server management agents**: Read `agents/prompts/server.md` (extends base.md)
- **Other agents**: Read `agents/prompts/base.md`
- **Domain-specific**: Check if `agents/prompts/[domain].md` exists

The prompt defines your workflow, principles, and how to use systems (memory, skills, tools).

## How to Work

1. **Read Your Prompt**: Read your agent prompt (see above)
2. **Check Your Tasks**: Use `query_tasks(assignee="{agent_id}")` MCP tool
3. **Check Memory**: Query memory for related decisions and patterns
   - Use `memory_query_decisions()` for related decisions
   - Use `memory_query_patterns()` for common patterns
   - Use `memory_search()` for full-text search
4. **Use Your Specialization**: Leverage your specialized knowledge
5. **Update Status**: Use monitoring tools to update status
6. **Communicate**: Use communication MCP tools to communicate with parent agent
7. **Record Decisions**: Use `memory_record_decision()` for important decisions
8. **Complete Tasks**: Mark tasks complete using task coordination tools

## Communication

### With Parent Agent ({parent_agent_id})

- **Task Assignment**: Use Task Coordination System (`query_tasks()` MCP tool)
- **Status Updates**: Use Monitoring System (`update_agent_status()` MCP tool)
- **Communication**: Use Communication Protocol (`get_agent_messages()` MCP tool)
- **Results**: Document results in RESULTS.md

### File Structure

```
agents/active/{agent_id}-{specialization}/
├── dev-docs/             # Dev docs (plan, context, tasks) - managed by dev docs system
│   └── {task-name}-*.md
├── docs/                 # YOUR documentation (plans, notes, architecture, references)
│   ├── plans/            # Implementation plans
│   ├── notes/            # Working notes, research
│   ├── architecture/     # System designs
│   └── references/       # External references
└── RESULTS.md            # Completed work results

**Note**: Tasks, status, and communication are managed via centralized systems:
- **Tasks**: Task Coordination System (`agents/tasks/registry.md`) - Use `query_tasks()` MCP tool
- **Status**: Monitoring System (dashboard at `localhost:3012`) - Use `update_agent_status()` MCP tool
- **Communication**: Communication Protocol (`agents/communication/`) - Use `get_agent_messages()` MCP tool
```

**⚠️ IMPORTANT**: All your documentation, plans, and notes should go in `docs/` directory, NOT in `agents/docs/`. This ensures proper namespacing and automatic archiving.

## Discovery Workflow

Before starting work:

1. **Read Your Prompt**: Read your agent prompt (see "Your Prompt" section above)
2. **Check Memory**: Query previous decisions and patterns using memory MCP tools
3. **Check Skills**: Review `agents/skills/README.md` for workflows
4. **Check MCP Tools**: Review `agents/apps/agent-mcp/README.md` for available tools
5. **Check Your Tasks**: Use `query_tasks(assignee="{agent_id}")` MCP tool

## Memory Integration

Use memory MCP tools throughout your work:

- **Before Work**: `memory_query_decisions()`, `memory_query_patterns()`, `memory_search()`
- **During Work**: `memory_record_decision()`, `memory_record_pattern()`, `memory_save_context()`
- **After Work**: `memory_save_context(status="completed")`

## Status Updates

Update STATUS.md regularly with:

- Current task progress
- Any blockers
- Next steps
- Questions for parent agent

---

**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Parent Agent**: {parent_agent_id}
"""
        
        # Write agent definition
        definition_path = definitions_dir / f"{agent_id}-{specialization}.md"
        definition_path.write_text(definition_content)
        
        # Note: TASKS.md, STATUS.md, and COMMUNICATION.md are REMOVED
        # Use centralized systems instead:
        # - Task Coordination System (agents/tasks/registry.md) for tasks
        # - Monitoring System (dashboard at localhost:3012) for status
        # - Communication Protocol (agents/communication/) for messaging
        
        # Create RESULTS.md (still used for agent-specific results documentation)
        results_path = agent_dir / "RESULTS.md"
        results_path.write_text(f"# Results for {agent_id.upper()}\n\n## Completed Work\n\n_Results will be documented here._\n")
        
        # Update registry
        registry_path = project_root / "agents" / "registry" / "agent-registry.md"
        if registry_path.exists():
            registry_content = registry_path.read_text()
            
            # Add to ready agents table
            ready_section = "## Ready Agents"
            if ready_section in registry_content:
                # Find the table and add entry
                table_marker = "| Agent ID | Specialization |"
                if table_marker in registry_content:
                    # Insert new row after header
                    new_row = f"| {agent_id} | {specialization} | {parent_agent_id} | {datetime.now().strftime('%Y-%m-%d')} | `agents/registry/agent-definitions/{agent_id}-{specialization}.md` | Task Coordination System |\n"
                    registry_content = registry_content.replace(
                        table_marker + "\n|----------|",
                        table_marker + "\n" + new_row + "|----------|"
                    )
                    
                    # Update last updated
                    if "**Last Updated**:" in registry_content:
                        registry_content = registry_content.replace(
                            "**Last Updated**: ",
                            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        )
                    
                    registry_path.write_text(registry_content)
            
            # Sync registry after creation
            try:
                await sync_agent_registry()
            except:
                pass  # Sync is optional, don't fail if it doesn't work
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "specialization": specialization,
            "definition_path": str(definition_path.relative_to(project_root)),
            "message": f"Agent definition created: {agent_id} ({specialization}). Use Task Coordination System (agents/tasks/registry.md) for tasks."
        }
    
    @with_automatic_logging()

    @server.tool()
    async def query_agent_registry(
        specialization: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query the agent registry for existing agents.
        
        Args:
            specialization: Filter by specialization
            status: Filter by status (active, ready, archived)
            limit: Maximum results
        
        Returns:
            List of matching agents
        """
        registry_path = project_root / "agents" / "registry" / "agent-registry.md"
        
        if not registry_path.exists():
            return {
                "status": "success",
                "count": 0,
                "agents": []
            }
        
        # Simple parsing (can be improved)
        content = registry_path.read_text()
        agents = []
        
        # Parse ready agents table
        if "## Ready Agents" in content:
            ready_section = content.split("## Ready Agents")[1].split("##")[0]
            lines = ready_section.split('\n')
            for line in lines:
                if line.startswith('|') and 'agent-' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 5:
                        agent_id = parts[0]
                        spec = parts[1]
                        created_by = parts[2]
                        created_date = parts[3]
                        
                        if specialization and specialization.lower() not in spec.lower():
                            continue
                        
                        agents.append({
                            "agent_id": agent_id,
                            "specialization": spec,
                            "created_by": created_by,
                            "created_date": created_date,
                            "status": "ready"
                        })
        
        # Filter by status if provided
        if status:
            agents = [a for a in agents if a.get("status") == status.lower()]
        
        # Limit results
        agents = agents[:limit]
        
        return {
            "status": "success",
            "count": len(agents),
            "agents": agents
        }
    
    @with_automatic_logging()

    @server.tool()
    async def assign_task_to_agent(
        agent_id: str,
        task_description: str,
        priority: str = "medium",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign a new task to an existing agent.
        
        Args:
            agent_id: Agent ID to assign task to
            specialization: Agent specialization (used to find agent directory)
            task_description: Description of the task
            priority: Task priority (high, medium, low)
            task_id: Optional task ID (auto-generated if not provided)
        
        Returns:
            Task assignment confirmation
        """
        # Find agent directory
        active_dir = project_root / "agents" / "active"
        agent_dirs = [d for d in active_dir.iterdir() if d.is_dir() and agent_id in d.name]
        
        if not agent_dirs:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in active agents"
            }
        
        agent_dir = agent_dirs[0]
        
        # Note: TASKS.md is REMOVED - use Task Coordination System instead
        # Generate task ID if not provided (for registry)
        if not task_id:
            # Use task coordination system to generate ID
            from tools.task_coordination import _parse_registry, _generate_task_id
            existing_tasks = _parse_registry()
            project = "agent-tasks"  # Default project name
            task_id = _generate_task_id(project, existing_tasks)
        
        # Also register in central task registry
        try:
            # Import task coordination functions
            # Use relative import since both are in tools/
            import sys
            from pathlib import Path
            tools_dir = Path(__file__).parent
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            from task_coordination import _parse_registry, _write_registry, _generate_task_id
            
            # Determine project from agent_id or use default
            project = "agent-tasks"  # Default project name
            
            # Parse existing tasks
            existing_tasks = _parse_registry()
            
            # Generate task ID for registry
            registry_task_id = _generate_task_id(project, existing_tasks)
            
            # Create task for registry
            registry_task = {
                "task_id": registry_task_id,
                "title": task_description[:100] if len(task_description) > 100 else task_description,
                "description": task_description[:500] if len(task_description) > 500 else task_description,
                "status": "pending",
                "assignee": "-",
                "priority": priority.lower(),
                "dependencies": "-",
                "project": project,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add to registry
            existing_tasks.append(registry_task)
            _write_registry(existing_tasks)
            
            registry_registered = True
            registry_task_id_used = registry_task_id
        except Exception as e:
            # If registry registration fails, return error
            return {
                "status": "error",
                "message": f"Failed to register task in Task Coordination System: {str(e)}",
                "error_type": type(e).__name__
            }
        
        # Note: TASKS.md is REMOVED - tasks are only in Task Coordination System
        result = {
            "status": "success",
            "agent_id": agent_id,
            "task_id": registry_task_id_used,
            "message": f"Task {registry_task_id_used} assigned to {agent_id} and registered in Task Coordination System (agents/tasks/registry.md)"
        }
        
        return result
    
    @with_automatic_logging()

    @server.tool()
    async def sync_agent_registry() -> Dict[str, Any]:
        """
        Sync agent registry markdown from monitoring DB and definition files.
        
        This generates agents/registry/agent-registry.md from:
        - Agent definitions (source of truth for metadata)
        - Monitoring DB (source of truth for status)
        - Active/archive directories (source of truth for location)
        
        Returns:
            Sync confirmation and statistics
        """
        try:
            # Import sync function
            sync_script = project_root / "agents" / "registry" / "sync_registry.py"
            if not sync_script.exists():
                return {
                    "status": "error",
                    "message": "Sync script not found"
                }
            
            # Run sync script
            import subprocess
            result = subprocess.run(
                [sys.executable, str(sync_script)],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "Registry synced successfully",
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Sync failed: {result.stderr}",
                    "output": result.stdout
                }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @with_automatic_logging()

    @server.tool()
    async def archive_agent(
        agent_id: str,
        reason: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Archive an agent (move to archive state).
        
        Args:
            agent_id: Agent ID to archive
            reason: Reason for archiving (optional)
            force: Force archive even if tasks pending (default: False)
        
        Returns:
            Archive confirmation and details
        """
        try:
            # Find agent directory
            active_dir = project_root / "agents" / "active"
            archive_dir = project_root / "agents" / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            agent_dirs = [d for d in active_dir.iterdir() if d.is_dir() and agent_id in d.name]
            
            if not agent_dirs:
                # Check if already archived
                archived_dirs = [d for d in archive_dir.iterdir() if d.is_dir() and agent_id in d.name]
                if archived_dirs:
                    return {
                        "status": "error",
                        "message": f"Agent {agent_id} is already archived"
                    }
                return {
                    "status": "error",
                    "message": f"Agent {agent_id} not found in active agents"
                }
            
            agent_dir = agent_dirs[0]
            
            # Check for pending tasks in Task Coordination System (unless force)
            if not force:
                from tools.task_coordination import query_tasks
                try:
                    pending_tasks = query_tasks(assignee=agent_id, status="in_progress", limit=1)
                    if pending_tasks.get("count", 0) > 0:
                        return {
                            "status": "error",
                            "message": f"Agent {agent_id} has pending tasks in Task Coordination System. Use force=True to archive anyway.",
                            "action": "Complete or cancel tasks before archiving"
                        }
            
            # Check for active monitoring session (if monitoring available)
            try:
                from tools.activity_monitoring import get_agent_status
                status = await get_agent_status(agent_id)
                if status and status.get("status") == "active":
                    return {
                        "status": "error",
                        "message": f"Agent {agent_id} has active monitoring session. End session before archiving."
                    }
            except:
                pass  # Monitoring not available, continue
            
            # Get agent specialization from directory name
            specialization = agent_dir.name.replace(f"{agent_id}-", "")
            
            # Move agent directory to archive
            archive_agent_dir = archive_dir / agent_dir.name
            if archive_agent_dir.exists():
                # If archive already exists, add timestamp
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                archive_agent_dir = archive_dir / f"{agent_dir.name}-{timestamp}"
            
            agent_dir.rename(archive_agent_dir)
            
            # Update agent definition
            definitions_dir = project_root / "agents" / "registry" / "agent-definitions"
            definition_files = list(definitions_dir.glob(f"{agent_id}-*.md"))
            
            if definition_files:
                definition_path = definition_files[0]
                definition_content = definition_path.read_text()
                
                # Update frontmatter
                if definition_content.startswith("---"):
                    parts = definition_content.split("---", 2)
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        metadata["status"] = "archived"
                        metadata["archived_date"] = datetime.now().strftime("%Y-%m-%d")
                        if reason:
                            metadata["archived_reason"] = reason
                        
                        # Rewrite definition
                        new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{parts[2]}"
                        definition_path.write_text(new_content)
            
            # Update registry
            registry_path = project_root / "agents" / "registry" / "agent-registry.md"
            if registry_path.exists():
                registry_content = registry_path.read_text()
                
                # Remove from Active Agents table
                if "## Active Agents" in registry_content:
                    active_section = registry_content.split("## Active Agents")[1].split("##")[0]
                    lines = active_section.split('\n')
                    new_lines = []
                    for line in lines:
                        if agent_id not in line or line.startswith('|---'):
                            new_lines.append(line)
                    registry_content = registry_content.replace(active_section, '\n'.join(new_lines))
                
                # Remove from Ready Agents table
                if "## Ready Agents" in registry_content:
                    ready_section = registry_content.split("## Ready Agents")[1].split("## Archived Agents")[0]
                    lines = ready_section.split('\n')
                    new_lines = []
                    for line in lines:
                        if agent_id not in line or line.startswith('|---'):
                            new_lines.append(line)
                    registry_content = registry_content.replace(
                        "## Ready Agents" + ready_section,
                        "## Ready Agents\n" + '\n'.join(new_lines)
                    )
                
                # Add to Archived Agents table
                if "## Archived Agents" in registry_content:
                    archived_section = registry_content.split("## Archived Agents")[1]
                    table_marker = "| Agent ID | Specialization |"
                    if table_marker in archived_section:
                        new_row = f"| {agent_id} | {specialization} | {metadata.get('created_by', 'unknown')} | {datetime.now().strftime('%Y-%m-%d')} | `agents/archive/{archive_agent_dir.name}/` |\n"
                        archived_section = archived_section.replace(
                            table_marker + "\n|----------|",
                            table_marker + "\n" + new_row + "|----------|"
                        )
                        registry_content = registry_content.replace(
                            "## Archived Agents" + registry_content.split("## Archived Agents")[1],
                            "## Archived Agents" + archived_section
                        )
                
                # Update last updated
                if "**Last Updated**:" in registry_content:
                    registry_content = registry_content.replace(
                        "**Last Updated**: ",
                        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                
                registry_path.write_text(registry_content)
            
            # Sync registry after archiving
            try:
                await sync_agent_registry()
            except:
                pass  # Sync is optional, don't fail if it doesn't work
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "archive_location": str(archive_agent_dir.relative_to(project_root)),
                "message": f"Agent {agent_id} archived successfully",
                "reason": reason or "No reason provided"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @with_automatic_logging()

    @server.tool()
    async def reactivate_agent(
        agent_id: str,
        new_tasks: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reactivate an archived agent.
        
        Args:
            agent_id: Agent ID to reactivate
            new_tasks: Optional new tasks to assign (optional)
        
        Returns:
            Reactivation confirmation and details
        """
        try:
            # Find agent in archive
            archive_dir = project_root / "agents" / "archive"
            active_dir = project_root / "agents" / "active"
            active_dir.mkdir(parents=True, exist_ok=True)
            
            archived_dirs = [d for d in archive_dir.iterdir() if d.is_dir() and agent_id in d.name]
            
            if not archived_dirs:
                # Check if already active
                active_dirs = [d for d in active_dir.iterdir() if d.is_dir() and agent_id in d.name]
                if active_dirs:
                    return {
                        "status": "error",
                        "message": f"Agent {agent_id} is already active"
                    }
                return {
                    "status": "error",
                    "message": f"Agent {agent_id} not found in archive"
                }
            
            # Use most recent archive if multiple
            archived_dir = sorted(archived_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            
            # Get specialization from directory name
            specialization = archived_dir.name.replace(f"{agent_id}-", "").split("-")[0]  # Handle timestamp suffix
            
            # Move back to active
            active_agent_dir = active_dir / f"{agent_id}-{specialization}"
            if active_agent_dir.exists():
                # If active directory exists, add timestamp
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                active_agent_dir = active_dir / f"{agent_id}-{specialization}-{timestamp}"
            
            archived_dir.rename(active_agent_dir)
            
            # Update agent definition
            definitions_dir = project_root / "agents" / "registry" / "agent-definitions"
            definition_files = list(definitions_dir.glob(f"{agent_id}-*.md"))
            
            if definition_files:
                definition_path = definition_files[0]
                definition_content = definition_path.read_text()
                
                # Update frontmatter
                if definition_content.startswith("---"):
                    parts = definition_content.split("---", 2)
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        metadata["status"] = "ready"  # Reactivated agents start as ready
                        metadata["reactivated_date"] = datetime.now().strftime("%Y-%m-%d")
                        if "archived_date" in metadata:
                            metadata["archived_date"] = None  # Clear archived date
                        
                        # Rewrite definition
                        new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{parts[2]}"
                        definition_path.write_text(new_content)
            
            # Update registry
            registry_path = project_root / "agents" / "registry" / "agent-registry.md"
            if registry_path.exists():
                registry_content = registry_path.read_text()
                
                # Remove from Archived Agents table
                if "## Archived Agents" in registry_content:
                    archived_section = registry_content.split("## Archived Agents")[1]
                    lines = archived_section.split('\n')
                    new_lines = []
                    for line in lines:
                        if agent_id not in line or line.startswith('|---'):
                            new_lines.append(line)
                    registry_content = registry_content.replace(
                        "## Archived Agents" + archived_section,
                        "## Archived Agents\n" + '\n'.join(new_lines)
                    )
                
                # Add to Ready Agents table
                if "## Ready Agents" in registry_content:
                    ready_section = registry_content.split("## Ready Agents")[1].split("## Archived Agents")[0]
                    table_marker = "| Agent ID | Specialization |"
                    if table_marker in ready_section:
                        created_by = metadata.get("created_by", "unknown")
                        new_row = f"| {agent_id} | {specialization} | {created_by} | {datetime.now().strftime('%Y-%m-%d')} | `agents/registry/agent-definitions/{agent_id}-{specialization}.md` | Task Coordination System |\n"
                        ready_section = ready_section.replace(
                            table_marker + "\n|----------|",
                            table_marker + "\n" + new_row + "|----------|"
                        )
                        registry_content = registry_content.replace(
                            "## Ready Agents" + registry_content.split("## Ready Agents")[1].split("## Archived Agents")[0],
                            "## Ready Agents" + ready_section
                        )
                
                # Update last updated
                if "**Last Updated**:" in registry_content:
                    registry_content = registry_content.replace(
                        "**Last Updated**: ",
                        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                
                registry_path.write_text(registry_content)
            
            # Sync registry after reactivation
            try:
                await sync_agent_registry()
            except:
                pass  # Sync is optional, don't fail if it doesn't work
            
            # Optionally assign new tasks
            task_assigned = False
            if new_tasks:
                try:
                    # Call assign_task_to_agent from this module
                    task_result = await assign_task_to_agent(
                        agent_id=agent_id,
                        task_description=new_tasks,
                        priority="medium"
                    )
                    task_assigned = task_result.get("status") == "success"
                except Exception as e:
                    # Task assignment failed, but reactivation succeeded
                    pass
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "active_location": str(active_agent_dir.relative_to(project_root)),
                "message": f"Agent {agent_id} reactivated successfully",
                "task_assigned": task_assigned
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

