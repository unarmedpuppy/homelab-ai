# Implementation Plan: Agent Gym

**Priority**: ⭐⭐ MEDIUM  
**Estimated Time**: 
- **NOW (Prompt Testing)**: 1-2 weeks
- **LATER (Process Simulation)**: 3-4 weeks  
**Status**: Planning

---

## ⚠️ Architecture Context

**Current Architecture**: Agents are Cursor sessions (ephemeral, file-based)  
**Future Architecture**: Agents will be dynamically spawned processes

This plan includes **TWO implementations**:
1. **NOW**: Prompt/definition testing and optimization (works with Cursor sessions)
2. **LATER**: Full process simulation and optimization (when you can spawn agents dynamically)

---

## Overview

Create an offline optimization platform (Agent Gym) for simulating, testing, and optimizing agents outside the production execution path.

**NOW**: Test and optimize agent prompts/definitions  
**LATER**: Simulate and optimize agent processes

---

## Goals

1. **Simulation Environment**: Test agents safely on simulated data
2. **Synthetic Data Generation**: Generate test scenarios
3. **Optimization Tools**: Advanced optimization capabilities
4. **Red-Teaming**: Pressure test agents
5. **Human Consultation**: Connect to domain experts

---

# PART 1: NOW - Prompt/Definition Testing

**Status**: ✅ Ready to implement  
**Architecture**: File-based, prompt testing  
**Timeline**: 1-2 weeks

---

## NOW: Overview

Test and optimize agent prompts/definitions without spawning processes:
- **Testing**: Test agent definitions against scenarios
- **Optimization**: Optimize prompts based on results
- **Evaluation**: Evaluate prompt effectiveness
- **Red-Teaming**: Test prompts with edge cases

---

## NOW: Architecture

### Components

```
agents/gym/
├── __init__.py
├── prompt_tester.py       # Test agent prompts
├── definition_analyzer.py  # Analyze agent definitions
├── scenario_generator.py   # Generate test scenarios
├── prompt_optimizer.py    # Optimize prompts
└── results_analyzer.py    # Analyze test results
```

### Flow (Prompt Testing)

```
Agent Definition
    ↓
Prompt Tester
    ↓
┌──────────────────────┐
│ 1. GENERATE SCENARIOS│ → Create test scenarios
│    - Load definition │ → Agent definition
│    - Generate data   │ → Synthetic scenarios
│    - Create tests    │ → Test cases
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 2. TEST PROMPT       │ → Test prompt logic
│    - Parse prompt    │ → Extract structure
│    - Test logic      │ → Validate reasoning
│    - Check coverage  │ → Test completeness
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. EVALUATE          │ → Measure effectiveness
│    - Score prompt    │ → Calculate scores
│    - Identify gaps   │ → Find issues
│    - Compare         │ → Compare versions
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 4. OPTIMIZE          │ → Improve prompt
│    - Suggest changes │ → Recommendations
│    - Generate variants│ → Create alternatives
│    - Test variants   │ → Compare results
└──────────────────────┘
    ↓
Optimized Prompt
```

---

## NOW: Implementation Steps

### Step 1: Prompt Tester

**File**: `agents/gym/prompt_tester.py`

