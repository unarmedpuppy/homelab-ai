# Implementation Plan: Formal Orchestration Layer

**Priority**: ⭐⭐⭐ HIGH  
**Estimated Time**: 
- **NOW (Session-based)**: 1 week
- **LATER (Process-based)**: 2-3 weeks  
**Status**: Planning

---

## ⚠️ Architecture Context

**Current Architecture**: Agents are Cursor sessions (ephemeral, file-based)  
**Future Architecture**: Agents will be dynamically spawned processes

This plan includes **TWO implementations**:
1. **NOW**: Simplified session-based orchestration (works with Cursor sessions)
2. **LATER**: Full process-based orchestration (when you can spawn agents dynamically)

---

## Overview

Implement a formal "Think, Act, Observe" orchestration layer that manages the agent execution loop, tracks state, handles errors, and coordinates tool execution.

**NOW**: Session-based, file-backed state tracking  
**LATER**: Process-based, in-memory state management

---

## Goals

1. **Explicit Loop Management**: Formal "Think, Act, Observe" cycle
2. **State Tracking**: Track loop iterations, context, and progress
3. **Error Recovery**: Automatic error handling and retries
4. **Tool Coordination**: Centralized tool execution
5. **Observation Processing**: Systematic result processing

---

# PART 1: NOW - Session-Based Orchestration

**Status**: ✅ Ready to implement  
**Architecture**: Cursor sessions, file-based state  
**Timeline**: 1 week

---

## NOW: Overview

Simplified orchestration that works within a single Cursor session:
- **State**: Stored in files (JSON/markdown)
- **Execution**: Within Cursor session
- **Coordination**: Via MCP tools
- **Persistence**: File-based, survives session restarts

---

## NOW: Architecture

### Components

```
agents/orchestration/
├── __init__.py
├── session_engine.py      # Session-based orchestration engine
├── file_state.py          # File-based state management
├── loop_tracker.py        # Track loops within session
└── types.py               # Type definitions (shared with LATER)
```

### Flow (Session-Based)

```
Cursor Session
    ↓
Session Orchestration Engine
    ↓
┌─────────────────┐
│ 1. THINK        │ → Reasoning (LLM in session)
│    - Analyze    │ → Plan actions
│    - Plan       │ → Select tools
│    - Save state │ → Write to file
└─────────────────┘
    ↓
┌─────────────────┐
│ 2. ACT          │ → Execute MCP tools
│    - Execute    │ → Call MCP tools
│    - Monitor    │ → Track execution
│    - Save state │ → Write to file
└─────────────────┘
    ↓
┌─────────────────┐
│ 3. OBSERVE      │ → Process results
│    - Collect    │ → Analyze outcomes
│    - Evaluate   │ → Check success
│    - Save state │ → Write to file
└─────────────────┘
    ↓
┌─────────────────┐
│ 4. DECIDE       │ → Continue or complete?
│    - Check goal │ → Goal achieved?
│    - Iterate?   │ → Next iteration
│    - Save state │ → Write to file
└─────────────────┘
    ↓
Loop or Complete
```

---

## NOW: Implementation Steps

### Step 1: File-Based State Management

**File**: `agents/orchestration/file_state.py`

```python
"""File-based state management for session orchestration."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid

class FileStateManager:
    """Manages orchestration state in files."""
    
    def __init__(self, agent_id: str, state_dir: Path):
        self.agent_id = agent_id
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = state_dir / f"{agent_id}-orchestration-state.json"
    
    def load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if not self.state_file.exists():
            return {
                "agent_id": self.agent_id,
                "current_iteration": 0,
                "iterations": [],
                "context": {},
                "created_at": datetime.now().isoformat()
            }
        
        with open(self.state_file, "r") as f:
            return json.load(f)
    
    def save_state(self, state: Dict[str, Any]):
        """Save state to file."""
        state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def start_iteration(self, goal: str) -> Dict[str, Any]:
        """Start a new loop iteration."""
        state = self.load_state()
        
        iteration = {
            "iteration_id": f"iter-{uuid.uuid4().hex[:8]}",
            "phase": "think",
            "goal": goal,
            "started_at": datetime.now().isoformat(),
            "tools_called": [],
            "observations": [],
            "errors": []
        }
        
        state["iterations"].append(iteration)
        state["current_iteration"] = len(state["iterations"]) - 1
        self.save_state(state)
        
        return iteration
    
    def update_iteration(self, iteration_id: str, updates: Dict[str, Any]):
        """Update iteration state."""
        state = self.load_state()
        
        for iteration in state["iterations"]:
            if iteration["iteration_id"] == iteration_id:
                iteration.update(updates)
                iteration["last_updated"] = datetime.now().isoformat()
                break
        
        self.save_state(state)
    
    def record_tool_call(self, iteration_id: str, tool_name: str, params: Dict):
        """Record a tool call."""
        state = self.load_state()
        
        for iteration in state["iterations"]:
            if iteration["iteration_id"] == iteration_id:
                iteration["tools_called"].append({
                    "tool": tool_name,
                    "parameters": params,
                    "timestamp": datetime.now().isoformat()
                })
                break
        
        self.save_state(state)
    
    def record_observation(self, iteration_id: str, observation: Dict[str, Any]):
        """Record an observation."""
        state = self.load_state()
        
        for iteration in state["iterations"]:
            if iteration["iteration_id"] == iteration_id:
                iteration["observations"].append({
                    **observation,
                    "timestamp": datetime.now().isoformat()
                })
                break
        
        self.save_state(state)
```

