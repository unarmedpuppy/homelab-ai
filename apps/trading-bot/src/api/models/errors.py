"""
Standard Error Response Models
==============================

Pydantic models for standardized error responses across all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: bool = Field(default=True, description="Always true for error responses")
    message: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    path: Optional[str] = Field(None, description="API path where error occurred")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    errors: list[ErrorDetail] = Field(default_factory=list, description="List of validation errors")


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        path: API path where error occurred
        status_code: HTTP status code
        
    Returns:
        Dictionary representation of error response
    """
    return {
        "error": True,
        "message": message,
        "error_code": error_code,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
        "path": path,
        "status_code": status_code
    }