```python
"""Test agent prompts and definitions."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
import re

class PromptTester:
    """Tests agent prompts and definitions."""
    
    def __init__(self, definition_path: Path):
        self.definition_path = definition_path
        self.definition = self._load_definition()
    
    def _load_definition(self) -> Dict[str, Any]:
        """Load agent definition."""
        with open(self.definition_path, "r") as f:
            content = f.read()
        
        # Parse YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                markdown_content = parts[2]
                metadata = yaml.safe_load(yaml_content)
                return {
                    **metadata,
                    "content": markdown_content
                }
        
        return {"content": content}
    
    def test_prompt_structure(self) -> Dict[str, Any]:
        """Test prompt structure."""
        content = self.definition.get("content", "")
        
        results = {
            "has_role": bool(re.search(r"# Role|## Role", content)),
            "has_responsibilities": bool(re.search(r"# Responsibilities|## Responsibilities", content)),
            "has_workflow": bool(re.search(r"# Workflow|## Workflow", content)),
            "has_tools": bool(re.search(r"# Tools|## Tools", content)),
            "has_examples": bool(re.search(r"# Examples|## Examples", content)),
            "sections": self._extract_sections(content)
        }
        
        return results
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract section headers."""
        sections = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
        return sections
    
    def test_prompt_completeness(self) -> Dict[str, Any]:
        """Test prompt completeness."""
        content = self.definition.get("content", "")
        
        # Check for required elements
        required = {
            "role": r"role|purpose|identity",
            "capabilities": r"capabilities|skills|tools",
            "workflow": r"workflow|process|steps"
        }
        
        results = {}
        for key, pattern in required.items():
            results[key] = bool(re.search(pattern, content, re.IGNORECASE))
        
        return results
    
    def test_against_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test prompt against scenarios."""
        results = []
        
        for scenario in scenarios:
            # Check if prompt mentions scenario-related concepts
            content = self.definition.get("content", "").lower()
            scenario_keywords = scenario.get("keywords", [])
            
            matches = sum(1 for keyword in scenario_keywords if keyword.lower() in content)
            coverage = matches / len(scenario_keywords) if scenario_keywords else 0
            
            results.append({
                "scenario": scenario.get("name"),
                "coverage": coverage,
                "matches": matches,
                "total_keywords": len(scenario_keywords)
            })
        
        return {
            "scenarios_tested": len(scenarios),
            "average_coverage": sum(r["coverage"] for r in results) / len(results) if results else 0,
            "results": results
        }
```

---

### Step 2: Scenario Generator

**File**: `agents/gym/scenario_generator.py`

```python
"""Generate test scenarios for prompt testing."""

from typing import Dict, List, Any
import uuid

class ScenarioGenerator:
    """Generates test scenarios for agent prompts."""
    
    def generate_scenarios(
        self,
        agent_type: str,
        complexity: str = "medium",
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate test scenarios."""
        scenarios = []
        
        # Base scenarios by agent type
        base_scenarios = {
            "server-management": [
                {"name": "Container deployment", "keywords": ["docker", "container", "deploy", "service"]},
                {"name": "Troubleshooting", "keywords": ["error", "log", "debug", "fix"]},
                {"name": "Monitoring", "keywords": ["monitor", "health", "status", "metrics"]}
            ],
            "media-download": [
                {"name": "Download management", "keywords": ["download", "queue", "client", "sonarr"]},
                {"name": "Stuck downloads", "keywords": ["stuck", "failed", "retry", "remove"]},
                {"name": "Quality settings", "keywords": ["quality", "profile", "format", "resolution"]}
            ]
        }
        
        base = base_scenarios.get(agent_type, [])
        
        for i in range(count):
            scenario = base[i % len(base)] if base else {
                "name": f"Scenario {i+1}",
                "keywords": []
            }
            
            scenarios.append({
                "scenario_id": f"scenario-{uuid.uuid4().hex[:8]}",
                "name": scenario["name"],
                "keywords": scenario["keywords"],
                "complexity": complexity,
                "description": f"Test scenario for {scenario['name']}"
            })
        
        return scenarios
```

---

### Step 3: Prompt Optimizer

**File**: `agents/gym/prompt_optimizer.py`

```python
"""Optimize agent prompts based on test results."""

from typing import Dict, List, Any
from pathlib import Path

class PromptOptimizer:
    """Optimizes agent prompts."""
    
    def analyze_prompt(self, definition_path: Path, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt and suggest improvements."""
        with open(definition_path, "r") as f:
            content = f.read()
        
        suggestions = []
        
        # Check structure
        if not test_results.get("has_role"):
            suggestions.append({
                "type": "missing_section",
                "section": "Role",
                "suggestion": "Add a 'Role' section defining the agent's identity"
            })
        
        if not test_results.get("has_workflow"):
            suggestions.append({
                "type": "missing_section",
                "section": "Workflow",
                "suggestion": "Add a 'Workflow' section describing the agent's process"
            })
        
        # Check coverage
        if test_results.get("average_coverage", 0) < 0.5:
            suggestions.append({
                "type": "low_coverage",
                "suggestion": "Add more keywords and concepts to improve scenario coverage"
            })
        
        return {
            "suggestions": suggestions,
            "score": self._calculate_score(test_results),
            "improvements": len(suggestions)
        }
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Calculate prompt quality score."""
        structure_score = sum([
            results.get("has_role", False),
            results.get("has_responsibilities", False),
            results.get("has_workflow", False),
            results.get("has_tools", False)
        ]) / 4.0
        
        coverage_score = results.get("average_coverage", 0)
        
        return (structure_score * 0.6 + coverage_score * 0.4)
```

