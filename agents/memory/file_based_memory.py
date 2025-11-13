"""
File-Based Memory System for Cursor/Claude Desktop Agents

Since agents run in Cursor/Claude Desktop (not Python), we use file-based memory
that agents can read/write directly.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import os


class FileBasedMemory:
    """
    File-based memory system for agents running in Cursor/Claude Desktop.
    
    Stores memories as markdown files organized by type:
    - decisions/ - Architectural and design decisions
    - patterns/ - Common patterns and learnings
    - context/ - Current work context
    - sessions/ - Session summaries
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize file-based memory system.
        
        Args:
            base_path: Base directory for memory files (defaults to agents/memory/)
        """
        if base_path is None:
            base_path = Path(__file__).parent / "memory"
        self.base_path = Path(base_path)
        
        # Create directory structure
        self.decisions_path = self.base_path / "decisions"
        self.patterns_path = self.base_path / "patterns"
        self.context_path = self.base_path / "context"
        self.sessions_path = self.base_path / "sessions"
        self.index_path = self.base_path / "index.json"
        
        # Create directories
        for path in [self.decisions_path, self.patterns_path, self.context_path, self.sessions_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize index
        self._init_index()
    
    def _init_index(self):
        """Initialize or load memory index."""
        if not self.index_path.exists():
            self.index = {
                "decisions": [],
                "patterns": [],
                "contexts": [],
                "sessions": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_index()
        else:
            with open(self.index_path, 'r') as f:
                self.index = json.load(f)
    
    def _save_index(self):
        """Save memory index."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def record_decision(
        self,
        content: str,
        rationale: str = "",
        alternatives: List[str] = None,
        project: str = "home-server",
        task: str = "",
        importance: float = 0.5,
        tags: List[str] = None
    ) -> str:
        """
        Record a decision.
        
        Args:
            content: Decision description
            rationale: Why this decision was made
            alternatives: Alternatives considered
            project: Project name
            task: Task ID or name
            importance: Importance score (0.0-1.0)
            tags: Tags for categorization
        
        Returns:
            File path of recorded decision
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H-%M-%S")
        
        # Create filename from content (sanitized)
        filename_safe = "".join(c for c in content[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename_safe = filename_safe.replace(' ', '-').lower()
        filename = f"{date_str}-{time_str}-{filename_safe}.md"
        filepath = self.decisions_path / filename
        
        # Create decision content
        decision_content = f"""# Decision: {content}

**Date**: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Project**: {project}
**Task**: {task}
**Importance**: {importance}

## Decision

{content}

## Rationale

{rationale}

"""
        
        if alternatives:
            decision_content += "## Alternatives Considered\n\n"
            for alt in alternatives:
                decision_content += f"- {alt}\n"
            decision_content += "\n"
        
        if tags:
            decision_content += "## Tags\n\n"
            for tag in tags:
                decision_content += f"- {tag}\n"
            decision_content += "\n"
        
        decision_content += f"---\n\n**Recorded**: {timestamp.isoformat()}\n"
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(decision_content)
        
        # Update index
        decision_entry = {
            "file": str(filepath.relative_to(self.base_path)),
            "content": content,
            "date": date_str,
            "project": project,
            "task": task,
            "importance": importance,
            "tags": tags or []
        }
        self.index["decisions"].append(decision_entry)
        self._save_index()
        
        return str(filepath)
    
    def record_pattern(
        self,
        name: str,
        description: str,
        examples: List[str] = None,
        solution: str = "",
        frequency: int = 1,
        severity: str = "medium",
        tags: List[str] = None
    ) -> str:
        """
        Record a pattern (common issue, solution, etc.).
        
        Args:
            name: Pattern name
            description: Pattern description
            examples: Example occurrences
            solution: Solution or workaround
            frequency: How often this occurs
            severity: low, medium, high
            tags: Tags for categorization
        
        Returns:
            File path of recorded pattern
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        filename_safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename_safe = filename_safe.replace(' ', '-').lower()
        filename = f"{filename_safe}.md"
        filepath = self.patterns_path / filename
        
        # Create pattern content
        pattern_content = f"""# Pattern: {name}

**Severity**: {severity}
**Frequency**: {frequency}
**Last Updated**: {date_str}

## Description

{description}

"""
        
        if solution:
            pattern_content += f"## Solution\n\n{solution}\n\n"
        
        if examples:
            pattern_content += "## Examples\n\n"
            for i, example in enumerate(examples, 1):
                pattern_content += f"{i}. {example}\n"
            pattern_content += "\n"
        
        if tags:
            pattern_content += "## Tags\n\n"
            for tag in tags:
                pattern_content += f"- {tag}\n"
            pattern_content += "\n"
        
        pattern_content += f"---\n\n**Last Updated**: {timestamp.isoformat()}\n"
        
        # Write or update file
        if filepath.exists():
            # Update existing pattern (increment frequency)
            with open(filepath, 'r') as f:
                existing = f.read()
            # Update frequency in content
            pattern_content = existing.replace(
                f"**Frequency**: {frequency - 1}",
                f"**Frequency**: {frequency}"
            ) if f"**Frequency**: {frequency - 1}" in existing else pattern_content
        
        with open(filepath, 'w') as f:
            f.write(pattern_content)
        
        # Update index
        pattern_entry = {
            "file": str(filepath.relative_to(self.base_path)),
            "name": name,
            "severity": severity,
            "frequency": frequency,
            "tags": tags or []
        }
        
        # Update or add to index
        existing_idx = next(
            (i for i, p in enumerate(self.index["patterns"]) if p["name"] == name),
            None
        )
        if existing_idx is not None:
            self.index["patterns"][existing_idx] = pattern_entry
        else:
            self.index["patterns"].append(pattern_entry)
        
        self._save_index()
        
        return str(filepath)
    
    def save_context(
        self,
        agent_id: str,
        task: str,
        current_work: str,
        status: str = "in_progress",
        notes: str = ""
    ) -> str:
        """
        Save current work context.
        
        Args:
            agent_id: Agent identifier
            task: Task ID or name
            current_work: Description of current work
            status: in_progress, completed, blocked
            notes: Additional notes
        
        Returns:
            File path of saved context
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        filename = f"{agent_id}-{task}-{date_str}.md"
        filepath = self.context_path / filename
        
        context_content = f"""# Context: {task}

