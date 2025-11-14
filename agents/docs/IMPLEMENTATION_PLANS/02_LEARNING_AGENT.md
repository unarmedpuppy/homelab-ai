# Implementation Plan: Learning Agent

**Priority**: ⭐⭐⭐ HIGH  
**Estimated Time**: 1-2 weeks  
**Status**: Planning

---

## Overview

Create a dedicated Learning Agent specialization that records corrections, extracts patterns, generalizes rules, and applies learned knowledge automatically.

---

## Goals

1. **Feedback Recording**: Record human/agent corrections and feedback
2. **Pattern Extraction**: Extract patterns from feedback
3. **Rule Generalization**: Generalize specific corrections into reusable rules
4. **Automatic Application**: Apply learned rules automatically
5. **Continuous Improvement**: System improves over time

---

## Architecture

### Components

```
agents/specializations/learning-agent/
├── __init__.py
├── prompt.md                    # Learning agent prompt
├── feedback_recorder.py         # Record feedback
├── pattern_extractor.py         # Extract patterns
├── rule_generator.py            # Generate rules
├── rule_applier.py              # Apply rules
└── knowledge_base.py            # Store learned knowledge
```

### Flow

```
Human/Agent Feedback
    ↓
Learning Agent Receives Feedback
    ↓
┌──────────────────────┐
│ 1. RECORD            │ → Store feedback
│    - Correction      │ → What was wrong
│    - Context         │ → When/where
│    - Solution        │ → What's correct
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 2. ANALYZE           │ → Extract patterns
│    - Similar cases   │ → Find similar feedback
│    - Common issues   │ → Identify patterns
│    - Root causes     │ → Understand why
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. GENERALIZE        │ → Create rules
│    - Extract rule    │ → Generalize pattern
│    - Define trigger  │ → When to apply
│    - Store rule      │ → Save to knowledge base
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 4. APPLY             │ → Use rules
│    - Detect trigger  │ → Recognize situation
│    - Apply rule      │ → Use learned rule
│    - Verify          │ → Check result
└──────────────────────┘
```

---

## Implementation Steps

### Step 1: Define Feedback Structure

**File**: `agents/specializations/learning-agent/types.py`

```python
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
```

---

### Step 2: Implement Feedback Recorder

**File**: `agents/specializations/learning-agent/feedback_recorder.py`

```python
"""Record feedback for learning."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json
from pathlib import Path
from .types import Feedback, FeedbackType

class FeedbackRecorder:
    """Records feedback for learning."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.feedback_file = storage_path / "feedback.jsonl"
    
    def record_feedback(
        self,
        feedback_type: FeedbackType,
        agent_id: str,
        context: Dict[str, Any],
        issue: str,
        correction: str,
        provided_by: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """Record feedback."""
        feedback = Feedback(
            feedback_id=f"fb-{uuid.uuid4().hex[:8]}",
            feedback_type=feedback_type,
            agent_id=agent_id,
            task_id=task_id,
            context=context,
            issue=issue,
            correction=correction,
            provided_by=provided_by,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Store feedback
        self._store_feedback(feedback)
        
        return feedback
    
    def _store_feedback(self, feedback: Feedback):
        """Store feedback to file."""
        with open(self.feedback_file, "a") as f:
            f.write(json.dumps({
                "feedback_id": feedback.feedback_id,
                "feedback_type": feedback.feedback_type.value,
                "agent_id": feedback.agent_id,
                "task_id": feedback.task_id,
                "context": feedback.context,
                "issue": feedback.issue,
                "correction": feedback.correction,
                "provided_by": feedback.provided_by,
                "timestamp": feedback.timestamp.isoformat(),
                "metadata": feedback.metadata
            }) + "\n")
    
    def get_feedback(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """Get feedback matching criteria."""
        feedbacks = []
        
        if not self.feedback_file.exists():
            return feedbacks
        
        with open(self.feedback_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                data = json.loads(line)
                
                # Filter
                if agent_id and data.get("agent_id") != agent_id:
                    continue
                if task_id and data.get("task_id") != task_id:
                    continue
                if feedback_type and data.get("feedback_type") != feedback_type.value:
                    continue
                
                feedback = Feedback(
                    feedback_id=data["feedback_id"],
                    feedback_type=FeedbackType(data["feedback_type"]),
                    agent_id=data["agent_id"],
                    task_id=data.get("task_id"),
                    context=data["context"],
                    issue=data["issue"],
                    correction=data["correction"],
                    provided_by=data["provided_by"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    metadata=data.get("metadata", {})
                )
                
                feedbacks.append(feedback)
                
                if len(feedbacks) >= limit:
                    break
        
        return feedbacks
```