---

## NOW: Success Criteria

1. ✅ Agent definitions tested for structure
2. ✅ Scenarios generated and tested
3. ✅ Prompt effectiveness measured
4. ✅ Optimization suggestions generated
5. ✅ Works with file-based definitions

---

# PART 2: LATER - Process Simulation

**Status**: ⏸️ Deferred until dynamic spawning available  
**Architecture**: Process simulation, dynamic spawning  
**Timeline**: 3-4 weeks (when ready)

---

## LATER: Overview

Full simulation environment for dynamically spawned agent processes:
- **Simulation**: Spawn agents as processes for testing
- **Optimization**: Optimize agent behavior through simulation
- **Red-Teaming**: Pressure test with adversarial scenarios
- **Evolution**: Evolutionary optimization of agents

---

## LATER: Architecture

### Components

```
agents/gym/
├── __init__.py
├── simulator.py          # Process simulation environment
├── data_generator.py      # Synthetic data generation
├── optimizer.py          # Optimization engine
├── red_team.py          # Red-teaming tools
├── process_manager.py   # Process lifecycle management
└── expert_consultation.py # Human expert integration
```

### Flow (Process Simulation)

```
Agent Definition
    ↓
Agent Gym
    ↓
┌──────────────────────┐
│ 1. SIMULATE          │ → Spawn agent process
│    - Load agent      │ → Agent definition
│    - Generate data   │ → Synthetic scenarios
│    - Spawn process   │ → Run agent as process
│    - Execute         │ → Run agent
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 2. EVALUATE          │ → Measure performance
│    - Collect metrics │ → Performance data
│    - Analyze         │ → Identify issues
│    - Score           │ → Calculate scores
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. OPTIMIZE          │ → Improve agent
│    - Identify issues │ → Find problems
│    - Suggest changes  │ → Recommendations
│    - Test changes    │ → Verify improvements
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 4. RED-TEAM          │ → Pressure test
│    - Edge cases      │ → Test edge cases
│    - Adversarial     │ → Test robustness
│    - Stress test     │ → Test limits
└──────────────────────┘
    ↓
Optimized Agent
```

---

## LATER: Implementation Steps

### Step 1: Create Simulation Environment

**File**: `agents/gym/simulator.py`

```python
"""Simulation environment for Agent Gym."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

class SimulationEnvironment:
    """Simulation environment for testing agents."""
    
    def __init__(self, agent_definition_path: Path):
        self.agent_definition_path = agent_definition_path
        self.simulation_results = []
    
    async def simulate_task(
        self,
        task_description: str,
        synthetic_data: Dict[str, Any],
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """Simulate agent executing a task."""
        # Load agent definition
        agent_def = self._load_agent_definition()
        
        # Create simulation context
        context = {
            "task": task_description,
            "data": synthetic_data,
            "simulation": True
        }
        
        # Simulate agent execution
        # This would use orchestration engine in simulation mode
        result = await self._simulate_execution(
            agent_def,
            context,
            max_iterations
        )
        
        self.simulation_results.append(result)
        return result
    
    def _load_agent_definition(self) -> Dict[str, Any]:
        """Load agent definition."""
        # Load from file
        import yaml
        with open(self.agent_definition_path) as f:
            return yaml.safe_load(f)
    
    async def _simulate_execution(
        self,
        agent_def: Dict[str, Any],
        context: Dict[str, Any],
        max_iterations: int
    ) -> Dict[str, Any]:
        """Simulate agent execution."""
        # Use orchestration engine in simulation mode
        # Tools are mocked/simulated
        # Results are simulated
        
        return {
            "success": True,
            "iterations": 5,
            "tools_called": ["tool1", "tool2"],
            "duration_seconds": 10.5,
            "simulated": True
        }
```

---

### Step 2: Implement Synthetic Data Generator

**File**: `agents/gym/data_generator.py`

