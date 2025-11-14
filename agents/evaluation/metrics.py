"""Metrics definitions and collection for agent evaluation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .types import Metric, MetricType

class MetricsCollector:
    """Collects metrics for evaluation."""
    
    def collect_task_metrics(
        self,
        agent_id: str,
        task_id: str,
        start_time: datetime,
        end_time: datetime,
        tool_calls: List[Dict[str, Any]],
        output: Any,
        success: bool
    ) -> List[Metric]:
        """Collect metrics from task execution."""
        metrics = []
        
        # Duration
        duration_seconds = (end_time - start_time).total_seconds()
        metrics.append(Metric(
            metric_id=f"metric-{uuid.uuid4().hex[:8]}",
            name="task_duration",
            metric_type=MetricType.PERFORMANCE,
            value=duration_seconds,
            unit="seconds",
            timestamp=end_time,
            context={"task_id": task_id}
        ))
        
        # Tool usage
        metrics.append(Metric(
            metric_id=f"metric-{uuid.uuid4().hex[:8]}",
            name="tool_calls_count",
            metric_type=MetricType.EFFICIENCY,
            value=len(tool_calls),
            unit="count",
            timestamp=end_time,
            context={"task_id": task_id}
        ))
        
        # Success rate
        metrics.append(Metric(
            metric_id=f"metric-{uuid.uuid4().hex[:8]}",
            name="task_success",
            metric_type=MetricType.RELIABILITY,
            value=1.0 if success else 0.0,
            unit="boolean",
            timestamp=end_time,
            context={"task_id": task_id}
        ))
        
        return metrics

