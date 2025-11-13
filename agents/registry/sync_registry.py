"""
Sync Agent Registry from Monitoring DB and Definition Files

This script generates the agent-registry.md file from:
1. Agent definitions (agents/registry/agent-definitions/*.md)
2. Monitoring DB status (agents/apps/agent-monitoring/data/agent_activity.db)
3. Active/archive directories (agents/active/, agents/archive/)

The monitoring DB is the source of truth for agent status.
"""

import sys
import sqlite3
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Paths
REGISTRY_PATH = project_root / "agents" / "registry" / "agent-registry.md"
DEFINITIONS_DIR = project_root / "agents" / "registry" / "agent-definitions"
ACTIVE_DIR = project_root / "agents" / "active"
ARCHIVE_DIR = project_root / "agents" / "archive"
MONITORING_DB = project_root / "apps" / "agent-monitoring" / "data" / "agent_activity.db"


def get_agent_status_from_db(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent status from monitoring DB."""
    if not MONITORING_DB.exists():
        return None
    
    try:
        conn = sqlite3.connect(MONITORING_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM agent_status WHERE agent_id = ?
        """, (agent_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception:
        return None


def get_all_agent_statuses() -> Dict[str, Dict[str, Any]]:
    """Get all agent statuses from monitoring DB."""
    if not MONITORING_DB.exists():
        return {}
    
    try:
        conn = sqlite3.connect(MONITORING_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agent_status")
        rows = cursor.fetchall()
        conn.close()
        
        return {dict(row)["agent_id"]: dict(row) for row in rows}
    except Exception:
        return {}


def parse_agent_definition(definition_path: Path) -> Optional[Dict[str, Any]]:
    """Parse agent definition file and extract metadata."""
    if not definition_path.exists():
        return None
    
    try:
        content = definition_path.read_text()
        
        if not content.startswith("---"):
            return None
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        
        metadata = yaml.safe_load(parts[1])
        
        # Extract agent_id from filename if not in metadata
        if "agent_id" not in metadata:
            filename = definition_path.stem
            # Try to extract agent_id from filename (e.g., "agent-002-media-download")
            if filename.startswith("agent-"):
                metadata["agent_id"] = filename.split("-")[0] + "-" + filename.split("-")[1]
        
        return metadata
    except Exception:
        return None


def get_agent_location(agent_id: str, specialization: str) -> Tuple[Optional[str], str]:
    """Get agent location (active or archive)."""
    # Check active
    active_dirs = list(ACTIVE_DIR.glob(f"{agent_id}-*"))
    if active_dirs:
        return ("active", str(active_dirs[0].relative_to(project_root)))
    
    # Check archive
    archive_dirs = list(ARCHIVE_DIR.glob(f"{agent_id}-*"))
    if archive_dirs:
        return ("archive", str(archive_dirs[0].relative_to(project_root)))
    
    return (None, "")


def sync_registry():
    """Generate agent-registry.md from definitions and monitoring DB."""
    
    # Get all agent definitions
    definitions = {}
    if DEFINITIONS_DIR.exists():
        for def_file in DEFINITIONS_DIR.glob("*.md"):
            metadata = parse_agent_definition(def_file)
            if metadata and metadata.get("agent_id"):
                definitions[metadata["agent_id"]] = metadata
    
    # Get all agent statuses from monitoring DB
    db_statuses = get_all_agent_statuses()
    
    # Categorize agents
    active_agents = []
    ready_agents = []
    archived_agents = []
    
    for agent_id, definition in definitions.items():
        specialization = definition.get("specialization", "")
        created_by = definition.get("created_by", "unknown")
        created_date = definition.get("created_date", "")
        status = definition.get("status", "ready")
        
        # Get status from DB if available
        db_status = db_statuses.get(agent_id)
        if db_status:
            # Use DB status as source of truth
            status = db_status.get("status", status)
        
        # Get location
        location_type, location_path = get_agent_location(agent_id, specialization)
        
        # Determine category
        if status == "archived" or location_type == "archive":
            archived_agents.append({
                "agent_id": agent_id,
                "specialization": specialization,
                "created_by": created_by,
                "completed_date": definition.get("archived_date", ""),
                "archive_location": location_path if location_type == "archive" else ""
            })
        elif status == "active" or (db_status and db_status.get("status") == "active"):
            active_agents.append({
                "agent_id": agent_id,
                "specialization": specialization,
                "created_by": created_by,
                "created_date": created_date,
                "status": db_status.get("status", "active") if db_status else "active",
                "location": location_path if location_type == "active" else f"agents/active/{agent_id}-{specialization}/"
            })
        else:
            # Ready agents
            ready_agents.append({
                "agent_id": agent_id,
                "specialization": specialization,
                "created_by": created_by,
                "created_date": created_date,
                "definition": f"agents/registry/agent-definitions/{agent_id}-{specialization}.md",
                "tasks": f"agents/active/{agent_id}-{specialization}/TASKS.md" if location_type == "active" else ""
            })
    
    # Generate registry markdown
    registry_content = f"""# Agent Registry

Master registry of all agents (active, ready, and archived).

**⚠️ NOTE**: This file is auto-generated from:
- Agent definitions (`agents/registry/agent-definitions/`)
- Monitoring DB (`agents/apps/agent-monitoring/data/agent_activity.db`)
- Active/archive directories

**Source of Truth**: Monitoring DB for status, Definition files for metadata.

**Last Synced**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Registry Status

- **Active Agents**: Agents currently working on tasks (status from monitoring DB)
- **Ready Agents**: Agent definitions ready for activation
- **Archived Agents**: Completed agents moved to archive

## Active Agents

| Agent ID | Specialization | Created By | Created Date | Status | Location |
|----------|---------------|------------|--------------|--------|----------|
"""
    
    if active_agents:
        for agent in active_agents:
            registry_content += f"| {agent['agent_id']} | {agent['specialization']} | {agent['created_by']} | {agent['created_date']} | {agent['status']} | `{agent['location']}` |\n"
    else:
        registry_content += "| - | - | - | - | - | - |\n"
    
    registry_content += """
## Ready Agents

| Agent ID | Specialization | Created By | Created Date | Definition | Tasks |
|----------|---------------|------------|--------------|------------|-------|
"""
    
    if ready_agents:
        for agent in ready_agents:
            registry_content += f"| {agent['agent_id']} | {agent['specialization']} | {agent['created_by']} | {agent['created_date']} | `{agent['definition']}` | `{agent['tasks']}` |\n"
    else:
        registry_content += "| - | - | - | - | - | - |\n"
    
    registry_content += """
## Archived Agents

| Agent ID | Specialization | Created By | Completed Date | Archive Location |
|----------|---------------|------------|----------------|------------------|
"""
    
    if archived_agents:
        for agent in archived_agents:
            registry_content += f"| {agent['agent_id']} | {agent['specialization']} | {agent['created_by']} | {agent['completed_date']} | `{agent['archive_location']}` |\n"
    else:
        registry_content += "| - | - | - | - | - |\n"
    
    registry_content += f"""
## How to Use

### For Agents Creating New Agents

1. Use `create_agent_definition` MCP tool to create agent definition
2. Agent will be added to "Ready Agents" table (after sync)
3. Human activates agent by opening new Cursor session with agent definition
4. Agent status updates automatically via monitoring system

### For Humans Activating Agents

1. Review agent definition in `agents/registry/agent-definitions/`
2. Open new Cursor session
3. Load agent definition as prompt
4. Agent will move to "Active Agents" when working (via monitoring system)

### For Agents Checking Registry

1. Query registry using `query_agent_registry` MCP tool
2. Or read this file directly
3. Check for existing agents with required specialization

### Syncing Registry

To regenerate this file:
```bash
python agents/registry/sync_registry.py
```

Or use MCP tool: `sync_agent_registry()`

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Agents**: {len(active_agents)} active, {len(ready_agents)} ready, {len(archived_agents)} archived
"""
    
    # Write registry
    REGISTRY_PATH.write_text(registry_content)
    print(f"✅ Registry synced: {len(active_agents)} active, {len(ready_agents)} ready, {len(archived_agents)} archived")


if __name__ == "__main__":
    sync_registry()