```python
"""Synthetic data generation for Agent Gym."""

from typing import Dict, List, Any
import random
import uuid

class SyntheticDataGenerator:
    """Generates synthetic data for testing."""
    
    def generate_task_scenario(
        self,
        task_type: str,
        complexity: str = "medium",
        edge_cases: bool = False
    ) -> Dict[str, Any]:
        """Generate synthetic task scenario."""
        scenario = {
            "task_id": f"sim-task-{uuid.uuid4().hex[:8]}",
            "task_type": task_type,
            "complexity": complexity,
            "description": self._generate_description(task_type, complexity),
            "data": self._generate_data(task_type, complexity, edge_cases),
            "expected_outcome": self._generate_expected_outcome(task_type)
        }
        
        return scenario
    
    def _generate_description(self, task_type: str, complexity: str) -> str:
        """Generate task description."""
        descriptions = {
            "deployment": {
                "simple": "Deploy a simple service",
                "medium": "Deploy a service with dependencies",
                "complex": "Deploy a complex multi-service application"
            },
            "troubleshooting": {
                "simple": "Fix a simple container issue",
                "medium": "Diagnose and fix a network problem",
                "complex": "Resolve a complex system failure"
            }
        }
        
        return descriptions.get(task_type, {}).get(complexity, "Test task")
    
    def _generate_data(self, task_type: str, complexity: str, edge_cases: bool) -> Dict[str, Any]:
        """Generate synthetic data."""
        data = {
            "containers": self._generate_containers(complexity),
            "networks": self._generate_networks(),
            "volumes": self._generate_volumes()
        }
        
        if edge_cases:
            data["edge_cases"] = self._generate_edge_cases(task_type)
        
        return data
    
    def _generate_containers(self, complexity: str) -> List[Dict[str, Any]]:
        """Generate synthetic container data."""
        count = {"simple": 1, "medium": 3, "complex": 10}[complexity]
        
        containers = []
        for i in range(count):
            containers.append({
                "name": f"container-{i}",
                "status": random.choice(["running", "stopped", "restarting"]),
                "image": f"image-{i}:latest"
            })
        
        return containers
    
    def _generate_networks(self) -> List[Dict[str, Any]]:
        """Generate synthetic network data."""
        return [
            {"name": "my-network", "driver": "bridge"},
            {"name": "default", "driver": "bridge"}
        ]
    
    def _generate_volumes(self) -> List[Dict[str, Any]]:
        """Generate synthetic volume data."""
        return [
            {"name": "data-volume", "driver": "local"}
        ]
    
    def _generate_edge_cases(self, task_type: str) -> List[str]:
        """Generate edge cases for testing."""
        edge_cases = {
            "deployment": [
                "port_conflict",
                "missing_dependency",
                "invalid_config"
            ],
            "troubleshooting": [
                "timeout",
                "permission_denied",
                "resource_exhaustion"
            ]
        }
        
        return edge_cases.get(task_type, [])
    
    def _generate_expected_outcome(self, task_type: str) -> Dict[str, Any]:
        """Generate expected outcome."""
        return {
            "success": True,
            "steps_completed": 5,
            "quality_score": 0.8
        }
```

---

### Step 3: Implement Optimizer

**File**: `agents/gym/optimizer.py`

