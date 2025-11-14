# Implementation Plan: Transparency & Guardrails

**Priority**: ⭐⭐ MEDIUM  
**Estimated Time**: 1-2 weeks  
**Status**: Planning

---

## Overview

Enhance transparency in agent reasoning and implement guardrails for safety and policy enforcement.

---

## Goals

1. **Reasoning Transparency**: Show agent reasoning process
2. **Human Feedback**: Structured feedback mechanism
3. **Guardrails System**: Safety checks before actions
4. **Policy Enforcement**: Enforce policies automatically
5. **Expert Consultation**: Connect to domain experts

---

## Architecture

### Components

```
agents/safety/
├── __init__.py
├── guardrails.py      # Guardrails system
├── policies.py        # Policy definitions
├── checker.py         # Safety checker
└── transparency.py    # Reasoning transparency
```

---

## Implementation Steps

### Step 1: Implement Guardrails

**File**: `agents/safety/guardrails.py`

```python
"""Guardrails system for agent safety."""

from typing import Dict, List, Any, Optional
from enum import Enum

class GuardrailAction(Enum):
    """Actions guardrails can take."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"

class Guardrail:
    """Represents a guardrail."""
    
    def __init__(
        self,
        guardrail_id: str,
        name: str,
        description: str,
        check_function: callable,
        action: GuardrailAction
    ):
        self.guardrail_id = guardrail_id
        self.name = name
        self.description = description
        self.check_function = check_function
        self.action = action
    
    def check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check guardrail."""
        try:
            result = self.check_function(context)
            return {
                "guardrail_id": self.guardrail_id,
                "name": self.name,
                "passed": result,
                "action": self.action.value if result else GuardrailAction.BLOCK.value
            }
        except Exception as e:
            return {
                "guardrail_id": self.guardrail_id,
                "name": self.name,
                "passed": False,
                "error": str(e),
                "action": GuardrailAction.BLOCK.value
            }

class GuardrailsSystem:
    """Guardrails system."""
    
    def __init__(self):
        self.guardrails: List[Guardrail] = []
        self._load_default_guardrails()
    
    def _load_default_guardrails(self):
        """Load default guardrails."""
        # Dangerous command guardrail
        self.guardrails.append(Guardrail(
            guardrail_id="dangerous-commands",
            name="Dangerous Commands",
            description="Block dangerous system commands",
            check_function=self._check_dangerous_commands,
            action=GuardrailAction.BLOCK
        ))
        
        # Direct server changes guardrail
        self.guardrails.append(Guardrail(
            guardrail_id="direct-server-changes",
            name="Direct Server Changes",
            description="Require approval for direct server changes",
            check_function=self._check_direct_changes,
            action=GuardrailAction.REQUIRE_APPROVAL
        ))
    
    def _check_dangerous_commands(self, context: Dict[str, Any]) -> bool:
        """Check for dangerous commands."""
        dangerous = ["rm -rf", "format", "delete all", "drop database"]
        command = context.get("command", "").lower()
        return not any(d in command for d in dangerous)
    
    def _check_direct_changes(self, context: Dict[str, Any]) -> bool:
        """Check if change is direct (not via Git)."""
        # If change is via Git workflow, allow
        if context.get("via_git", False):
            return True
        # Otherwise require approval
        return context.get("approved", False)
    
    def check_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check all guardrails."""
        results = []
        blocked = False
        
        for guardrail in self.guardrails:
            result = guardrail.check(context)
            results.append(result)
            
            if result["action"] == "block":
                blocked = True
        
        return {
            "passed": not blocked,
            "guardrails_checked": len(results),
            "results": results
        }
```

---

### Step 2: Implement Transparency

**File**: `agents/safety/transparency.py`

```python
"""Reasoning transparency for agents."""

from typing import Dict, List, Any, Optional
from datetime import datetime

class ReasoningLogger:
    """Logs agent reasoning for transparency."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def log_reasoning(
        self,
        agent_id: str,
        task_id: Optional[str],
        phase: str,
        reasoning: str,
        context: Dict[str, Any]
    ):
        """Log agent reasoning."""
        log_entry = {
            "agent_id": agent_id,
            "task_id": task_id,
            "phase": phase,
            "reasoning": reasoning,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store to file
        log_file = self.storage_path / f"{agent_id}-reasoning.jsonl"
        with open(log_file, "a") as f:
            import json
            f.write(json.dumps(log_entry) + "\n")
    
    def get_reasoning_trail(
        self,
        agent_id: str,
        task_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get reasoning trail for agent/task."""
        log_file = self.storage_path / f"{agent_id}-reasoning.jsonl"
        
        if not log_file.exists():
            return []
        
        entries = []
        with open(log_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                import json
                entry = json.loads(line)
                if not task_id or entry.get("task_id") == task_id:
                    entries.append(entry)
        
        return entries
```

---

## Integration Points

### 1. Integration with Orchestration

- Check guardrails before tool execution
- Log reasoning at each phase
- Block unsafe actions

### 2. Integration with Agents

- Agents see reasoning logs
- Guardrails prevent unsafe actions
- Policies enforced automatically

---

## Success Criteria

1. ✅ Guardrails check actions
2. ✅ Reasoning logged transparently
3. ✅ Policies enforced
4. ✅ Integration complete
5. ✅ Documentation complete

---

**Last Updated**: 2025-01-13  
**Status**: Planning Complete - Ready for Implementation