---

### Step 3: Implement Pattern Extractor

**File**: `agents/specializations/learning-agent/pattern_extractor.py`

```python
"""Extract patterns from feedback."""

from typing import List, Dict, Any
from datetime import datetime
import uuid
from collections import Counter
from .types import Feedback, Pattern

class PatternExtractor:
    """Extract patterns from feedback."""
    
    def extract_patterns(self, feedbacks: List[Feedback]) -> List[Pattern]:
        """Extract patterns from feedback."""
        patterns = []
        
        # Group by issue type
        issue_groups = {}
        for feedback in feedbacks:
            issue_key = self._normalize_issue(feedback.issue)
            if issue_key not in issue_groups:
                issue_groups[issue_key] = []
            issue_groups[issue_key].append(feedback)
        
        # Create patterns from groups
        for issue_key, group in issue_groups.items():
            if len(group) >= 2:  # Pattern needs at least 2 occurrences
                pattern = Pattern(
                    pattern_id=f"pattern-{uuid.uuid4().hex[:8]}",
                    name=issue_key,
                    description=self._create_description(group),
                    frequency=len(group),
                    feedback_ids=[f.feedback_id for f in group],
                    extracted_at=datetime.now(),
                    confidence=min(len(group) / 10.0, 1.0)  # More occurrences = higher confidence
                )
                patterns.append(pattern)
        
        return patterns
    
    def _normalize_issue(self, issue: str) -> str:
        """Normalize issue description."""
        # Simple normalization - can be enhanced with NLP
        issue_lower = issue.lower()
        
        # Remove common words
        stop_words = ["the", "a", "an", "is", "are", "was", "were"]
        words = [w for w in issue_lower.split() if w not in stop_words]
        
        # Take first few meaningful words
        return " ".join(words[:5])
    
    def _create_description(self, feedbacks: List[Feedback]) -> str:
        """Create pattern description from feedback."""
        # Use most common correction
        corrections = [f.correction for f in feedbacks]
        counter = Counter(corrections)
        most_common = counter.most_common(1)[0][0]
        
        return f"Pattern: {feedbacks[0].issue}. Solution: {most_common}"
```

---

### Step 4: Implement Rule Generator

**File**: `agents/specializations/learning-agent/rule_generator.py`