---

### Step 2: Session-Based Loop Tracker

**File**: `agents/orchestration/loop_tracker.py`

```python
"""Track Think-Act-Observe loops within a session."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .file_state import FileStateManager

class SessionLoopTracker:
    """Tracks loops within a Cursor session."""
    
    def __init__(self, agent_id: str, state_dir: Path):
        self.state_manager = FileStateManager(agent_id, state_dir)
        self.current_iteration_id: Optional[str] = None
    
    def start_loop(self, goal: str) -> Dict[str, Any]:
        """Start a new Think-Act-Observe loop."""
        iteration = self.state_manager.start_iteration(goal)
        self.current_iteration_id = iteration["iteration_id"]
        return iteration
    
    def update_phase(self, phase: str):
        """Update current phase."""
        if self.current_iteration_id:
            self.state_manager.update_iteration(
                self.current_iteration_id,
                {"phase": phase}
            )
    
    def record_tool_call(self, tool_name: str, params: Dict):
        """Record a tool call."""
        if self.current_iteration_id:
            self.state_manager.record_tool_call(
                self.current_iteration_id,
                tool_name,
                params
            )
    
    def record_observation(self, observation: Dict[str, Any]):
        """Record an observation."""
        if self.current_iteration_id:
            self.state_manager.record_observation(
                self.current_iteration_id,
                observation
            )
    
    def complete_iteration(self, success: bool):
        """Complete current iteration."""
        if self.current_iteration_id:
            self.state_manager.update_iteration(
                self.current_iteration_id,
                {
                    "phase": "complete",
                    "success": success,
                    "completed_at": datetime.now().isoformat()
                }
            )
    
    def get_iteration_summary(self) -> Dict[str, Any]:
        """Get summary of current iteration."""
        state = self.state_manager.load_state()
        
        if not state["iterations"]:
            return {}
        
        current = state["iterations"][-1]
        return {
            "iteration_id": current["iteration_id"],
            "phase": current["phase"],
            "tools_called": len(current.get("tools_called", [])),
            "observations": len(current.get("observations", [])),
            "errors": len(current.get("errors", []))
        }
```

---

### Step 3: Session Orchestration Engine

**File**: `agents/orchestration/session_engine.py`

```python
"""Session-based orchestration engine."""

from typing import Dict, List, Any, Optional
from pathlib import Path
from .loop_tracker import SessionLoopTracker

class SessionOrchestrationEngine:
    """Orchestration engine for Cursor sessions."""
    
    def __init__(self, agent_id: str, state_dir: Path):
        self.agent_id = agent_id
        self.tracker = SessionLoopTracker(agent_id, state_dir)
    
    async def run_loop(
        self,
        goal: str,
        think_handler: Optional[callable] = None,
        act_handler: Optional[callable] = None,
        observe_handler: Optional[callable] = None,
        decide_handler: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Run a Think-Act-Observe loop."""
        # Start loop
        iteration = self.tracker.start_loop(goal)
        
        try:
            # THINK phase
            self.tracker.update_phase("think")
            if think_handler:
                tool_calls = await think_handler(goal, self.tracker.get_iteration_summary())
            else:
                tool_calls = []
            
            # ACT phase
            self.tracker.update_phase("act")
            observations = []
            if act_handler:
                for tool_call in tool_calls:
                    # Record tool call
                    self.tracker.record_tool_call(
                        tool_call["tool"],
                        tool_call.get("parameters", {})
                    )
                    # Execute (via MCP tools)
                    obs = await act_handler(tool_call)
                    observations.append(obs)
            
            # OBSERVE phase
            self.tracker.update_phase("observe")
            if observe_handler:
                analysis = await observe_handler(observations)
            else:
                analysis = {"success": all(o.get("success", False) for o in observations)}
            
            # DECIDE phase
            self.tracker.update_phase("decide")
            if decide_handler:
                should_complete = await decide_handler(goal, analysis)
            else:
                should_complete = analysis.get("success", False)
            
            # Complete iteration
            self.tracker.complete_iteration(should_complete)
            
            return {
                "success": should_complete,
                "iteration_id": iteration["iteration_id"],
                "analysis": analysis
            }
            
        except Exception as e:
            self.tracker.record_observation({
                "error": str(e),
                "error_type": type(e).__name__,
                "success": False
            })
            self.tracker.complete_iteration(False)
            raise
```

