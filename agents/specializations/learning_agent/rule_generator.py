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

