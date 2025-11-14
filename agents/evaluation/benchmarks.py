"""Benchmarking system for agent evaluation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .types import AgentMetrics

class Benchmark:
    """Represents a benchmark."""
    
    def __init__(
        self,
        benchmark_id: str,
        name: str,
        description: str,
        baseline_scores: Dict[str, float]
    ):
        self.benchmark_id = benchmark_id
        self.name = name
        self.description = description
        self.baseline_scores = baseline_scores  # Expected scores

class BenchmarkSystem:
    """Benchmarking system for agents."""
    
    def __init__(self):
        self.benchmarks: Dict[str, Benchmark] = {}
        self._load_default_benchmarks()
    
    def _load_default_benchmarks(self):
        """Load default benchmarks."""
        # Quality benchmark
        self.benchmarks["quality"] = Benchmark(
            benchmark_id="quality-baseline",
            name="Quality Baseline",
            description="Minimum acceptable quality score",
            baseline_scores={"quality": 0.7, "composite": 0.7}
        )
        
        # Performance benchmark
        self.benchmarks["performance"] = Benchmark(
            benchmark_id="performance-baseline",
            name="Performance Baseline",
            description="Minimum acceptable performance",
            baseline_scores={"performance": 0.6, "composite": 0.7}
        )
    
    def compare_to_benchmark(
        self,
        agent_metrics: AgentMetrics,
        benchmark_id: str
    ) -> Dict[str, Any]:
        """Compare agent metrics to benchmark."""
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {"error": f"Benchmark {benchmark_id} not found"}
        
        comparison = {
            "benchmark_id": benchmark_id,
            "benchmark_name": benchmark.name,
            "scores": {},
            "meets_benchmark": True
        }
        
        agent_scores = {
            "quality": agent_metrics.quality_score,
            "performance": agent_metrics.performance_score,
            "correctness": agent_metrics.correctness_score,
            "efficiency": agent_metrics.efficiency_score,
            "composite": agent_metrics.composite_score
        }
        
        for score_name, baseline in benchmark.baseline_scores.items():
            agent_value = agent_scores.get(score_name, 0.0)
            comparison["scores"][score_name] = {
                "agent": agent_value,
                "baseline": baseline,
                "difference": agent_value - baseline,
                "meets": agent_value >= baseline
            }
            
            if agent_value < baseline:
                comparison["meets_benchmark"] = False
        
        return comparison
    
    def compare_to_peers(
        self,
        agent_metrics: AgentMetrics,
        peer_metrics: List[AgentMetrics]
    ) -> Dict[str, Any]:
        """Compare agent to peers."""
        if not peer_metrics:
            return {"error": "No peer metrics available"}
        
        # Calculate peer averages
        peer_avg = {
            "quality": sum(m.quality_score for m in peer_metrics) / len(peer_metrics),
            "performance": sum(m.performance_score for m in peer_metrics) / len(peer_metrics),
            "correctness": sum(m.correctness_score for m in peer_metrics) / len(peer_metrics),
            "efficiency": sum(m.efficiency_score for m in peer_metrics) / len(peer_metrics),
            "composite": sum(m.composite_score for m in peer_metrics) / len(peer_metrics)
        }
        
        agent_scores = {
            "quality": agent_metrics.quality_score,
            "performance": agent_metrics.performance_score,
            "correctness": agent_metrics.correctness_score,
            "efficiency": agent_metrics.efficiency_score,
            "composite": agent_metrics.composite_score
        }
        
        comparison = {
            "agent_scores": agent_scores,
            "peer_averages": peer_avg,
            "percentiles": {}
        }
        
        # Calculate percentiles
        for score_name in agent_scores.keys():
            agent_value = agent_scores[score_name]
            peer_values = [getattr(m, f"{score_name}_score") for m in peer_metrics]
            peer_values.append(agent_value)
            peer_values.sort()
            
            percentile = (peer_values.index(agent_value) / len(peer_values)) * 100
            comparison["percentiles"][score_name] = percentile
        
        return comparison