---

### Step 4: MCP Tool Integration

**File**: `agents/apps/agent-mcp/tools/orchestration.py`

```python
"""MCP tools for session-based orchestration."""

from mcp.server import Server
from typing import Dict, Any, Optional
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.orchestration.session_engine import SessionOrchestrationEngine
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False

def register_orchestration_tools(server: Server):
    """Register session-based orchestration MCP tools."""
    
    if not ORCHESTRATION_AVAILABLE:
        return
    
    @server.tool()
    async def start_orchestrated_loop(
        agent_id: str,
        goal: str,
        state_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start an orchestrated Think-Act-Observe loop.
        
        Works within the current Cursor session.
        State is persisted to files.
        """
        if not state_dir:
            state_dir = project_root / "agents" / "orchestration" / "state"
        
        engine = SessionOrchestrationEngine(agent_id, Path(state_dir))
        
        # Run loop (simplified - agent provides handlers)
        result = await engine.run_loop(goal)
        
        return {
            "status": "success",
            "result": result
        }
    
    @server.tool()
    async def get_loop_state(agent_id: str) -> Dict[str, Any]:
        """Get current loop state from file."""
        from agents.orchestration.file_state import FileStateManager
        
        state_dir = project_root / "agents" / "orchestration" / "state"
        state_manager = FileStateManager(agent_id, state_dir)
        state = state_manager.load_state()
        
        return {
            "status": "success",
            "state": state
        }
```

---

## NOW: Success Criteria

1. ✅ Loop state tracked in files
2. ✅ Phases tracked (Think, Act, Observe, Decide)
3. ✅ Tool calls recorded
4. ✅ Observations stored
5. ✅ Works within Cursor session
6. ✅ State persists across session restarts

---

# PART 2: LATER - Process-Based Orchestration

**Status**: ⏸️ Deferred until dynamic spawning available  
**Architecture**: Separate processes, in-memory state  
**Timeline**: 2-3 weeks (when ready)

---

## LATER: Overview

Full orchestration layer for dynamically spawned agent processes:
- **State**: In-memory, shared across processes
- **Execution**: Separate agent processes
- **Coordination**: Via A2A protocol, HTTP
- **Persistence**: Database-backed, real-time

---

## LATER: Architecture

### Components

```
agents/orchestration/
├── __init__.py
├── engine.py              # Main orchestration engine (process-based)
├── loop_state.py          # Loop state management (in-memory)
├── tool_executor.py       # Tool execution coordinator
├── observer.py            # Observation handler
├── error_recovery.py      # Error handling and retries
├── context_manager.py     # Context management
├── process_manager.py     # Process lifecycle management
└── types.py               # Type definitions
```

### Flow (Process-Based)

```
Agent Process Spawned
    ↓
Orchestration Engine (Process)
    ↓
┌─────────────────┐
│ 1. THINK        │ → Reasoning (LLM)
│    - Analyze    │ → Plan actions
│    - Plan       │ → Select tools
│    - State      │ → In-memory state
└─────────────────┘
    ↓
┌─────────────────┐
│ 2. ACT          │ → Execute tools
│    - Execute    │ → Coordinate tools
│    - Monitor    │ → Track execution
│    - State      │ → In-memory state
└─────────────────┘
    ↓
┌─────────────────┐
│ 3. OBSERVE      │ → Process results
│    - Collect    │ → Analyze outcomes
│    - Evaluate   │ → Check success
│    - State      │ → In-memory state
└─────────────────┘
    ↓
┌─────────────────┐
│ 4. DECIDE       │ → Continue or complete?
│    - Check goal │ → Goal achieved?
│    - Iterate?   │ → Next iteration
│    - State      │ → In-memory state
└─────────────────┘
    ↓
Loop or Complete
```

---

## LATER: Implementation Steps

### Step 1: Define Types and Interfaces

**File**: `agents/orchestration/types.py`

