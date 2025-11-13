"""
Memory Management Tools for MCP Server

Provides tools for agents to query and record memories (decisions, patterns, context).
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.memory import get_memory
from mcp.server import Server
from mcp.types import Tool


def register_memory_tools(server: Server):
    """Register memory management tools with MCP server."""
    
    @server.tool()
    async def memory_query_decisions(
        project: Optional[str] = None,
        task: Optional[str] = None,
        tags: Optional[str] = None,
        min_importance: float = 0.0,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query decisions from memory.
        
        Args:
            project: Filter by project name
            task: Filter by task ID or name (partial match)
            tags: Comma-separated list of tags to filter by
            min_importance: Minimum importance score (0.0-1.0)
            search_text: Full-text search query
            limit: Maximum number of results
        
        Returns:
            List of decisions matching criteria
        """
        memory = get_memory()
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        decisions = memory.query_decisions(
            project=project,
            task=task,
            tags=tag_list,
            min_importance=min_importance,
            search_text=search_text,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(decisions),
            "decisions": decisions
        }
    
    @server.tool()
    async def memory_query_patterns(
        severity: Optional[str] = None,
        tags: Optional[str] = None,
        min_frequency: int = 1,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query patterns from memory.
        
        Args:
            severity: Filter by severity (low, medium, high)
            tags: Comma-separated list of tags to filter by
            min_frequency: Minimum frequency count
            search_text: Full-text search query
            limit: Maximum number of results
        
        Returns:
            List of patterns matching criteria
        """
        memory = get_memory()
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        patterns = memory.query_patterns(
            severity=severity,
            tags=tag_list,
            min_frequency=min_frequency,
            search_text=search_text,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(patterns),
            "patterns": patterns
        }
    
    @server.tool()
    async def memory_search(
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Full-text search across all memories (decisions and patterns).
        
        Args:
            query: Search query text
            limit: Maximum results per type
        
        Returns:
            Search results with decisions and patterns
        """
        memory = get_memory()
        
        results = memory.search(query, limit=limit)
        
        return {
            "status": "success",
            "query": query,
            "total": results["total"],
            "decisions_count": len(results["decisions"]),
            "patterns_count": len(results["patterns"]),
            "decisions": results["decisions"],
            "patterns": results["patterns"]
        }
    
    @server.tool()
    async def memory_record_decision(
        content: str,
        rationale: str = "",
        project: str = "home-server",
        task: str = "",
        importance: float = 0.5,
        tags: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a decision in memory.
        
        Args:
            content: Decision description
            rationale: Why this decision was made
            project: Project name (default: home-server)
            task: Task ID or name
            importance: Importance score 0.0-1.0 (default: 0.5)
            tags: Comma-separated list of tags
        
        Returns:
            Decision ID and confirmation
        """
        memory = get_memory()
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        decision_id = memory.record_decision(
            content=content,
            rationale=rationale,
            project=project,
            task=task,
            importance=importance,
            tags=tag_list
        )
        
        return {
            "status": "success",
            "decision_id": decision_id,
            "message": f"Decision recorded: {content[:50]}..."
        }
    
    @server.tool()
    async def memory_record_pattern(
        name: str,
        description: str,
        solution: str = "",
        severity: str = "medium",
        frequency: int = 1,
        tags: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record or update a pattern in memory.
        
        Args:
            name: Pattern name
            description: Pattern description
            solution: Solution or workaround
            severity: low, medium, or high (default: medium)
            frequency: Frequency count (default: 1, increments if pattern exists)
            tags: Comma-separated list of tags
        
        Returns:
            Pattern ID and confirmation
        """
        memory = get_memory()
        
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        pattern_id = memory.record_pattern(
            name=name,
            description=description,
            solution=solution,
            severity=severity,
            frequency=frequency,
            tags=tag_list
        )
        
        return {
            "status": "success",
            "pattern_id": pattern_id,
            "message": f"Pattern recorded: {name}"
        }
    
    @server.tool()
    async def memory_save_context(
        agent_id: str,
        task: str,
        current_work: str,
        status: str = "in_progress",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Save or update current work context.
        
        Args:
            agent_id: Agent identifier
            task: Task ID or name
            current_work: Description of current work
            status: in_progress, completed, or blocked (default: in_progress)
            notes: Additional notes
        
        Returns:
            Context ID and confirmation
        """
        memory = get_memory()
        
        context_id = memory.save_context(
            agent_id=agent_id,
            task=task,
            current_work=current_work,
            status=status,
            notes=notes
        )
        
        return {
            "status": "success",
            "context_id": context_id,
            "message": f"Context saved for {agent_id} - {task}"
        }
    
    @server.tool()
    async def memory_get_recent_context(
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get recent work context.
        
        Args:
            agent_id: Filter by agent ID (optional)
            limit: Maximum number of results
        
        Returns:
            List of recent context entries
        """
        memory = get_memory()
        
        conn = sqlite3.connect(memory.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM context"
        params = []
        
        if agent_id:
            query += " WHERE agent_id = ?"
            params.append(agent_id)
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        contexts = [dict(row) for row in rows]
        
        conn.close()
        
        return {
            "status": "success",
            "count": len(contexts),
            "contexts": contexts
        }
    
    @server.tool()
    async def memory_get_context_by_task(
        task: str
    ) -> Dict[str, Any]:
        """
        Get context for a specific task.
        
        Args:
            task: Task ID or name
        
        Returns:
            Context entry for the task
        """
        memory = get_memory()
        
        conn = sqlite3.connect(memory.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM context 
            WHERE task = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (task,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "status": "success",
                "context": dict(row)
            }
        else:
            return {
                "status": "not_found",
                "message": f"No context found for task: {task}"
            }
    
    @server.tool()
    async def memory_export_to_markdown(
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all memories to markdown files for human review.
        
        Args:
            output_path: Optional output directory path (defaults to agents/memory/memory/export/)
        
        Returns:
            Export path and file counts
        """
        memory = get_memory()
        
        export_path = Path(output_path) if output_path else None
        result_path = memory.export_to_markdown(export_path)
        
        # Count exported files
        decisions_path = result_path / "decisions"
        patterns_path = result_path / "patterns"
        
        decisions_count = len(list(decisions_path.glob("*.md"))) if decisions_path.exists() else 0
        patterns_count = len(list(patterns_path.glob("*.md"))) if patterns_path.exists() else 0
        
        return {
            "status": "success",
            "export_path": str(result_path),
            "decisions_exported": decisions_count,
            "patterns_exported": patterns_count,
            "message": f"Exported {decisions_count} decisions and {patterns_count} patterns to markdown"
        }

