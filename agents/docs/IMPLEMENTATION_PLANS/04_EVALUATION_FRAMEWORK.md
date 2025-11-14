# Implementation Plan: Evaluation Framework

**Priority**: ⭐⭐⭐ HIGH  
**Estimated Time**: 1-2 weeks  
**Status**: Planning

---

## Overview

Create a systematic evaluation framework for measuring agent performance, quality, and effectiveness with metrics, benchmarking, and continuous evaluation.

---

## Goals

1. **Performance Metrics**: Define and track agent performance metrics
2. **Quality Scoring**: Score agent outputs systematically
3. **Benchmarking**: Compare agents against standards
4. **Continuous Evaluation**: Evaluate agents continuously
5. **Improvement Tracking**: Track improvements over time

---

## Architecture

### Components

```
agents/evaluation/
├── __init__.py
├── engine.py              # Evaluation engine
├── metrics.py             # Metrics definitions
├── benchmarks.py          # Benchmarking system
├── scorer.py              # Quality scoring
├── reports.py             # Evaluation reports
└── dashboard.py           # Evaluation dashboard
```

### Flow

```
Agent Output/Performance
    ↓
Evaluation Engine
    ↓
┌──────────────────────┐
│ 1. COLLECT           │ → Gather data
│    - Outputs         │ → Agent outputs
│    - Metrics         │ → Performance data
│    - Context         │ → Task context
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 2. MEASURE           │ → Calculate metrics
│    - Quality         │ → Output quality
│    - Performance     │ → Speed, efficiency
│    - Correctness     │ → Accuracy
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. COMPARE           │ → Benchmark
│    - Against standard│ → Compare to baseline
│    - Against peers   │ → Compare to other agents
│    - Against history  │ → Compare to past
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 4. SCORE             │ → Calculate scores
│    - Quality score   │ → Overall quality
│    - Performance score│ → Efficiency
│    - Composite score │ → Overall score
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 5. REPORT            │ → Generate report
│    - Metrics         │ → Show metrics
│    - Trends          │ → Show trends
│    - Recommendations │ → Improvement suggestions
└──────────────────────┘
```

---

## Implementation Steps

### Step 1: Define Metrics

**File**: `agents/evaluation/metrics.py`

```python
"""Metrics definitions for agent evaluation."""

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
```

---

### Step 2: Implement Scorer

**File**: `agents/evaluation/scorer.py`

```python
"""Quality scoring for agent evaluation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .metrics import AgentMetrics, Metric, MetricType

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
```

---

### Step 3: Implement Benchmarks

**File**: `agents/evaluation/benchmarks.py`

```python
"""Benchmarking system for agent evaluation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .metrics import AgentMetrics

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
```

---

### Step 4: Implement Evaluation Engine

**File**: `agents/evaluation/engine.py`

```python
"""Main evaluation engine."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .metrics import MetricsCollector, AgentMetrics, Metric
from .scorer import AgentScorer
from .benchmarks import BenchmarkSystem
from .reports import ReportGenerator

class EvaluationEngine:
    """Main evaluation engine."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.scorer = AgentScorer()
        self.benchmark_system = BenchmarkSystem()
        self.report_generator = ReportGenerator()
    
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
            from .metrics import Metric, MetricType
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
```

---

### Step 5: Create MCP Tools

**File**: `agents/apps/agent-mcp/tools/evaluation.py`

```python
"""MCP tools for evaluation framework."""

from mcp.server import Server
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.evaluation.engine import EvaluationEngine
    from agents.evaluation.metrics import AgentMetrics
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False

def register_evaluation_tools(server: Server):
    """Register evaluation MCP tools."""
    
    if not EVALUATION_AVAILABLE:
        return
    
    engine = EvaluationEngine()
    
    @server.tool()
    async def evaluate_agent_task(
        agent_id: str,
        task_id: str,
        start_time: str,
        end_time: str,
        tool_calls: str,
        success: bool,
        quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Evaluate an agent task."""
        import json
        from datetime import datetime
        
        tool_calls_list = json.loads(tool_calls) if isinstance(tool_calls, str) else tool_calls
        
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        
        metrics = engine.evaluate_agent_task(
            agent_id=agent_id,
            task_id=task_id,
            start_time=start,
            end_time=end,
            tool_calls=tool_calls_list,
            output=None,  # Output not needed for basic evaluation
            success=success,
            quality_score=quality_score
        )
        
        report = engine.generate_evaluation_report(metrics)
        
        return {
            "status": "success",
            "report": report
        }
    
    @server.tool()
    async def get_agent_performance(
        agent_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get agent performance metrics."""
        # This would query stored metrics
        # For now, return placeholder
        return {
            "status": "success",
            "agent_id": agent_id,
            "metrics": []
        }
```

---

## Integration Points

### 1. Integration with Monitoring

- Collect metrics from monitoring system
- Store evaluation results
- Display in dashboard

### 2. Integration with Agents

- Agents request evaluation
- Automatic evaluation on task completion
- Feedback based on evaluation

### 3. Integration with Learning Agent

- Evaluation results feed learning
- Identify improvement areas
- Track improvement over time

---

## Success Criteria

1. ✅ Metrics collected systematically
2. ✅ Scores calculated accurately
3. ✅ Benchmarks defined and used
4. ✅ Reports generated
5. ✅ Integration with monitoring
6. ✅ Documentation complete

---

**Last Updated**: 2025-01-13  
**Status**: Planning Complete - Ready for Implementation