```python
"""Type definitions for orchestration layer."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime

class LoopPhase(Enum):
    """Phases of the Think-Act-Observe loop."""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    DECIDE = "decide"
    COMPLETE = "complete"
    ERROR = "error"

class LoopState(Enum):
    """State of the orchestration loop."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class LoopIteration:
    """Represents a single loop iteration."""
    iteration_id: str
    phase: LoopPhase
    state: LoopState
    timestamp: datetime
    context: Dict[str, Any]
    tools_called: List[str]
    observations: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    retry_count: int = 0

@dataclass
class ToolExecution:
    """Represents a tool execution."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: Optional[datetime] = None

@dataclass
class Observation:
    """Represents an observation from tool execution."""
    tool_name: str
    result: Any
    success: bool
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class OrchestrationContext:
    """Context for orchestration loop."""
    agent_id: str
    task_id: Optional[str]
    goal: str
    max_iterations: int = 50
    current_iteration: int = 0
    iterations: List[LoopIteration] = None
    context_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.iterations is None:
            self.iterations = []
        if self.context_data is None:
            self.context_data = {}
```

---

### Step 2: Implement Loop State Management

**File**: `agents/orchestration/loop_state.py`

```python
"""Loop state management for orchestration."""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
from .types import (
    LoopIteration, LoopPhase, LoopState,
    OrchestrationContext, ToolExecution, Observation
)

class LoopStateManager:
    """Manages state of orchestration loop."""
    
    def __init__(self, context: OrchestrationContext):
        self.context = context
        self.current_iteration: Optional[LoopIteration] = None
    
    def start_iteration(self) -> LoopIteration:
        """Start a new loop iteration."""
        iteration_id = f"iter-{uuid.uuid4().hex[:8]}"
        
        self.current_iteration = LoopIteration(
            iteration_id=iteration_id,
            phase=LoopPhase.THINK,
            state=LoopState.RUNNING,
            timestamp=datetime.now(),
            context=self.context.context_data.copy(),
            tools_called=[],
            observations=[],
            errors=[],
            retry_count=0
        )
        
        self.context.iterations.append(self.current_iteration)
        self.context.current_iteration += 1
        
        return self.current_iteration
    
    def update_phase(self, phase: LoopPhase):
        """Update current iteration phase."""
        if self.current_iteration:
            self.current_iteration.phase = phase
    
    def record_tool_call(self, tool_name: str, parameters: Dict):
        """Record a tool call."""
        if self.current_iteration:
            self.current_iteration.tools_called.append({
                "tool": tool_name,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            })
    
    def record_observation(self, observation: Observation):
        """Record an observation."""
        if self.current_iteration:
            self.current_iteration.observations.append({
                "tool": observation.tool_name,
                "success": observation.success,
                "result": observation.result,
                "timestamp": observation.timestamp.isoformat()
            })
    
    def record_error(self, error: Dict[str, Any]):
        """Record an error."""
        if self.current_iteration:
            self.current_iteration.errors.append({
                **error,
                "timestamp": datetime.now().isoformat()
            })
            self.current_iteration.state = LoopState.FAILED
    
    def complete_iteration(self):
        """Mark current iteration as complete."""
        if self.current_iteration:
            self.current_iteration.state = LoopState.COMPLETED
            self.current_iteration.phase = LoopPhase.COMPLETE
    
    def get_iteration_summary(self) -> Dict:
        """Get summary of current iteration."""
        if not self.current_iteration:
            return {}
        
        return {
            "iteration_id": self.current_iteration.iteration_id,
            "phase": self.current_iteration.phase.value,
            "state": self.current_iteration.state.value,
            "tools_called": len(self.current_iteration.tools_called),
            "observations": len(self.current_iteration.observations),
            "errors": len(self.current_iteration.errors),
            "retry_count": self.current_iteration.retry_count
        }
    
    def should_continue(self) -> bool:
        """Check if loop should continue."""
        # Check max iterations
        if self.context.current_iteration >= self.context.max_iterations:
            return False
        
        # Check if current iteration failed
        if self.current_iteration and self.current_iteration.state == LoopState.FAILED:
            # Allow retries
            return self.current_iteration.retry_count < 3
        
        return True
```

---

### Step 3: Implement Tool Executor

**File**: `agents/orchestration/tool_executor.py`

