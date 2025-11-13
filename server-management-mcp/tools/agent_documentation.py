"""
Agent Documentation Tools for MCP Server

Provides tools for agents to create and manage their own namespaced documentation.
This ensures all agent-specific files are organized in the agent's directory and
can be properly archived when the agent lifecycle completes.
"""

import sys
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


def _get_agent_docs_dir(agent_id: str) -> Path:
    """Get agent documentation directory."""
    agent_dir = ACTIVE_DIR / agent_id
    docs_dir = agent_dir / "docs"
    return docs_dir


def _get_doc_path(agent_id: str, doc_type: str, doc_name: str) -> Path:
    """Get path to a documentation file."""
    docs_dir = _get_agent_docs_dir(agent_id)
    type_dir = docs_dir / doc_type
    type_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure .md extension
    if not doc_name.endswith(".md"):
        doc_name = f"{doc_name}.md"
    
    return type_dir / doc_name


def _ensure_agent_dir(agent_id: str) -> Path:
    """Ensure agent directory exists."""
    agent_dir = ACTIVE_DIR / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir


def register_agent_documentation_tools(server: Server):
    """Register agent documentation tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def create_agent_doc(
        agent_id: str,
        doc_type: str,
        doc_name: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Create agent-specific documentation in the agent's namespaced directory.
        
        This ensures all agent documentation is organized and can be properly
        archived when the agent lifecycle completes.
        
        Args:
            agent_id: Your agent ID
            doc_type: Type of documentation ("plan", "note", "architecture", "reference")
            doc_name: Name of the document (without .md extension)
            content: Document content (markdown)
        
        Returns:
            Path to created document
        
        Example:
            create_agent_doc(
                agent_id="agent-001",
                doc_type="plan",
                doc_name="feature-x-implementation",
                content="# Implementation Plan\n\n..."
            )
        """
        # Validate doc_type
        valid_types = ["plan", "note", "architecture", "reference"]
        if doc_type not in valid_types:
            return {
                "status": "error",
                "message": f"Invalid doc_type. Must be one of: {', '.join(valid_types)}"
            }
        
        # Ensure agent directory exists
        _ensure_agent_dir(agent_id)
        
        # Get document path
        doc_path = _get_doc_path(agent_id, doc_type, doc_name)
        
        # Add frontmatter
        frontmatter = f"""---
agent_id: {agent_id}
doc_type: {doc_type}
doc_name: {doc_name}
created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
---

"""
        
        full_content = frontmatter + content
        
        # Write document
        doc_path.write_text(full_content, encoding="utf-8")
        
        return {
            "status": "success",
            "message": f"Document created: {doc_type}/{doc_name}",
            "path": str(doc_path.relative_to(project_root)),
            "agent_id": agent_id,
            "doc_type": doc_type,
            "doc_name": doc_name
        }
    
    @server.tool()
    @with_automatic_logging()
    async def list_agent_docs(
        agent_id: str,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all documentation for an agent.
        
        Args:
            agent_id: Your agent ID
            doc_type: Optional filter by type ("plan", "note", "architecture", "reference")
        
        Returns:
            List of documentation files
        
        Example:
            list_agent_docs(agent_id="agent-001", doc_type="plan")
        """
        docs_dir = _get_agent_docs_dir(agent_id)
        
        if not docs_dir.exists():
            return {
                "status": "success",
                "message": "No documentation found",
                "docs": [],
                "agent_id": agent_id
            }
        
        docs = []
        
        # If doc_type specified, only list that type
        if doc_type:
            type_dir = docs_dir / doc_type
            if type_dir.exists():
                for doc_file in type_dir.glob("*.md"):
                    stat = doc_file.stat()
                    docs.append({
                        "doc_type": doc_type,
                        "doc_name": doc_file.stem,
                        "path": str(doc_file.relative_to(project_root)),
                        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": stat.st_size
                    })
        else:
            # List all types
            for type_dir in docs_dir.iterdir():
                if not type_dir.is_dir():
                    continue
                
                for doc_file in type_dir.glob("*.md"):
                    stat = doc_file.stat()
                    docs.append({
                        "doc_type": type_dir.name,
                        "doc_name": doc_file.stem,
                        "path": str(doc_file.relative_to(project_root)),
                        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": stat.st_size
                    })
        
        # Sort by created date (newest first)
        docs.sort(key=lambda x: x["created"], reverse=True)
        
        return {
            "status": "success",
            "message": f"Found {len(docs)} document(s)",
            "docs": docs,
            "agent_id": agent_id,
            "filtered_by": doc_type if doc_type else "all"
        }
    
    @server.tool()
    @with_automatic_logging()
    async def read_agent_doc(
        agent_id: str,
        doc_type: str,
        doc_name: str
    ) -> Dict[str, Any]:
        """
        Read agent documentation.
        
        Args:
            agent_id: Your agent ID
            doc_type: Type of documentation ("plan", "note", "architecture", "reference")
            doc_name: Name of the document (without .md extension)
        
        Returns:
            Document content
        
        Example:
            read_agent_doc(
                agent_id="agent-001",
                doc_type="plan",
                doc_name="feature-x-implementation"
            )
        """
        doc_path = _get_doc_path(agent_id, doc_type, doc_name)
        
        if not doc_path.exists():
            return {
                "status": "error",
                "message": f"Document not found: {doc_type}/{doc_name}",
                "path": str(doc_path.relative_to(project_root))
            }
        
        content = doc_path.read_text(encoding="utf-8")
        
        return {
            "status": "success",
            "content": content,
            "path": str(doc_path.relative_to(project_root)),
            "agent_id": agent_id,
            "doc_type": doc_type,
            "doc_name": doc_name
        }
    
    @server.tool()
    @with_automatic_logging()
    async def update_agent_doc(
        agent_id: str,
        doc_type: str,
        doc_name: str,
        content: str,
        append: bool = False
    ) -> Dict[str, Any]:
        """
        Update agent documentation.
        
        Args:
            agent_id: Your agent ID
            doc_type: Type of documentation
            doc_name: Name of the document
            content: New content (or content to append)
            append: If True, append to existing content; if False, replace
        
        Returns:
            Updated document path
        
        Example:
            update_agent_doc(
                agent_id="agent-001",
                doc_type="note",
                doc_name="research-notes",
                content="\n\n## New Finding\n\n...",
                append=True
            )
        """
        doc_path = _get_doc_path(agent_id, doc_type, doc_name)
        
        if not doc_path.exists():
            return {
                "status": "error",
                "message": f"Document not found: {doc_type}/{doc_name}. Use create_agent_doc() to create it first."
            }
        
        if append:
            # Read existing content
            existing = doc_path.read_text(encoding="utf-8")
            # Append new content
            updated = existing + "\n\n" + content
        else:
            # Replace content (preserve frontmatter if present)
            existing = doc_path.read_text(encoding="utf-8")
            if existing.startswith("---"):
                # Extract frontmatter
                parts = existing.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = f"---{parts[1]}---\n\n"
                    updated = frontmatter + content
                else:
                    updated = content
            else:
                updated = content
        
        # Update timestamp in frontmatter if present
        if updated.startswith("---"):
            parts = updated.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                # Update or add updated timestamp
                if "updated:" in frontmatter:
                    updated = updated.replace(
                        "updated:",
                        f"updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    # Add updated timestamp
                    frontmatter += f"\nupdated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    updated = f"---{frontmatter}---\n\n{parts[2]}"
        
        doc_path.write_text(updated, encoding="utf-8")
        
        return {
            "status": "success",
            "message": f"Document updated: {doc_type}/{doc_name}",
            "path": str(doc_path.relative_to(project_root)),
            "agent_id": agent_id,
            "doc_type": doc_type,
            "doc_name": doc_name
        }
    
    @server.tool()
    @with_automatic_logging()
    async def get_agent_doc_structure(agent_id: str) -> Dict[str, Any]:
        """
        Get the documentation directory structure for an agent.
        
        Shows what documentation exists and the directory structure.
        
        Args:
            agent_id: Your agent ID
        
        Returns:
            Directory structure and documentation summary
        
        Example:
            get_agent_doc_structure(agent_id="agent-001")
        """
        agent_dir = ACTIVE_DIR / agent_id
        docs_dir = _get_agent_docs_dir(agent_id)
        
        structure = {
            "agent_id": agent_id,
            "agent_dir": str(agent_dir.relative_to(project_root)),
            "docs_dir": str(docs_dir.relative_to(project_root)) if docs_dir.exists() else None,
            "exists": agent_dir.exists(),
            "doc_types": {}
        }
        
        if not docs_dir.exists():
            return {
                "status": "success",
                "message": "No documentation directory found",
                **structure
            }
        
        # Count documents by type
        for type_dir in docs_dir.iterdir():
            if not type_dir.is_dir():
                continue
            
            doc_files = list(type_dir.glob("*.md"))
            structure["doc_types"][type_dir.name] = {
                "count": len(doc_files),
                "files": [f.stem for f in doc_files]
            }
        
        return {
            "status": "success",
            "message": f"Documentation structure for {agent_id}",
            **structure
        }

