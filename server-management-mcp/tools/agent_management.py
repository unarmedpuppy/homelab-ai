"""
Agent Management Tools for MCP Server

Provides tools for agents to create specialized agent definitions and manage agent registry.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server


def register_agent_management_tools(server: Server):
    """Register agent management tools with MCP server."""
    
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

**Primary Task Location**: `agents/active/{agent_id}-{specialization}/TASKS.md`

### Initial Tasks

{initial_tasks}

Read your TASKS.md file to see all assigned tasks.

## How to Work

1. **Read Your Tasks**: Check `agents/active/{agent_id}-{specialization}/TASKS.md`
2. **Check Memory**: Query memory for related decisions and patterns
   - Use `memory_query_decisions()` for related decisions
   - Use `memory_query_patterns()` for common patterns
   - Use `memory_search()` for full-text search
3. **Use Your Specialization**: Leverage your specialized knowledge
4. **Update Status**: Regularly update `STATUS.md` with progress
5. **Communicate**: Use `COMMUNICATION.md` to communicate with parent agent
6. **Record Decisions**: Use `memory_record_decision()` for important decisions
7. **Complete Tasks**: Mark tasks complete in TASKS.md

## Communication

### With Parent Agent ({parent_agent_id})

- **Task Assignment**: Check TASKS.md for new tasks
- **Status Updates**: Update STATUS.md regularly
- **Guidance**: Check COMMUNICATION.md for parent guidance
- **Results**: Document results in RESULTS.md

### File Structure

```
agents/active/{agent_id}-{specialization}/
├── TASKS.md              # Your assigned tasks
├── STATUS.md             # Your current status
├── COMMUNICATION.md      # Parent-child communication
└── RESULTS.md            # Completed work results
```

## Discovery Workflow

Before starting work:

1. **Check Memory**: Query previous decisions and patterns using memory MCP tools
2. **Check Skills**: Review `server-management-skills/README.md` for workflows
3. **Check MCP Tools**: Review `server-management-mcp/README.md` for available tools
4. **Read Your Tasks**: Check TASKS.md

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
        
        # Create TASKS.md
        tasks_content = f"""# Tasks for {agent_id.upper()}

## Assigned Tasks

### Initial Task
**Assigned By**: {parent_agent_id}
**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: PENDING

**Description**:
{initial_tasks}

**Steps**:
1. Review task description
2. Check memory for related decisions
3. Use specialized knowledge to complete task
4. Update status as you work
5. Mark complete when done

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        tasks_path = agent_dir / "TASKS.md"
        tasks_path.write_text(tasks_content)
        
        # Create STATUS.md
        status_content = f"""# Status for {agent_id.upper()}

## Current Status

**Agent ID**: {agent_id}
**Specialization**: {specialization}
**Status**: READY
**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Current Task

**Task**: Initial task assignment
**Status**: PENDING
**Progress**: 0%

## Notes

Waiting for activation...

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        status_path = agent_dir / "STATUS.md"
        status_path.write_text(status_content)
        
        # Create COMMUNICATION.md
        comm_content = f"""# Communication for {agent_id.upper()}

## Messages from Parent Agent ({parent_agent_id})

### Initial Assignment
**From**: {parent_agent_id}
**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Welcome! You have been created to handle specialized tasks in {specialization.replace('-', ' ')}.

Please review your TASKS.md file and begin work.

---

## Messages to Parent Agent

_Add messages here when you need to communicate with your parent agent._

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        comm_path = agent_dir / "COMMUNICATION.md"
        comm_path.write_text(comm_content)
        
        # Create RESULTS.md
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
                    new_row = f"| {agent_id} | {specialization} | {parent_agent_id} | {datetime.now().strftime('%Y-%m-%d')} | `agents/registry/agent-definitions/{agent_id}-{specialization}.md` | `agents/active/{agent_id}-{specialization}/TASKS.md` |\n"
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
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "specialization": specialization,
            "definition_path": str(definition_path.relative_to(project_root)),
            "tasks_path": str(tasks_path.relative_to(project_root)),
            "status_path": str(status_path.relative_to(project_root)),
            "message": f"Agent definition created: {agent_id} ({specialization})"
        }
    
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
        tasks_path = agent_dir / "TASKS.md"
        
        if not tasks_path.exists():
            return {
                "status": "error",
                "message": f"TASKS.md not found for agent {agent_id}"
            }
        
        # Generate task ID if not provided
        if not task_id:
            # Read existing tasks to find next ID
            tasks_content = tasks_path.read_text()
            import re
            task_matches = re.findall(r'### T(\d+)\.(\d+)', tasks_content)
            if task_matches:
                max_task = max([int(m[0]) * 100 + int(m[1]) for m in task_matches])
                task_id = f"T{max_task // 100}.{(max_task % 100) + 1}"
            else:
                task_id = "T1.1"
        
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
            
            # Generate task ID for registry (may differ from TASKS.md ID)
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
            # If registry registration fails, continue with TASKS.md only
            registry_registered = False
            registry_task_id_used = None
        
        # Append new task to agent's TASKS.md
        new_task = f"""
### {task_id}: {task_description[:50]}...
**Assigned By**: [Parent Agent]
**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Priority**: {priority.upper()}
**Status**: PENDING
{f"**Registry Task ID**: {registry_task_id_used}" if registry_registered else ""}

**Description**:
{task_description}

**Steps**:
1. Review task description
2. Check memory for related decisions
3. Use specialized knowledge to complete task
4. Update status as you work
5. Mark complete when done

---
"""
        
        # Append to tasks file
        tasks_content = tasks_path.read_text()
        tasks_content += new_task
        tasks_path.write_text(tasks_content)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "task_id": task_id,
            "message": f"Task {task_id} assigned to {agent_id}"
        }