```python
"""Tool execution coordinator for orchestration."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import asyncio
from .types import ToolExecution, Observation
from .loop_state import LoopStateManager

class ToolExecutor:
    """Coordinates tool execution in orchestration loop."""
    
    def __init__(self, state_manager: LoopStateManager, mcp_tools: Dict):
        self.state_manager = state_manager
        self.mcp_tools = mcp_tools  # Dictionary of available MCP tools
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Observation:
        """Execute a tool and return observation."""
        # Record tool call
        self.state_manager.record_tool_call(tool_name, parameters)
        
        # Get tool function
        tool_func = self.mcp_tools.get(tool_name)
        if not tool_func:
            return Observation(
                tool_name=tool_name,
                result=None,
                success=False,
                metadata={"error": f"Tool {tool_name} not found"},
                timestamp=datetime.now()
            )
        
        # Execute tool
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**parameters)
            else:
                result = tool_func(**parameters)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Record observation
            observation = Observation(
                tool_name=tool_name,
                result=result,
                success=True,
                metadata={
                    "duration_ms": duration_ms,
                    "parameters": parameters
                },
                timestamp=datetime.now()
            )
            
            self.state_manager.record_observation(observation)
            return observation
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error
            self.state_manager.record_error({
                "tool": tool_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": duration_ms
            })
            
            return Observation(
                tool_name=tool_name,
                result=None,
                success=False,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms
                },
                timestamp=datetime.now()
            )
    
    async def execute_tools_parallel(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Observation]:
        """Execute multiple tools in parallel."""
        tasks = [
            self.execute_tool(call["tool"], call["parameters"])
            for call in tool_calls
        ]
        return await asyncio.gather(*tasks)
    
    async def execute_tools_sequential(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Observation]:
        """Execute multiple tools sequentially."""
        observations = []
        for call in tool_calls:
            obs = await self.execute_tool(call["tool"], call["parameters"])
            observations.append(obs)
            # Stop on error if needed
            if not obs.success and call.get("stop_on_error", False):
                break
        return observations
```

---

### Step 4: Implement Observer

**File**: `agents/orchestration/observer.py`

```python
"""Observation handler for orchestration."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .types import Observation, LoopIteration

class Observer:
    """Processes and analyzes observations from tool execution."""
    
    def __init__(self):
        self.observations: List[Observation] = []
    
    def process_observation(self, observation: Observation) -> Dict[str, Any]:
        """Process a single observation."""
        self.observations.append(observation)
        
        return {
            "success": observation.success,
            "tool": observation.tool_name,
            "has_result": observation.result is not None,
            "metadata": observation.metadata
        }
    
    def analyze_iteration(self, iteration: LoopIteration) -> Dict[str, Any]:
        """Analyze observations from an iteration."""
        successful = sum(1 for obs in iteration.observations if obs.get("success", False))
        failed = len(iteration.observations) - successful
        
        return {
            "total_observations": len(iteration.observations),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(iteration.observations) if iteration.observations else 0,
            "tools_used": list(set(obs.get("tool") for obs in iteration.observations)),
            "has_errors": len(iteration.errors) > 0
        }
    
    def check_goal_achieved(
        self,
        goal: str,
        observations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """Check if goal has been achieved based on observations."""
        # Simple heuristic: check if all observations successful
        # This can be enhanced with LLM-based goal checking
        all_successful = all(obs.get("success", False) for obs in observations)
        
        # Check for completion indicators in results
        completion_indicators = [
            "completed", "success", "done", "finished"
        ]
        
        for obs in observations:
            result_str = str(obs.get("result", "")).lower()
            if any(indicator in result_str for indicator in completion_indicators):
                return True
        
        return all_successful
    
    def extract_context(self, observations: List[Observation]) -> Dict[str, Any]:
        """Extract context from observations."""
        context = {
            "tools_used": list(set(obs.tool_name for obs in observations)),
            "successful_tools": [obs.tool_name for obs in observations if obs.success],
            "failed_tools": [obs.tool_name for obs in observations if not obs.success],
            "results": [obs.result for obs in observations if obs.result is not None]
        }
        return context
```

---

### Step 5: Implement Error Recovery

**File**: `agents/orchestration/error_recovery.py`

