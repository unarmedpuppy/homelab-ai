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