**Agent**: {agent_id}
**Date**: {date_str}
**Status**: {status}

## Current Work

{current_work}

"""
        
        if notes:
            context_content += f"## Notes\n\n{notes}\n\n"
        
        context_content += f"---\n\n**Last Updated**: {timestamp.isoformat()}\n"
        
        with open(filepath, 'w') as f:
            f.write(context_content)
        
        # Update index
        context_entry = {
            "file": str(filepath.relative_to(self.base_path)),
            "agent_id": agent_id,
            "task": task,
            "status": status,
            "date": date_str
        }
        
        # Update or add to index
        existing_idx = next(
            (i for i, c in enumerate(self.index["contexts"]) 
             if c["agent_id"] == agent_id and c["task"] == task),
            None
        )
        if existing_idx is not None:
            self.index["contexts"][existing_idx] = context_entry
        else:
            self.index["contexts"].append(context_entry)
        
        self._save_index()
        
        return str(filepath)
    
    def query_decisions(
        self,
        project: Optional[str] = None,
        task: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query decisions.
        
        Args:
            project: Filter by project
            task: Filter by task
            tags: Filter by tags
            min_importance: Minimum importance score
            limit: Maximum results
        
        Returns:
            List of decision entries
        """
        results = self.index["decisions"].copy()
        
        if project:
            results = [d for d in results if d.get("project") == project]
        
        if task:
            results = [d for d in results if task.lower() in d.get("task", "").lower()]
        
        if tags:
            results = [d for d in results if any(tag in d.get("tags", []) for tag in tags)]
        
        results = [d for d in results if d.get("importance", 0) >= min_importance]
        
        # Sort by date (newest first)
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return results[:limit]
    
    def query_patterns(
        self,
        severity: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_frequency: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Query patterns.
        
        Args:
            severity: Filter by severity
            tags: Filter by tags
            min_frequency: Minimum frequency
        
        Returns:
            List of pattern entries
        """
        results = self.index["patterns"].copy()
        
        if severity:
            results = [p for p in results if p.get("severity") == severity]
        
        if tags:
            results = [p for p in results if any(tag in p.get("tags", []) for tag in tags)]
        
        results = [p for p in results if p.get("frequency", 0) >= min_frequency]
        
        # Sort by frequency (highest first)
        results.sort(key=lambda x: x.get("frequency", 0), reverse=True)
        
        return results
    
    def get_recent_context(
        self,
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent context.
        
        Args:
            agent_id: Filter by agent
            limit: Maximum results
        
        Returns:
            List of context entries
        """
        results = self.index["contexts"].copy()
        
        if agent_id:
            results = [c for c in results if c.get("agent_id") == agent_id]
        
        # Sort by date (newest first)
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return results[:limit]


# Global instance
_memory_instance: Optional[FileBasedMemory] = None


def get_memory() -> FileBasedMemory:
    """Get global memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = FileBasedMemory()
    return _memory_instance