```python
"""Error recovery and retry logic for orchestration."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from .types import LoopIteration, LoopState, LoopPhase
from .loop_state import LoopStateManager

class ErrorRecovery:
    """Handles error recovery and retries."""
    
    def __init__(self, state_manager: LoopStateManager):
        self.state_manager = state_manager
        self.max_retries = 3
        self.retry_delay_seconds = 1.0
    
    def should_retry(self, iteration: LoopIteration) -> bool:
        """Determine if iteration should be retried."""
        if iteration.state != LoopState.FAILED:
            return False
        
        if iteration.retry_count >= self.max_retries:
            return False
        
        # Check if errors are recoverable
        recoverable_errors = [
            "timeout", "network", "temporary", "rate_limit"
        ]
        
        for error in iteration.errors:
            error_msg = str(error.get("error", "")).lower()
            if any(recoverable in error_msg for recoverable in recoverable_errors):
                return True
        
        return True
    
    def prepare_retry(self, iteration: LoopIteration) -> Dict[str, Any]:
        """Prepare for retry."""
        iteration.retry_count += 1
        iteration.state = LoopState.RETRYING
        iteration.phase = LoopPhase.THINK  # Start over
        
        return {
            "retry_count": iteration.retry_count,
            "max_retries": self.max_retries,
            "delay_seconds": self.retry_delay_seconds * iteration.retry_count
        }
    
    def get_recovery_strategy(self, iteration: LoopIteration) -> str:
        """Get recovery strategy for failed iteration."""
        if not iteration.errors:
            return "unknown"
        
        # Analyze errors to determine strategy
        error_types = [e.get("error_type", "") for e in iteration.errors]
        
        if "TimeoutError" in error_types:
            return "increase_timeout"
        elif "ConnectionError" in error_types:
            return "retry_connection"
        elif "RateLimitError" in error_types:
            return "wait_and_retry"
        else:
            return "retry_with_backoff"
    
    def apply_recovery_strategy(
        self,
        strategy: str,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply recovery strategy to tool calls."""
        if strategy == "increase_timeout":
            # Add timeout parameter to tool calls
            for call in tool_calls:
                if "timeout" not in call.get("parameters", {}):
                    call["parameters"]["timeout"] = 60
        elif strategy == "wait_and_retry":
            # Add delay before retry
            import asyncio
            asyncio.sleep(self.retry_delay_seconds)
        
        return tool_calls
```

---

### Step 6: Implement Context Manager

**File**: `agents/orchestration/context_manager.py`

```python
"""Context management for orchestration."""

from typing import Dict, Any, Optional
from .types import OrchestrationContext, LoopIteration

class ContextManager:
    """Manages context across loop iterations."""
    
    def __init__(self, context: OrchestrationContext):
        self.context = context
    
    def update_context(self, key: str, value: Any):
        """Update context data."""
        self.context.context_data[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context data."""
        return self.context.context_data.get(key, default)
    
    def merge_observations_into_context(self, iteration: LoopIteration):
        """Merge observations from iteration into context."""
        for obs in iteration.observations:
            if obs.get("success") and obs.get("result"):
                # Store tool results in context
                tool_name = obs.get("tool", "unknown")
                self.update_context(f"last_{tool_name}_result", obs.get("result"))
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context."""
        return {
            "agent_id": self.context.agent_id,
            "task_id": self.context.task_id,
            "goal": self.context.goal,
            "current_iteration": self.context.current_iteration,
            "max_iterations": self.context.max_iterations,
            "context_keys": list(self.context.context_data.keys()),
            "total_iterations": len(self.context.iterations)
        }
```

---

### Step 7: Implement Main Orchestration Engine

**File**: `agents/orchestration/engine.py`