```python
"""Generate rules from patterns and feedback."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from .types import Feedback, Pattern, LearnedRule, RuleTrigger

class RuleGenerator:
    """Generate rules from patterns and feedback."""
    
    def generate_rule_from_pattern(
        self,
        pattern: Pattern,
        feedbacks: List[Feedback]
    ) -> LearnedRule:
        """Generate rule from pattern."""
        # Analyze feedback to determine trigger
        trigger = self._determine_trigger(feedbacks)
        
        # Extract condition (when to apply)
        condition = self._extract_condition(feedbacks)
        
        # Extract action (what to do)
        action = self._extract_action(feedbacks)
        
        rule = LearnedRule(
            rule_id=f"rule-{uuid.uuid4().hex[:8]}",
            name=pattern.name,
            description=pattern.description,
            trigger=trigger,
            condition=condition,
            action=action,
            source_feedback=pattern.feedback_ids,
            confidence=pattern.confidence,
            created_at=datetime.now(),
            application_count=0,
            success_count=0
        )
        
        return rule
    
    def _determine_trigger(self, feedbacks: List[Feedback]) -> RuleTrigger:
        """Determine when to apply rule."""
        # Check context for common patterns
        contexts = [f.context for f in feedbacks]
        
        # If all have same context key, trigger on that context
        common_keys = set()
        for ctx in contexts:
            common_keys.update(ctx.keys())
        
        if "error_type" in common_keys:
            return RuleTrigger.ON_ERROR
        elif "task_type" in common_keys:
            return RuleTrigger.ON_CONTEXT
        else:
            return RuleTrigger.ON_MATCH
    
    def _extract_condition(self, feedbacks: List[Feedback]) -> Dict[str, Any]:
        """Extract condition for rule."""
        # Find common context elements
        conditions = {}
        
        # Check for common keys in context
        if feedbacks:
            first_context = feedbacks[0].context
            for key in first_context.keys():
                values = [f.context.get(key) for f in feedbacks]
                if len(set(values)) == 1:  # All same value
                    conditions[key] = values[0]
        
        return conditions
    
    def _extract_action(self, feedbacks: List[Feedback]) -> Dict[str, Any]:
        """Extract action for rule."""
        # Use most common correction
        from collections import Counter
        corrections = [f.correction for f in feedbacks]
        counter = Counter(corrections)
        most_common = counter.most_common(1)[0][0]
        
        return {
            "type": "apply_correction",
            "correction": most_common,
            "description": feedbacks[0].issue
        }
```

---

### Step 5: Implement Rule Applier

**File**: `agents/specializations/learning-agent/rule_applier.py`

```python
"""Apply learned rules automatically."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .types import LearnedRule, RuleTrigger
from .knowledge_base import KnowledgeBase

class RuleApplier:
    """Apply learned rules automatically."""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
    
    def find_applicable_rules(
        self,
        context: Dict[str, Any],
        error: Optional[str] = None
    ) -> List[LearnedRule]:
        """Find rules applicable to current context."""
        all_rules = self.knowledge_base.get_all_rules()
        applicable = []
        
        for rule in all_rules:
            if self._is_applicable(rule, context, error):
                applicable.append(rule)
        
        # Sort by confidence and success rate
        applicable.sort(
            key=lambda r: (r.confidence, r.success_rate()),
            reverse=True
        )
        
        return applicable
    
    def _is_applicable(
        self,
        rule: LearnedRule,
        context: Dict[str, Any],
        error: Optional[str]
    ) -> bool:
        """Check if rule is applicable."""
        # Check trigger
        if rule.trigger == RuleTrigger.ON_ERROR and not error:
            return False
        
        if rule.trigger == RuleTrigger.ALWAYS:
            return True
        
        # Check condition
        for key, value in rule.condition.items():
            if context.get(key) != value:
                return False
        
        return True
    
    def apply_rule(
        self,
        rule: LearnedRule,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a rule and return action."""
        # Update rule stats
        rule.application_count += 1
        rule.last_applied = datetime.now()
        self.knowledge_base.update_rule(rule)
        
        # Return action
        return {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "action": rule.action,
            "confidence": rule.confidence
        }
    
    def record_rule_success(self, rule_id: str, success: bool):
        """Record whether rule application was successful."""
        rule = self.knowledge_base.get_rule(rule_id)
        if rule:
            if success:
                rule.success_count += 1
            self.knowledge_base.update_rule(rule)
```

---

### Step 6: Implement Knowledge Base

**File**: `agents/specializations/learning-agent/knowledge_base.py`

