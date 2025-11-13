"""
Agent Memory Integration - SQLite + File-Based Hybrid

Uses SQLite for fast queries and structured storage, with optional
markdown export for human readability. Agents can query via helper
functions or read exported markdown files.
"""

from .sqlite_memory import get_sqlite_memory, SQLiteMemory
from .file_based_memory import get_memory, FileBasedMemory

# Default to SQLite (faster, better for agents)
get_memory = get_sqlite_memory

__all__ = ["get_memory", "get_sqlite_memory", "SQLiteMemory", "FileBasedMemory"]