```python
"""Main orchestration engine for Think-Act-Observe loop."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
from .types import (
    OrchestrationContext, LoopPhase, LoopState,
    Observation
)
from .loop_state import LoopStateManager
from .tool_executor import ToolExecutor
from .observer import Observer
from .error_recovery import ErrorRecovery
from .context_manager import ContextManager

class OrchestrationEngine:
    """Main orchestration engine managing Think-Act-Observe loop."""
    
    def __init__(
        self,
        context: OrchestrationContext,
        mcp_tools: Dict[str, Callable],
        think_handler: Optional[Callable] = None,
        decide_handler: Optional[Callable] = None
    ):
        self.context = context
        self.state_manager = LoopStateManager(context)
        self.tool_executor = ToolExecutor(self.state_manager, mcp_tools)
        self.observer = Observer()
        self.error_recovery = ErrorRecovery(self.state_manager)
        self.context_manager = ContextManager(context)
        
        # Handlers for custom logic
        self.think_handler = think_handler  # LLM-based thinking
        self.decide_handler = decide_handler  # Goal checking
    
    async def run(self) -> Dict[str, Any]:
        """Run the orchestration loop."""
        try:
            while self.state_manager.should_continue():
                # Start iteration
                iteration = self.state_manager.start_iteration()
                
                # THINK phase
                await self._think_phase(iteration)
                
                # ACT phase
                observations = await self._act_phase(iteration)
                
                # OBSERVE phase
                analysis = await self._observe_phase(observations, iteration)
                
                # DECIDE phase
                should_complete = await self._decide_phase(analysis, iteration)
                
                if should_complete:
                    self.state_manager.complete_iteration()
                    break
                
                # Check for errors and retry
                if iteration.state == LoopState.FAILED:
                    if self.error_recovery.should_retry(iteration):
                        retry_info = self.error_recovery.prepare_retry(iteration)
                        await asyncio.sleep(retry_info["delay_seconds"])
                        continue
                    else:
                        break
            
            return self._generate_result()
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "iterations": len(self.context.iterations)
            }
    
    async def _think_phase(self, iteration):
        """Execute THINK phase."""
        self.state_manager.update_phase(LoopPhase.THINK)
        
        # Use custom think handler if provided
        if self.think_handler:
            tool_calls = await self.think_handler(
                self.context.goal,
                self.context_manager.get_context_summary(),
                iteration
            )
            iteration.context["planned_tool_calls"] = tool_calls
        else:
            # Default: no tool calls planned
            iteration.context["planned_tool_calls"] = []
    
    async def _act_phase(self, iteration) -> list:
        """Execute ACT phase."""
        self.state_manager.update_phase(LoopPhase.ACT)
        
        tool_calls = iteration.context.get("planned_tool_calls", [])
        
        if not tool_calls:
            return []
        
        # Execute tools
        observations = []
        for call in tool_calls:
            obs = await self.tool_executor.execute_tool(
                call["tool"],
                call["parameters"]
            )
            observations.append(obs)
        
        return observations
    
    async def _observe_phase(self, observations: list, iteration) -> Dict[str, Any]:
        """Execute OBSERVE phase."""
        self.state_manager.update_phase(LoopPhase.OBSERVE)
        
        # Process observations
        for obs_dict in observations:
            # Convert dict to Observation if needed
            if isinstance(obs_dict, dict):
                from .types import Observation
                obs = Observation(
                    tool_name=obs_dict.get("tool", "unknown"),
                    result=obs_dict.get("result"),
                    success=obs_dict.get("success", False),
                    metadata=obs_dict.get("metadata", {}),
                    timestamp=datetime.now()
                )
            else:
                obs = obs_dict
            
            self.observer.process_observation(obs)
        
        # Analyze iteration
        analysis = self.observer.analyze_iteration(iteration)
        
        # Merge observations into context
        self.context_manager.merge_observations_into_context(iteration)
        
        return analysis
    
    async def _decide_phase(self, analysis: Dict[str, Any], iteration) -> bool:
        """Execute DECIDE phase."""
        self.state_manager.update_phase(LoopPhase.DECIDE)
        
        # Check if goal achieved
        if self.decide_handler:
            should_complete = await self.decide_handler(
                self.context.goal,
                analysis,
                self.context_manager.get_context_summary()
            )
        else:
            # Default: check if all observations successful
            should_complete = analysis.get("success_rate", 0) == 1.0
        
        return should_complete
    
    def _generate_result(self) -> Dict[str, Any]:
        """Generate final result."""
        successful_iterations = sum(
            1 for iter in self.context.iterations
            if iter.state == LoopState.COMPLETED
        )
        
        return {
            "success": successful_iterations > 0,
            "agent_id": self.context.agent_id,
            "task_id": self.context.task_id,
            "goal": self.context.goal,
            "total_iterations": len(self.context.iterations),
            "successful_iterations": successful_iterations,
            "final_state": self.context.iterations[-1].state.value if self.context.iterations else "unknown",
            "iterations": [
                self.state_manager.get_iteration_summary()
                for _ in self.context.iterations
            ],
            "context_summary": self.context_manager.get_context_summary()
        }
```

---

### Step 8: Create MCP Integration

**File**: `agents/orchestration/mcp_integration.py`

```python
"""MCP integration for orchestration layer."""

from typing import Dict, Callable, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def get_mcp_tools() -> Dict[str, Callable]:
    """Get all available MCP tools."""
    # This would import from MCP server
    # For now, return empty dict - will be populated from MCP server
    return {}

def create_orchestration_context(
    agent_id: str,
    goal: str,
    task_id: Optional[str] = None,
    max_iterations: int = 50
) -> OrchestrationContext:
    """Create orchestration context from agent parameters."""
    from .types import OrchestrationContext
    
    return OrchestrationContext(
        agent_id=agent_id,
        task_id=task_id,
        goal=goal,
        max_iterations=max_iterations,
        current_iteration=0,
        iterations=[],
        context_data={}
    )
```

---

### Step 9: Create MCP Tool Wrapper

**File**: `agents/apps/agent-mcp/tools/orchestration.py`