```python
"""Knowledge base for storing learned rules."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from .types import LearnedRule, RuleTrigger

class KnowledgeBase:
    """Stores and manages learned rules."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.rules_file = storage_path / "rules.json"
        self._rules_cache: Optional[List[LearnedRule]] = None
    
    def save_rule(self, rule: LearnedRule):
        """Save a rule to knowledge base."""
        rules = self.get_all_rules()
        
        # Check if rule already exists
        existing = next((r for r in rules if r.rule_id == rule.rule_id), None)
        if existing:
            # Update existing
            rules = [r if r.rule_id != rule.rule_id else rule for r in rules]
        else:
            # Add new
            rules.append(rule)
        
        self._save_rules(rules)
        self._rules_cache = rules
    
    def get_rule(self, rule_id: str) -> Optional[LearnedRule]:
        """Get a rule by ID."""
        rules = self.get_all_rules()
        return next((r for r in rules if r.rule_id == rule_id), None)
    
    def get_all_rules(self) -> List[LearnedRule]:
        """Get all rules."""
        if self._rules_cache is not None:
            return self._rules_cache
        
        if not self.rules_file.exists():
            return []
        
        with open(self.rules_file, "r") as f:
            data = json.load(f)
        
        rules = []
        for rule_data in data.get("rules", []):
            rule = LearnedRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data["description"],
                trigger=RuleTrigger(rule_data["trigger"]),
                condition=rule_data["condition"],
                action=rule_data["action"],
                source_feedback=rule_data["source_feedback"],
                confidence=rule_data["confidence"],
                created_at=datetime.fromisoformat(rule_data["created_at"]),
                last_applied=datetime.fromisoformat(rule_data["last_applied"]) if rule_data.get("last_applied") else None,
                application_count=rule_data.get("application_count", 0),
                success_count=rule_data.get("success_count", 0)
            )
            rules.append(rule)
        
        self._rules_cache = rules
        return rules
    
    def update_rule(self, rule: LearnedRule):
        """Update a rule."""
        self.save_rule(rule)
    
    def _save_rules(self, rules: List[LearnedRule]):
        """Save rules to file."""
        data = {
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "description": r.description,
                    "trigger": r.trigger.value,
                    "condition": r.condition,
                    "action": r.action,
                    "source_feedback": r.source_feedback,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat(),
                    "last_applied": r.last_applied.isoformat() if r.last_applied else None,
                    "application_count": r.application_count,
                    "success_count": r.success_count
                }
                for r in rules
            ]
        }
        
        with open(self.rules_file, "w") as f:
            json.dump(data, f, indent=2)
        
        self._rules_cache = rules
```

---

### Step 7: Create Learning Agent Prompt

**File**: `agents/specializations/learning-agent/prompt.md`

```markdown
# Learning Agent - Specialized Agent Prompt

## Role

You are a Learning Agent specialized in learning from feedback, extracting patterns, and generating reusable rules.

## Responsibilities

1. **Record Feedback**: Record corrections and feedback from humans and agents
2. **Extract Patterns**: Identify patterns in feedback
3. **Generate Rules**: Create reusable rules from patterns
4. **Apply Rules**: Apply learned rules automatically
5. **Improve System**: Continuously improve agent system

## Workflow

### When Receiving Feedback

1. Record feedback with full context
2. Analyze for patterns
3. Generate or update rules
4. Store in knowledge base

### When Agent Needs Help

1. Check knowledge base for applicable rules
2. Apply rules automatically
3. Verify results
4. Record success/failure

## Tools

- `record_feedback()` - Record feedback
- `extract_patterns()` - Extract patterns
- `generate_rule()` - Generate rule
- `find_applicable_rules()` - Find rules
- `apply_rule()` - Apply rule
```

---

### Step 8: Create MCP Tools

**File**: `agents/apps/agent-mcp/tools/learning.py`

