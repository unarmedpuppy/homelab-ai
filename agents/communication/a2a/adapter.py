"""
A2A Protocol Adapter

Converts between custom message format and A2A protocol format.
"""
from typing import Dict, Any, Optional
from .message import A2AMessage, A2ARequest, A2AResponse, A2AMessageType, A2APriority, A2AStatus


def to_a2a_format(custom_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert custom message format to A2A format.
    
    Args:
        custom_message: Custom message dictionary
    
    Returns:
        A2A JSON-RPC 2.0 request dictionary
    """
    # Create A2A message
    a2a_msg = A2AMessage(
        from_agent=custom_message["from_agent"],
        to_agent=custom_message["to_agent"],
        message_type=A2AMessageType(custom_message["type"]),
        priority=A2APriority(custom_message["priority"]),
        subject=custom_message["subject"],
        content=custom_message.get("content", ""),
        message_id=custom_message.get("message_id"),
        status=A2AStatus(custom_message.get("status", "pending")),
        metadata={
            "related_task_id": custom_message.get("related_task_id"),
            "related_message_id": custom_message.get("related_message_id")
        }
    )
    
    # Convert to A2A request
    a2a_request = a2a_msg.to_a2a_request()
    return a2a_request.to_dict()


def from_a2a_format(a2a_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert A2A format to custom message format.
    
    Args:
        a2a_message: A2A JSON-RPC 2.0 request/response dictionary
    
    Returns:
        Custom message dictionary
    """
    # Handle JSON-RPC 2.0 request
    if "method" in a2a_message and "params" in a2a_message:
        request = A2ARequest.from_dict(a2a_message)
        a2a_msg = A2AMessage.from_a2a_request(request)
        
        # Convert to custom format
        custom = a2a_msg.to_dict()
        
        # Extract metadata
        metadata = a2a_msg.metadata
        custom["related_task_id"] = metadata.get("related_task_id")
        custom["related_message_id"] = metadata.get("related_message_id")
        
        return custom
    
    # Handle JSON-RPC 2.0 response
    elif "result" in a2a_message:
        return {
            "status": "success",
            "result": a2a_message["result"]
        }
    
    # Handle error response
    elif "error" in a2a_message:
        error = a2a_message["error"]
        return {
            "status": "error",
            "error": {
                "code": error.get("code"),
                "message": error.get("message"),
                "data": error.get("data")
            }
        }
    
    # Unknown format
    raise ValueError(f"Unknown A2A message format: {a2a_message}")


def validate_a2a_message(message: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate A2A message format.
    
    Args:
        message: Message dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check JSON-RPC 2.0 structure
    if "jsonrpc" not in message:
        return False, "Missing 'jsonrpc' field (must be '2.0')"
    
    if message["jsonrpc"] != "2.0":
        return False, f"Invalid jsonrpc version: {message['jsonrpc']} (must be '2.0')"
    
    # Check for request or response
    if "method" in message:
        # Request validation
        if "id" not in message:
            return False, "Missing 'id' field in request"
        if "params" not in message:
            return False, "Missing 'params' field in request"
        
        # Validate params for a2a.sendMessage
        if message["method"] == "a2a.sendMessage":
            params = message["params"]
            required = ["from", "to", "type", "priority", "subject", "content"]
            for field in required:
                if field not in params:
                    return False, f"Missing required field in params: {field}"
            
            # Validate type
            valid_types = ["request", "response", "notification", "escalation"]
            if params["type"] not in valid_types:
                return False, f"Invalid type: {params['type']} (must be one of {valid_types})"
            
            # Validate priority
            valid_priorities = ["low", "medium", "high", "urgent"]
            if params["priority"] not in valid_priorities:
                return False, f"Invalid priority: {params['priority']} (must be one of {valid_priorities})"
    
    elif "result" in message or "error" in message:
        # Response validation
        if "id" not in message:
            return False, "Missing 'id' field in response"
        if "result" not in message and "error" not in message:
            return False, "Response must have either 'result' or 'error'"
        
        if "error" in message:
            error = message["error"]
            if "code" not in error:
                return False, "Error object missing 'code' field"
            if "message" not in error:
                return False, "Error object missing 'message' field"
    
    else:
        return False, "Message must be either a request (with 'method') or response (with 'result' or 'error')"
    
    return True, None

