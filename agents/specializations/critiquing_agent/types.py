"""Type definitions for critiquing agent."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class IssueSeverity(Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"  # Must fix
    HIGH = "high"  # Should fix
    MEDIUM = "medium"  # Consider fixing
    LOW = "low"  # Nice to fix

class IssueCategory(Enum):
    """Categories of issues."""
    CODE_QUALITY = "code_quality"
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"

@dataclass
class QualityIssue:
    """Represents a quality issue found."""
    issue_id: str
    severity: IssueSeverity
    category: IssueCategory
    description: str
    location: Optional[str]  # File, line, etc.
    suggestion: str  # How to fix
    rule_applied: Optional[str]  # Rule ID if rule applied
    detected_at: datetime

@dataclass
class QualityReport:
    """Quality report for agent output."""
    report_id: str
    agent_id: str
    task_id: Optional[str]
    output_type: str  # "code", "documentation", "plan", etc.
    output_content: str
    quality_score: float  # 0.0 to 1.0
    issues: List[QualityIssue]
    rules_applied: List[str]
    created_at: datetime
    reviewed_by: str  # "critiquing-agent"

