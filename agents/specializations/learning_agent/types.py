"""Type definitions for learning agent."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class FeedbackType(Enum):
    """Types of feedback."""
    CORRECTION = "correction"  # Something was wrong
    IMPROVEMENT = "improvement"  # Could be better
    CONFIRMATION = "confirmation"  # This is correct
    REJECTION = "rejection"  # This is wrong

class RuleTrigger(Enum):
    """When to apply a rule."""
    ALWAYS = "always"  # Always apply
    ON_MATCH = "on_match"  # When pattern matches
    ON_ERROR = "on_error"  # When error occurs
    ON_CONTEXT = "on_context"  # When context matches

@dataclass
class Feedback:
    """Represents feedback from human or agent."""
    feedback_id: str
    feedback_type: FeedbackType
    agent_id: str
    task_id: Optional[str]
    context: Dict[str, Any]  # What was being done
    issue: str  # What was wrong/needs improvement
    correction: str  # What should be done
    provided_by: str  # "human" or agent_id
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LearnedRule:
    """Represents a learned rule."""
    rule_id: str
    name: str
    description: str
    trigger: RuleTrigger
    condition: Dict[str, Any]  # When to apply
    action: Dict[str, Any]  # What to do
    source_feedback: List[str]  # Feedback IDs that created this rule
    confidence: float  # 0.0 to 1.0
    created_at: datetime
    last_applied: Optional[datetime] = None
    application_count: int = 0
    success_count: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.application_count == 0:
            return 0.0
        return self.success_count / self.application_count

@dataclass
class Pattern:
    """Represents a pattern extracted from feedback."""
    pattern_id: str
    name: str
    description: str
    frequency: int  # How many times seen
    feedback_ids: List[str]  # Related feedback
    extracted_at: datetime
    confidence: float

