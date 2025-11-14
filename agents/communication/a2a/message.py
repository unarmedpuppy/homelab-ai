"""
A2A Message Format

Implements JSON-RPC 2.0 format for A2A protocol compliance.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class A2AMessageType(str, Enum):
    """A2A message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ESCALATION = "escalation"


class A2APriority(str, Enum):
    """A2A priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class A2AStatus(str, Enum):
    """A2A message status."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class A2AError:
    """A2A error object (JSON-RPC 2.0 format)."""
    
    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AError":
        """Create from dictionary."""
        return cls(
            code=data.get("code", -32000),
            message=data.get("message", "Unknown error"),
            data=data.get("data")
        )


class A2ARequest:
    """A2A JSON-RPC 2.0 request."""
    
    def __init__(
        self,
        method: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ):
        self.jsonrpc = "2.0"
        self.id = request_id or self._generate_id()
        self.method = method
        self.params = params
    
    def _generate_id(self) -> str:
        """Generate unique request ID."""
        return f"req-{datetime.now().isoformat()}-{id(self)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON-RPC 2.0 format)."""
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": self.params
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2ARequest":
        """Create from dictionary."""
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
            request_id=data.get("id")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "A2ARequest":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class A2AResponse:
    """A2A JSON-RPC 2.0 response."""
    
    def __init__(
        self,
        request_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[A2AError] = None
    ):
        self.jsonrpc = "2.0"
        self.id = request_id
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON-RPC 2.0 format)."""
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
        return response
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def success(cls, request_id: str, result: Dict[str, Any]) -> "A2AResponse":
        """Create success response."""
        return cls(request_id=request_id, result=result)
    
    @classmethod
    def error(
        cls,
        request_id: str,
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> "A2AResponse":
        """Create error response."""
        return cls(
            request_id=request_id,
            error=A2AError(code=code, message=message, data=data)
        )


class A2AMessage:
    """A2A message wrapper (combines request/response with message data)."""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: A2AMessageType,
        priority: A2APriority,
        subject: str,
        content: str,
        message_id: Optional[str] = None,
        status: A2AStatus = A2AStatus.PENDING,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message_id = message_id or self._generate_message_id()
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.type = message_type
        self.priority = priority
        self.subject = subject
        self.content = content
        self.status = status
        self.created_at = datetime.now().isoformat() + "Z"
        self.acknowledged_at: Optional[str] = None
        self.resolved_at: Optional[str] = None
        self.metadata = metadata or {}
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        # Simple ID generation (can be enhanced)
        return f"MSG-{date_str}-{id(self)}"
    
    def to_a2a_request(self, method: str = "a2a.sendMessage") -> A2ARequest:
        """Convert to A2A JSON-RPC 2.0 request."""
        params = {
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.type.value,
            "priority": self.priority.value,
            "subject": self.subject,
            "content": self.content,
            "metadata": {
                **self.metadata,
                "message_id": self.message_id,
                "status": self.status.value,
                "created_at": self.created_at
            }
        }
        return A2ARequest(method=method, params=params, request_id=self.message_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "type": self.type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "subject": self.subject,
            "content": self.content,
            "created_at": self.created_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create from dictionary."""
        msg = cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            message_type=A2AMessageType(data["type"]),
            priority=A2APriority(data["priority"]),
            subject=data["subject"],
            content=data["content"],
            message_id=data.get("message_id"),
            status=A2AStatus(data.get("status", "pending"))
        )
        msg.created_at = data.get("created_at", msg.created_at)
        msg.acknowledged_at = data.get("acknowledged_at")
        msg.resolved_at = data.get("resolved_at")
        msg.metadata = data.get("metadata", {})
        return msg
    
    @classmethod
    def from_a2a_request(cls, request: A2ARequest) -> "A2AMessage":
        """Create from A2A JSON-RPC 2.0 request."""
        params = request.params
        metadata = params.get("metadata", {})
        
        return cls(
            from_agent=params["from"],
            to_agent=params["to"],
            message_type=A2AMessageType(params["type"]),
            priority=A2APriority(params["priority"]),
            subject=params["subject"],
            content=params["content"],
            message_id=metadata.get("message_id"),
            status=A2AStatus(metadata.get("status", "pending")),
            metadata={k: v for k, v in metadata.items() if k not in ["message_id", "status", "created_at"]}
        )

