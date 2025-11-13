"""
Agent Memory Integration - File-Based System

Since agents run in Cursor/Claude Desktop, we use file-based memory
that agents can read/write directly as markdown files.
"""

from .file_based_memory import get_memory, FileBasedMemory

__all__ = ["get_memory", "FileBasedMemory"]

