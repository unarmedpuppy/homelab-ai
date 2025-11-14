"""Knowledge base for storing learned rules."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
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

