"""
Agent Communication Tools for MCP Server

Provides tools for agents to send, receive, and manage messages with each other.
"""
import sys
import json
import uuid
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server


# Paths for communication
COMMUNICATION_DIR = project_root / "agents" / "communication"
MESSAGES_DIR = COMMUNICATION_DIR / "messages"
INDEX_PATH = MESSAGES_DIR / "index.json"


def _ensure_communication_dir():
    """Ensure communication directory structure exists."""
    COMMUNICATION_DIR.mkdir(parents=True, exist_ok=True)
    MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create index.json if it doesn't exist
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(json.dumps({"messages": []}, indent=2))


def _load_index() -> Dict[str, Any]:
    """Load message index."""
    _ensure_communication_dir()
    if not INDEX_PATH.exists():
        return {"messages": []}
    return json.loads(INDEX_PATH.read_text())


def _save_index(index: Dict[str, Any]):
    """Save message index."""
    _ensure_communication_dir()
    INDEX_PATH.write_text(json.dumps(index, indent=2))


def _generate_message_id() -> str:
    """Generate unique message ID."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Get existing messages for today
    index = _load_index()
    today_messages = [
        m for m in index.get("messages", [])
        if m.get("message_id", "").startswith(f"MSG-{date_str}")
    ]
    
    # Get next number
    next_num = len(today_messages) + 1
    return f"MSG-{date_str}-{next_num:03d}"


def _get_message_file(message_id: str) -> Path:
    """Get path to message file."""
    return MESSAGES_DIR / f"{message_id}.md"


def _parse_message_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse a message markdown file and return metadata and content."""
    if not file_path.exists():
        return None
    
    content = file_path.read_text()
    
    # Split frontmatter and body
    if not content.startswith("---"):
        return None
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    
    # Parse YAML frontmatter
    try:
        metadata = yaml.safe_load(parts[1])
        body = parts[2].strip()
        
        return {
            **metadata,
            "content": body,
            "file": str(file_path.relative_to(project_root))
        }
    except Exception:
        return None