```python
"""Optimization engine for Agent Gym."""

from typing import Dict, List, Any, Optional
from .simulator import SimulationEnvironment
from .data_generator import SyntheticDataGenerator

class AgentOptimizer:
    """Optimizes agents using simulation."""
    
    def __init__(self, agent_definition_path: Path):
        self.simulator = SimulationEnvironment(agent_definition_path)
        self.data_generator = SyntheticDataGenerator()
    
    async def optimize_agent(
        self,
        optimization_goals: List[str],
        test_scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Optimize agent using simulation."""
        if not test_scenarios:
            test_scenarios = self._generate_test_scenarios()
        
        results = []
        for scenario in test_scenarios:
            result = await self.simulator.simulate_task(
                task_description=scenario["description"],
                synthetic_data=scenario["data"]
            )
            results.append(result)
        
        # Analyze results
        analysis = self._analyze_results(results, optimization_goals)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)
        
        return {
            "results": results,
            "analysis": analysis,
            "recommendations": recommendations
        }
    
    def _generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate test scenarios."""
        scenarios = []
        
        # Simple scenarios
        for _ in range(5):
            scenarios.append(
                self.data_generator.generate_task_scenario("deployment", "simple")
            )
        
        # Medium scenarios
        for _ in range(5):
            scenarios.append(
                self.data_generator.generate_task_scenario("deployment", "medium")
            )
        
        # Complex scenarios
        for _ in range(3):
            scenarios.append(
                self.data_generator.generate_task_scenario("deployment", "complex")
            )
        
        # Edge cases
        for _ in range(2):
            scenarios.append(
                self.data_generator.generate_task_scenario("deployment", "medium", edge_cases=True)
            )
        
        return scenarios
    
    def _analyze_results(
        self,
        results: List[Dict[str, Any]],
        goals: List[str]
    ) -> Dict[str, Any]:
        """Analyze simulation results."""
        analysis = {
            "total_scenarios": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "average_duration": sum(r.get("duration_seconds", 0) for r in results) / len(results),
            "average_iterations": sum(r.get("iterations", 0) for r in results) / len(results),
            "issues": []
        }
        
        # Identify issues
        for result in results:
            if not result.get("success"):
                analysis["issues"].append({
                    "scenario": result.get("task_id"),
                    "error": result.get("error"),
                    "iterations": result.get("iterations")
                })
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if analysis["successful"] / analysis["total_scenarios"] < 0.8:
            recommendations.append("Improve error handling - many scenarios failed")
        
        if analysis["average_duration"] > 60:
            recommendations.append("Optimize performance - tasks take too long")
        
        if analysis["average_iterations"] > 20:
            recommendations.append("Reduce loop iterations - agent is inefficient")
        
        if analysis["issues"]:
            recommendations.append(f"Fix {len(analysis['issues'])} identified issues")
        
        return recommendations
```

---

### Step 4: Implement Red-Teaming

**File**: `agents/gym/red_team.py`

```python
"""Red-teaming tools for Agent Gym."""

from typing import Dict, List, Any
from .simulator import SimulationEnvironment

class RedTeam:
    """Red-teaming tools for pressure testing."""
    
    def __init__(self, simulator: SimulationEnvironment):
        self.simulator = simulator
    
    async def test_edge_cases(
        self,
        agent_definition_path: Path
    ) -> Dict[str, Any]:
        """Test agent with edge cases."""
        edge_case_scenarios = [
            {"description": "Empty input", "data": {}},
            {"description": "Invalid input", "data": {"invalid": True}},
            {"description": "Extremely large input", "data": {"size": "very_large"}},
            {"description": "Missing required data", "data": {"partial": True}}
        ]
        
        results = []
        for scenario in edge_case_scenarios:
            result = await self.simulator.simulate_task(
                task_description=scenario["description"],
                synthetic_data=scenario["data"]
            )
            results.append(result)
        
        return {
            "edge_cases_tested": len(edge_case_scenarios),
            "results": results,
            "robustness_score": self._calculate_robustness(results)
        }
    
    def _calculate_robustness(self, results: List[Dict[str, Any]]) -> float:
        """Calculate robustness score."""
        successful = sum(1 for r in results if r.get("success"))
        return successful / len(results) if results else 0.0
```

---

## Integration Points

### 1. Integration with Orchestration

- Use orchestration engine in simulation mode
- Mock tool execution
- Simulate observations

### 2. Integration with Evaluation

- Evaluate simulated runs
- Compare to benchmarks
- Track improvements

### 3. Integration with Learning Agent

- Learn from simulation results
- Generate rules from failures
- Improve based on testing

---

## LATER: Success Criteria

1. ✅ Process simulation environment working
2. ✅ Agents spawned dynamically for testing
3. ✅ Synthetic data generated
4. ✅ Optimization recommendations generated
5. ✅ Red-teaming tests pass
6. ✅ Process lifecycle managed
7. ✅ Integration complete
8. ✅ Documentation complete

---

## Migration Path: NOW → LATER

When you can spawn agents dynamically:

1. **Keep prompt testing** as first validation step
2. **Add process spawning** for full simulation
3. **Add process manager** for lifecycle management
4. **Add real-time monitoring** of simulated processes
5. **Add evolutionary optimization** for process-based agents
6. **Add red-teaming** with adversarial process testing

---

**Last Updated**: 2025-01-13  
**Status**: 
- **NOW**: Planning Complete - Ready for Prompt Testing Implementation
- **LATER**: Detailed Plan Preserved - Ready When Dynamic Spawning Available