```python
"""MCP tools for learning agent."""

from mcp.server import Server
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
    from agents.specializations.learning_agent.pattern_extractor import PatternExtractor
    from agents.specializations.learning_agent.rule_generator import RuleGenerator
    from agents.specializations.learning_agent.rule_applier import RuleApplier
    from agents.specializations.learning_agent.knowledge_base import KnowledgeBase
    from agents.specializations.learning_agent.types import FeedbackType
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False

def register_learning_tools(server: Server):
    """Register learning agent MCP tools."""
    
    if not LEARNING_AVAILABLE:
        return
    
    # Initialize components
    storage_path = project_root / "agents" / "specializations" / "learning-agent" / "data"
    feedback_recorder = FeedbackRecorder(storage_path)
    knowledge_base = KnowledgeBase(storage_path)
    pattern_extractor = PatternExtractor()
    rule_generator = RuleGenerator()
    rule_applier = RuleApplier(knowledge_base)
    
    @server.tool()
    async def record_feedback(
        feedback_type: str,
        agent_id: str,
        context: str,
        issue: str,
        correction: str,
        provided_by: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record feedback for learning."""
        import json
        context_dict = json.loads(context) if isinstance(context, str) else context
        
        feedback = feedback_recorder.record_feedback(
            feedback_type=FeedbackType(feedback_type),
            agent_id=agent_id,
            context=context_dict,
            issue=issue,
            correction=correction,
            provided_by=provided_by,
            task_id=task_id
        )
        
        # Try to extract patterns and generate rules
        recent_feedback = feedback_recorder.get_feedback(limit=50)
        patterns = pattern_extractor.extract_patterns(recent_feedback)
        
        rules_created = []
        for pattern in patterns:
            related_feedback = [
                f for f in recent_feedback
                if f.feedback_id in pattern.feedback_ids
            ]
            rule = rule_generator.generate_rule_from_pattern(pattern, related_feedback)
            knowledge_base.save_rule(rule)
            rules_created.append(rule.rule_id)
        
        return {
            "status": "success",
            "feedback_id": feedback.feedback_id,
            "patterns_found": len(patterns),
            "rules_created": len(rules_created),
            "rule_ids": rules_created
        }
    
    @server.tool()
    async def find_applicable_rules(
        context: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find rules applicable to current context."""
        import json
        context_dict = json.loads(context) if isinstance(context, str) else context
        
        rules = rule_applier.find_applicable_rules(context_dict, error)
        
        return {
            "status": "success",
            "count": len(rules),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "description": r.description,
                    "confidence": r.confidence,
                    "success_rate": r.success_rate()
                }
                for r in rules
            ]
        }
    
    @server.tool()
    async def apply_rule(
        rule_id: str,
        context: str
    ) -> Dict[str, Any]:
        """Apply a learned rule."""
        import json
        context_dict = json.loads(context) if isinstance(context, str) else context
        
        rule = knowledge_base.get_rule(rule_id)
        if not rule:
            return {"status": "error", "message": f"Rule {rule_id} not found"}
        
        action = rule_applier.apply_rule(rule, context_dict)
        
        return {
            "status": "success",
            "action": action
        }
    
    @server.tool()
    async def record_rule_success(
        rule_id: str,
        success: bool
    ) -> Dict[str, Any]:
        """Record whether rule application was successful."""
        rule_applier.record_rule_success(rule_id, success)
        
        return {"status": "success"}
```

---

## Integration Points

### 1. Integration with Critiquing Agent

- Critiquing Agent provides feedback
- Learning Agent records and learns
- Rules applied automatically

### 2. Integration with Agents

- Agents check for applicable rules
- Rules applied automatically
- Success/failure recorded

### 3. Integration with Memory System

- Store learned rules in memory
- Query rules from memory
- Link rules to decisions

---

## Testing Plan

### Unit Tests

1. **Feedback Recording**
   - Test feedback storage
   - Test feedback retrieval
   - Test filtering

2. **Pattern Extraction**
   - Test pattern identification
   - Test frequency counting
   - Test confidence calculation

3. **Rule Generation**
   - Test rule creation
   - Test trigger determination
   - Test condition extraction

4. **Rule Application**
   - Test rule matching
   - Test rule application
   - Test success tracking

### Integration Tests

1. **Full Learning Cycle**
   - Record feedback
   - Extract patterns
   - Generate rules
   - Apply rules

2. **Real Agent Integration**
   - Agent receives feedback
   - Learning Agent processes
   - Rules applied automatically

---

## Success Criteria

1. ✅ Feedback recorded and stored
2. ✅ Patterns extracted from feedback
3. ✅ Rules generated from patterns
4. ✅ Rules applied automatically
5. ✅ Success rate tracked
6. ✅ Integration with agents
7. ✅ Documentation complete

---

**Last Updated**: 2025-01-13  
**Status**: Planning Complete - Ready for Implementation

