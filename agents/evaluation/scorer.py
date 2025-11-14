"""Quality scoring for agent evaluation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .types import Metric, MetricType

class AgentScorer:
    """Scores agent performance."""
    
    def calculate_scores(self, metrics: List[Metric]) -> Dict[str, float]:
        """Calculate scores from metrics."""
        scores = {
            "quality": self._calculate_quality_score(metrics),
            "performance": self._calculate_performance_score(metrics),
            "correctness": self._calculate_correctness_score(metrics),
            "efficiency": self._calculate_efficiency_score(metrics)
        }
        
        # Composite score (weighted average)
        scores["composite"] = (
            scores["quality"] * 0.4 +
            scores["performance"] * 0.2 +
            scores["correctness"] * 0.3 +
            scores["efficiency"] * 0.1
        )
        
        return scores
    
    def _calculate_quality_score(self, metrics: List[Metric]) -> float:
        """Calculate quality score."""
        quality_metrics = [m for m in metrics if m.metric_type == MetricType.QUALITY]
        
        if not quality_metrics:
            return 0.5  # Default if no quality metrics
        
        # Average quality metrics
        return sum(m.value for m in quality_metrics) / len(quality_metrics)
    
    def _calculate_performance_score(self, metrics: List[Metric]) -> float:
        """Calculate performance score."""
        perf_metrics = [m for m in metrics if m.metric_type == MetricType.PERFORMANCE]
        
        if not perf_metrics:
            return 0.5
        
        # Lower duration = higher score (normalized)
        duration_metrics = [m for m in perf_metrics if m.name == "task_duration"]
        if duration_metrics:
            avg_duration = sum(m.value for m in duration_metrics) / len(duration_metrics)
            # Normalize: 0-60 seconds = 1.0, 60-300 = 0.5, 300+ = 0.0
            if avg_duration <= 60:
                return 1.0
            elif avg_duration <= 300:
                return 1.0 - (avg_duration - 60) / 480
            else:
                return 0.0
        
        return 0.5
    
    def _calculate_correctness_score(self, metrics: List[Metric]) -> float:
        """Calculate correctness score."""
        correctness_metrics = [m for m in metrics if m.metric_type == MetricType.CORRECTNESS]
        
        if not correctness_metrics:
            # Use success rate as proxy
            success_metrics = [m for m in metrics if m.name == "task_success"]
            if success_metrics:
                return sum(m.value for m in success_metrics) / len(success_metrics)
            return 0.5
        
        return sum(m.value for m in correctness_metrics) / len(correctness_metrics)
    
    def _calculate_efficiency_score(self, metrics: List[Metric]) -> float:
        """Calculate efficiency score."""
        efficiency_metrics = [m for m in metrics if m.metric_type == MetricType.EFFICIENCY]
        
        if not efficiency_metrics:
            return 0.5
        
        # Lower tool calls = higher efficiency (for same result)
        tool_call_metrics = [m for m in efficiency_metrics if m.name == "tool_calls_count"]
        if tool_call_metrics:
            avg_calls = sum(m.value for m in tool_call_metrics) / len(tool_call_metrics)
            # Normalize: 0-5 calls = 1.0, 5-20 = 0.5, 20+ = 0.0
            if avg_calls <= 5:
                return 1.0
            elif avg_calls <= 20:
                return 1.0 - (avg_calls - 5) / 30
            else:
                return 0.0
        
        return 0.5

