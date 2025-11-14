"""Type definitions for evaluation framework."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class MetricType(Enum):
    """Types of metrics."""
    QUALITY = "quality"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"

@dataclass
class Metric:
    """Represents a metric."""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

@dataclass
class AgentMetrics:
    """Metrics for an agent."""
    agent_id: str
    task_id: Optional[str]
    metrics: List[Metric]
    quality_score: float
    performance_score: float
    correctness_score: float
    efficiency_score: float
    composite_score: float
    evaluated_at: datetime

