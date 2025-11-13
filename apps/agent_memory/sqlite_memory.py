"""
SQLite-Based Memory System for Agents

Uses SQLite for fast queries and structured storage, with optional
markdown export for human readability.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import os


class SQLiteMemory:
    """
    SQLite-based memory system with full-text search.
    
    Provides fast queries, relationships, and full-text search while
    maintaining the ability to export to markdown for human readability.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQLite memory system.
        
        Args:
            db_path: Path to SQLite database (defaults to apps/agent_memory/memory.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent / "memory.db"
        self.db_path = Path(db_path)
        
        # Create database and tables
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                rationale TEXT,
                project TEXT,
                task TEXT,
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                solution TEXT,
                severity TEXT DEFAULT 'medium',
                frequency INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                task TEXT,
                current_work TEXT,
                status TEXT DEFAULT 'in_progress',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_tags (
                decision_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (decision_id, tag_id),
                FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_tags (
                pattern_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (pattern_id, tag_id),
                FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        # Full-text search tables
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
                content, rationale, project, task,
                content_rowid=id,
                tokenize='porter'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(
                name, description, solution,
                content_rowid=id,
                tokenize='porter'
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_task ON decisions(task)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_importance ON decisions(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_severity ON patterns(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_agent ON context(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_task ON context(task)")
        
        conn.commit()
        conn.close()
    
    def _get_tags(self, tag_names: List[str], conn: Optional[sqlite3.Connection] = None) -> List[int]:
        """Get or create tag IDs."""
        if not tag_names:
            return []
        
        close_conn = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
        
        cursor = conn.cursor()
        
        tag_ids = []
        for tag_name in tag_names:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_ids.append(cursor.fetchone()[0])
        
        if close_conn:
            conn.commit()
            conn.close()
        
        return tag_ids
    
    def record_decision(
        self,
        content: str,
        rationale: str = "",
        project: str = "home-server",
        task: str = "",
        importance: float = 0.5,
        tags: List[str] = None
    ) -> int:
        """
        Record a decision.
        
        Returns:
            Decision ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decisions (content, rationale, project, task, importance)
            VALUES (?, ?, ?, ?, ?)
        """, (content, rationale, project, task, importance))
        
        decision_id = cursor.lastrowid
        
        # Add to full-text search
        cursor.execute("""
            INSERT INTO decisions_fts (rowid, content, rationale, project, task)
            VALUES (?, ?, ?, ?, ?)
        """, (decision_id, content, rationale, project, task))
        
        # Add tags
        if tags:
            tag_ids = self._get_tags(tags, conn)
            for tag_id in tag_ids:
                cursor.execute("""
                    INSERT INTO decision_tags (decision_id, tag_id)
                    VALUES (?, ?)
                """, (decision_id, tag_id))
        
        conn.commit()
        conn.close()
        
        return decision_id
    
    def record_pattern(
        self,
        name: str,
        description: str,
        solution: str = "",
        severity: str = "medium",
        frequency: int = 1,
        tags: List[str] = None
    ) -> int:
        """
        Record or update a pattern.
        
        Returns:
            Pattern ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute("SELECT id, frequency FROM patterns WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing pattern
            pattern_id, old_frequency = existing
            new_frequency = old_frequency + frequency
            
            cursor.execute("""
                UPDATE patterns 
                SET description = ?, solution = ?, severity = ?, frequency = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (description, solution, severity, new_frequency, pattern_id))
            
            # Update full-text search
            cursor.execute("""
                UPDATE patterns_fts 
                SET name = ?, description = ?, solution = ?
                WHERE rowid = ?
            """, (name, description, solution, pattern_id))
        else:
            # Create new pattern
            cursor.execute("""
                INSERT INTO patterns (name, description, solution, severity, frequency)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, solution, severity, frequency))
            
            pattern_id = cursor.lastrowid
            
            # Add to full-text search
            cursor.execute("""
                INSERT INTO patterns_fts (rowid, name, description, solution)
                VALUES (?, ?, ?, ?)
            """, (pattern_id, name, description, solution))
        
        # Update tags
        if tags:
            # Remove old tags
            cursor.execute("DELETE FROM pattern_tags WHERE pattern_id = ?", (pattern_id,))
            # Add new tags
            tag_ids = self._get_tags(tags, conn)
            for tag_id in tag_ids:
                cursor.execute("""
                    INSERT INTO pattern_tags (pattern_id, tag_id)
                    VALUES (?, ?)
                """, (pattern_id, tag_id))
        
        conn.commit()
        conn.close()
        
        return pattern_id
    
    def save_context(
        self,
        agent_id: str,
        task: str,
        current_work: str,
        status: str = "in_progress",
        notes: str = ""
    ) -> int:
        """
        Save or update context.
        
        Returns:
            Context ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if context exists
        cursor.execute("""
            SELECT id FROM context 
            WHERE agent_id = ? AND task = ?
        """, (agent_id, task))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing context
            context_id = existing[0]
            cursor.execute("""
                UPDATE context 
                SET current_work = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (current_work, status, notes, context_id))
        else:
            # Create new context
            cursor.execute("""
                INSERT INTO context (agent_id, task, current_work, status, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, task, current_work, status, notes))
            context_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return context_id
    
    def query_decisions(
        self,
        project: Optional[str] = None,
        task: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query decisions with fast SQLite queries.
        
        Args:
            project: Filter by project
            task: Filter by task
            tags: Filter by tags
            min_importance: Minimum importance score
            search_text: Full-text search
            limit: Maximum results
        
        Returns:
            List of decision dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT d.* FROM decisions d"
        conditions = []
        params = []
        
        if search_text:
            # Use full-text search
            query = """
                SELECT d.* FROM decisions d
                JOIN decisions_fts fts ON d.id = fts.rowid
                WHERE decisions_fts MATCH ?
            """
            conditions.append("decisions_fts MATCH ?")
            params.append(search_text)
        else:
            if project:
                conditions.append("d.project = ?")
                params.append(project)
            
            if task:
                conditions.append("d.task LIKE ?")
                params.append(f"%{task}%")
            
            if min_importance > 0:
                conditions.append("d.importance >= ?")
                params.append(min_importance)
        
        if tags:
            query += """
                JOIN decision_tags dt ON d.id = dt.decision_id
                JOIN tags t ON dt.tag_id = t.id
            """
            conditions.append("t.name IN ({})".format(','.join('?' * len(tags))))
            params.extend(tags)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY d.importance DESC, d.created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        results = []
        for row in rows:
            result = dict(row)
            # Get tags
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN decision_tags dt ON t.id = dt.tag_id
                WHERE dt.decision_id = ?
            """, (result['id'],))
            result['tags'] = [tag[0] for tag in cursor.fetchall()]
            results.append(result)
        
        conn.close()
        return results
    
    def query_patterns(
        self,
        severity: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_frequency: int = 1,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query patterns with fast SQLite queries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT p.* FROM patterns p"
        conditions = []
        params = []
        
        if search_text:
            query = """
                SELECT p.* FROM patterns p
                JOIN patterns_fts fts ON p.id = fts.rowid
                WHERE patterns_fts MATCH ?
            """
            conditions.append("patterns_fts MATCH ?")
            params.append(search_text)
        else:
            if severity:
                conditions.append("p.severity = ?")
                params.append(severity)
            
            if min_frequency > 1:
                conditions.append("p.frequency >= ?")
                params.append(min_frequency)
        
        if tags:
            query += """
                JOIN pattern_tags pt ON p.id = pt.pattern_id
                JOIN tags t ON pt.tag_id = t.id
            """
            conditions.append("t.name IN ({})".format(','.join('?' * len(tags))))
            params.extend(tags)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY p.frequency DESC, p.updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            result = dict(row)
            # Get tags
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN pattern_tags pt ON t.id = pt.pattern_id
                WHERE pt.pattern_id = ?
            """, (result['id'],))
            result['tags'] = [tag[0] for tag in cursor.fetchall()]
            results.append(result)
        
        conn.close()
        return results
    
    def search(self, query_text: str, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        Full-text search across all memories.
        
        Returns:
            Dictionary with 'decisions' and 'patterns' lists
        """
        decisions = self.query_decisions(search_text=query_text, limit=limit)
        patterns = self.query_patterns(search_text=query_text, limit=limit)
        
        return {
            "decisions": decisions,
            "patterns": patterns,
            "query": query_text,
            "total": len(decisions) + len(patterns)
        }
    
    def export_to_markdown(self, output_path: Optional[Path] = None) -> Path:
        """
        Export all memories to markdown files for human readability.
        
        Args:
            output_path: Directory to export to (defaults to apps/agent_memory/memory/)
        
        Returns:
            Path to export directory
        """
        if output_path is None:
            output_path = Path(__file__).parent / "memory" / "export"
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        decisions_path = output_path / "decisions"
        patterns_path = output_path / "patterns"
        decisions_path.mkdir(exist_ok=True)
        patterns_path.mkdir(exist_ok=True)
        
        # Export decisions
        decisions = self.query_decisions(limit=1000)
        for decision in decisions:
            date_str = decision['created_at'][:10] if decision['created_at'] else datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}-{decision['id']}-{decision['content'][:50].replace(' ', '-').lower()}.md"
            filepath = decisions_path / filename
            
            content = f"""# Decision: {decision['content']}

**Date**: {decision['created_at']}
**Project**: {decision['project']}
**Task**: {decision['task']}
**Importance**: {decision['importance']}

## Decision

{decision['content']}

## Rationale

{decision['rationale'] or 'N/A'}

## Tags

{chr(10).join(f'- {tag}' for tag in decision.get('tags', []))}

---
"""
            filepath.write_text(content)
        
        # Export patterns
        patterns = self.query_patterns(limit=1000)
        for pattern in patterns:
            filename = f"{pattern['name'].replace(' ', '-').lower()}.md"
            filepath = patterns_path / filename
            
            content = f"""# Pattern: {pattern['name']}

**Severity**: {pattern['severity']}
**Frequency**: {pattern['frequency']}
**Last Updated**: {pattern['updated_at']}

## Description

{pattern['description'] or 'N/A'}

## Solution

{pattern['solution'] or 'N/A'}

## Tags

{chr(10).join(f'- {tag}' for tag in pattern.get('tags', []))}

---
"""
            filepath.write_text(content)
        
        return output_path


# Global instance
_sqlite_memory_instance: Optional[SQLiteMemory] = None


def get_sqlite_memory() -> SQLiteMemory:
    """Get global SQLite memory instance."""
    global _sqlite_memory_instance
    if _sqlite_memory_instance is None:
        _sqlite_memory_instance = SQLiteMemory()
    return _sqlite_memory_instance