def register_communication_tools(server: Server):
    """Register communication tools with MCP server."""
    
    @server.tool()
    async def send_agent_message(
        from_agent: str,
        to_agent: str,
        type: str,
        priority: str,
        subject: str,
        content: str,
        related_task_id: Optional[str] = None,
        related_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to another agent.
        
        Args:
            from_agent: Agent ID sending the message
            to_agent: Agent ID receiving (or "all" for broadcast)
            type: Message type (request, response, notification, escalation)
            priority: Priority level (low, medium, high, urgent)
            subject: Brief subject line
            content: Message content (markdown supported)
            related_task_id: Related task ID (optional)
            related_message_id: Original message ID for responses (optional)
            
        Returns:
            Message ID and status
        """
        try:
            _ensure_communication_dir()
            
            # Validate inputs
            valid_types = ["request", "response", "notification", "escalation"]
            if type not in valid_types:
                return {
                    "status": "error",
                    "message": f"Invalid type. Must be one of: {', '.join(valid_types)}"
                }
            
            valid_priorities = ["low", "medium", "high", "urgent"]
            if priority not in valid_priorities:
                return {
                    "status": "error",
                    "message": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
                }
            
            # Generate message ID
            message_id = _generate_message_id()
            
            # Create message file
            message_file = _get_message_file(message_id)
            
            # Create YAML frontmatter
            frontmatter = {
                "message_id": message_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "type": type,
                "priority": priority,
                "status": "pending",
                "subject": subject,
                "created_at": datetime.now().isoformat() + "Z",
                "acknowledged_at": None,
                "resolved_at": None
            }
            
            if related_task_id:
                frontmatter["related_task_id"] = related_task_id
            if related_message_id:
                frontmatter["related_message_id"] = related_message_id
            
            # Write message file
            message_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n# {subject}\n\n{content}\n"
            message_file.write_text(message_content)
            
            # Update index
            index = _load_index()
            index["messages"].append({
                "message_id": message_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "type": type,
                "priority": priority,
                "status": "pending",
                "created_at": frontmatter["created_at"],
                "file": str(message_file.relative_to(project_root))
            })
            _save_index(index)
            
            return {
                "status": "success",
                "message_id": message_id,
                "message": f"Message sent successfully to {to_agent}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def get_agent_messages(
        agent_id: str,
        status: Optional[str] = None,
        type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: Agent ID to get messages for (or "all" for all messages)
            status: Filter by status (pending, acknowledged, in_progress, resolved, escalated)
            type: Filter by type (request, response, notification, escalation)
            priority: Filter by priority (low, medium, high, urgent)
            limit: Maximum number of messages to return
            
        Returns:
            List of messages matching filters
        """
        try:
            _ensure_communication_dir()
            
            index = _load_index()
            messages = []
            
            # Filter messages
            for msg_entry in index.get("messages", []):
                # Check if message is for this agent
                if agent_id != "all" and msg_entry.get("to_agent") != agent_id:
                    # Also check if agent sent the message (for responses)
                    if msg_entry.get("from_agent") != agent_id:
                        continue
                
                # Apply filters
                if status and msg_entry.get("status") != status:
                    continue
                if type and msg_entry.get("type") != type:
                    continue
                if priority and msg_entry.get("priority") != priority:
                    continue
                
                # Load full message
                message_file = project_root / msg_entry.get("file", "")
                if message_file.exists():
                    full_message = _parse_message_file(message_file)
                    if full_message:
                        messages.append(full_message)
            
            # Sort by created_at (newest first)
            messages.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply limit
            messages = messages[:limit]
            
            return {
                "status": "success",
                "count": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def acknowledge_message(
        message_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Acknowledge receipt of a message.
        
        Args:
            message_id: Message ID to acknowledge
            agent_id: Agent ID acknowledging the message
            
        Returns:
            Status of acknowledgment
        """
        try:
            message_file = _get_message_file(message_id)
            if not message_file.exists():
                return {
                    "status": "error",
                    "message": f"Message {message_id} not found"
                }
            
            # Parse message
            message = _parse_message_file(message_file)
            if not message:
                return {
                    "status": "error",
                    "message": "Failed to parse message file"
                }
            
            # Verify agent is recipient
            if message.get("to_agent") != agent_id and message.get("to_agent") != "all":
                return {
                    "status": "error",
                    "message": "Agent is not the recipient of this message"
                }
            
            # Update message
            import yaml
            content = message_file.read_text()
            parts = content.split("---", 2)
            
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                metadata["status"] = "acknowledged"
                metadata["acknowledged_at"] = datetime.now().isoformat() + "Z"
                
                # Rewrite file
                new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{parts[2]}"
                message_file.write_text(new_content)
                
                # Update index
                index = _load_index()
                for msg in index.get("messages", []):
                    if msg.get("message_id") == message_id:
                        msg["status"] = "acknowledged"
                        msg["acknowledged_at"] = metadata["acknowledged_at"]
                        break
                _save_index(index)
            
            return {
                "status": "success",
                "message": f"Message {message_id} acknowledged"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def mark_message_resolved(
        message_id: str,
        agent_id: str,
        resolution_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a message as resolved.
        
        Args:
            message_id: Message ID to resolve
            agent_id: Agent ID resolving the message
            resolution_note: Optional note about resolution
            
        Returns:
            Status of resolution
        """
        try:
            message_file = _get_message_file(message_id)
            if not message_file.exists():
                return {
                    "status": "error",
                    "message": f"Message {message_id} not found"
                }
            
            # Parse message
            message = _parse_message_file(message_file)
            if not message:
                return {
                    "status": "error",
                    "message": "Failed to parse message file"
                }
            
            # Verify agent is recipient or sender
            if (message.get("to_agent") != agent_id and 
                message.get("from_agent") != agent_id and
                message.get("to_agent") != "all"):
                return {
                    "status": "error",
                    "message": "Agent is not authorized to resolve this message"
                }
            
            # Update message
            content = message_file.read_text()
            parts = content.split("---", 2)
            
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                metadata["status"] = "resolved"
                metadata["resolved_at"] = datetime.now().isoformat() + "Z"
                
                # Add resolution note if provided
                if resolution_note:
                    body = parts[2]
                    body += f"\n\n## Resolution\n\n{resolution_note}\n"
                    parts[2] = body
                
                # Rewrite file
                new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{parts[2]}"
                message_file.write_text(new_content)
                
                # Update index
                index = _load_index()
                for msg in index.get("messages", []):
                    if msg.get("message_id") == message_id:
                        msg["status"] = "resolved"
                        msg["resolved_at"] = metadata["resolved_at"]
                        break
                _save_index(index)
            
            return {
                "status": "success",
                "message": f"Message {message_id} marked as resolved"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def query_messages(
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        related_task_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Query messages with multiple filters.
        
        Args:
            from_agent: Filter by sender agent ID
            to_agent: Filter by recipient agent ID
            type: Filter by type (request, response, notification, escalation)
            priority: Filter by priority (low, medium, high, urgent)
            status: Filter by status (pending, acknowledged, in_progress, resolved, escalated)
            related_task_id: Filter by related task ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages matching all filters
        """
        try:
            _ensure_communication_dir()
            
            index = _load_index()
            messages = []
            
            # Filter messages
            for msg_entry in index.get("messages", []):
                # Apply all filters
                if from_agent and msg_entry.get("from_agent") != from_agent:
                    continue
                if to_agent and msg_entry.get("to_agent") != to_agent:
                    continue
                if type and msg_entry.get("type") != type:
                    continue
                if priority and msg_entry.get("priority") != priority:
                    continue
                if status and msg_entry.get("status") != status:
                    continue
                
                # Load full message for task_id check
                message_file = project_root / msg_entry.get("file", "")
                if message_file.exists():
                    full_message = _parse_message_file(message_file)
                    if full_message:
                        # Check task_id if filter provided
                        if related_task_id:
                            if full_message.get("related_task_id") != related_task_id:
                                continue
                        
                        messages.append(full_message)
            
            # Sort by created_at (newest first)
            messages.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply limit
            messages = messages[:limit]
            
            return {
                "status": "success",
                "count": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

