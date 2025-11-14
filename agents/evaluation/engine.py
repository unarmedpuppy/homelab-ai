"""Main evaluation engine."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .metrics import MetricsCollector
from .types import AgentMetrics, Metric
from .scorer import AgentScorer
from .benchmarks import BenchmarkSystem

class EvaluationEngine:
    """Main evaluation engine."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.scorer = AgentScorer()
        self.benchmark_system = BenchmarkSystem()
    
    def evaluate_agent_task(
        self,
        agent_id: str,
        task_id: str,
        start_time: datetime,
        end_time: datetime,
        tool_calls: List[Dict[str, Any]],
        output: Any,
        success: bool,
        quality_score: Optional[float] = None
    ) -> AgentMetrics:
        """Evaluate an agent task."""
        # Collect metrics
        metrics = self.metrics_collector.collect_task_metrics(
            agent_id=agent_id,
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            tool_calls=tool_calls,
            output=output,
            success=success
        )
        
        # Add quality score if provided
        if quality_score is not None:
            from .types import Metric, MetricType
            metrics.append(Metric(
                metric_id=f"metric-{uuid.uuid4().hex[:8]}",
                name="output_quality",
                metric_type=MetricType.QUALITY,
                value=quality_score,
                unit="score",
                timestamp=end_time,
                context={"task_id": task_id}
            ))
        
        # Calculate scores
        scores = self.scorer.calculate_scores(metrics)
        
        # Create agent metrics
        agent_metrics = AgentMetrics(
            agent_id=agent_id,
            task_id=task_id,
            metrics=metrics,
            quality_score=scores["quality"],
            performance_score=scores["performance"],
            correctness_score=scores["correctness"],
            efficiency_score=scores["efficiency"],
            composite_score=scores["composite"],
            evaluated_at=datetime.now()
        )
        
        return agent_metrics
    
    def generate_evaluation_report(
        self,
        agent_metrics: AgentMetrics,
        compare_to_benchmark: bool = True,
        compare_to_peers: bool = False,
        peer_metrics: Optional[List[AgentMetrics]] = None
    ) -> Dict[str, Any]:
        """Generate evaluation report."""
        report = {
            "agent_id": agent_metrics.agent_id,
            "task_id": agent_metrics.task_id,
            "scores": {
                "quality": agent_metrics.quality_score,
                "performance": agent_metrics.performance_score,
                "correctness": agent_metrics.correctness_score,
                "efficiency": agent_metrics.efficiency_score,
                "composite": agent_metrics.composite_score
            },
            "metrics_count": len(agent_metrics.metrics),
            "evaluated_at": agent_metrics.evaluated_at.isoformat()
        }
        
        # Compare to benchmark
        if compare_to_benchmark:
            benchmark_comparison = self.benchmark_system.compare_to_benchmark(
                agent_metrics,
                "quality"
            )
            report["benchmark_comparison"] = benchmark_comparison
        
        # Compare to peers
        if compare_to_peers and peer_metrics:
            peer_comparison = self.benchmark_system.compare_to_peers(
                agent_metrics,
                peer_metrics
            )
            report["peer_comparison"] = peer_comparison
        
        return report