```python
"""MCP tools for orchestration layer."""

from mcp.server import Server
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.orchestration.engine import OrchestrationEngine
    from agents.orchestration.types import OrchestrationContext
    from agents.orchestration.mcp_integration import get_mcp_tools, create_orchestration_context
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False

def register_orchestration_tools(server: Server):
    """Register orchestration MCP tools."""
    
    if not ORCHESTRATION_AVAILABLE:
        return
    
    @server.tool()
    async def run_orchestrated_task(
        agent_id: str,
        goal: str,
        task_id: Optional[str] = None,
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Run a task using the orchestration layer.
        
        Args:
            agent_id: Agent identifier
            goal: Goal description
            task_id: Optional task ID
            max_iterations: Maximum loop iterations
        
        Returns:
            Orchestration result
        """
        # Create context
        context = create_orchestration_context(
            agent_id=agent_id,
            goal=goal,
            task_id=task_id,
            max_iterations=max_iterations
        )
        
        # Get MCP tools
        mcp_tools = get_mcp_tools()
        
        # Create engine
        engine = OrchestrationEngine(
            context=context,
            mcp_tools=mcp_tools
        )
        
        # Run orchestration
        result = await engine.run()
        
        return result
```

---

### Step 10: Integration with Monitoring

**File**: `agents/orchestration/monitoring.py`

```python
"""Monitoring integration for orchestration."""

from typing import Dict, Any
from .types import OrchestrationContext
import requests

def log_orchestration_event(
    context: OrchestrationContext,
    event_type: str,
    data: Dict[str, Any]
):
    """Log orchestration event to monitoring system."""
    try:
        requests.post(
            "http://localhost:3001/api/actions",
            json={
                "agent_id": context.agent_id,
                "action_type": f"orchestration_{event_type}",
                "details": {
                    **data,
                    "task_id": context.task_id,
                    "goal": context.goal,
                    "current_iteration": context.current_iteration
                }
            },
            timeout=1.0
        )
    except Exception:
        # Fail silently if monitoring unavailable
        pass
```

---

## Testing Plan

### Unit Tests

1. **Loop State Management**
   - Test iteration tracking
   - Test phase transitions
   - Test error recording

2. **Tool Executor**
   - Test tool execution
   - Test error handling
   - Test parallel execution

3. **Observer**
   - Test observation processing
   - Test goal checking
   - Test context extraction

4. **Error Recovery**
   - Test retry logic
   - Test recovery strategies
   - Test max retries

### Integration Tests

1. **Full Loop**
   - Test complete Think-Act-Observe cycle
   - Test multiple iterations
   - Test goal achievement

2. **Error Scenarios**
   - Test tool failures
   - Test retry logic
   - Test max iterations

3. **MCP Integration**
   - Test with real MCP tools
   - Test tool discovery
   - Test execution flow

---

## Documentation

### User Guide

**File**: `agents/orchestration/README.md`

- Overview of orchestration layer
- How to use orchestration engine
- Integration with agents
- Examples

### API Reference

**File**: `agents/orchestration/API.md`

- Class documentation
- Method signatures
- Type definitions
- Examples

---

## Migration Path

### Phase 1: Implementation (Week 1-2)
- Implement core components
- Unit tests
- Basic integration

### Phase 2: Integration (Week 2-3)
- MCP tool integration
- Monitoring integration
- Agent prompt updates

### Phase 3: Testing (Week 3)
- Integration tests
- Real agent testing
- Performance testing

### Phase 4: Documentation (Week 3)
- User guide
- API reference
- Examples

---

## Success Criteria

1. ✅ Orchestration engine manages Think-Act-Observe loop
2. ✅ Loop state tracked across iterations
3. ✅ Tool execution coordinated
4. ✅ Observations processed systematically
5. ✅ Error recovery works
6. ✅ Integration with MCP tools
7. ✅ Monitoring integration
8. ✅ Documentation complete

---

## LATER: Success Criteria

1. ✅ Orchestration engine manages Think-Act-Observe loop across processes
2. ✅ Loop state tracked in-memory and persisted
3. ✅ Tool execution coordinated across processes
4. ✅ Observations processed systematically
5. ✅ Error recovery works across process boundaries
6. ✅ Integration with A2A protocol
7. ✅ Process lifecycle management
8. ✅ Documentation complete

---

## Migration Path: NOW → LATER

When you can spawn agents dynamically:

1. **Keep file-based state** as fallback/persistence layer
2. **Add in-memory state** for active processes
3. **Add process manager** for spawning/coordinating
4. **Add A2A integration** for cross-process communication
5. **Migrate session engine** to process engine
6. **Add process monitoring** and lifecycle management

---

**Last Updated**: 2025-01-13  
**Status**: 
- **NOW**: Planning Complete - Ready for Session-Based Implementation
- **LATER**: Detailed Plan Preserved - Ready When Dynamic Spawning Available

