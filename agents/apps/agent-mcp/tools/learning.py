"""Learning Agent Tools for MCP Server

Provides tools for recording feedback, extracting patterns, generating rules, and applying learned knowledge.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging

# Try to import learning agent modules
try:
    from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
    from agents.specializations.learning_agent.pattern_extractor import PatternExtractor
    from agents.specializations.learning_agent.rule_generator import RuleGenerator
    from agents.specializations.learning_agent.rule_applier import RuleApplier
    from agents.specializations.learning_agent.knowledge_base import KnowledgeBase
    from agents.specializations.learning_agent.types import FeedbackType
    LEARNING_AVAILABLE = True
except ImportError as e:
    LEARNING_AVAILABLE = False
    print(f"⚠️  Warning: Learning Agent modules not available: {e}")


def register_learning_tools(server: Server):
    """Register learning agent MCP tools."""
    
    if not LEARNING_AVAILABLE:
        return
    
    # Initialize components
    storage_path = project_root / "agents" / "specializations" / "learning_agent" / "data"
    feedback_recorder = FeedbackRecorder(storage_path)
    knowledge_base = KnowledgeBase(storage_path)
    pattern_extractor = PatternExtractor()
    rule_generator = RuleGenerator()
    rule_applier = RuleApplier(knowledge_base)
    
    @server.tool()
    @with_automatic_logging()
    async def record_feedback(
        feedback_type: str,
        agent_id: str,
        context: str,
        issue: str,
        correction: str,
        provided_by: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record feedback for learning.
        
        Args:
            feedback_type: Type of feedback (correction, improvement, confirmation, rejection)
            agent_id: ID of agent that received feedback
            context: JSON string with context (task_type, error_type, etc.)
            issue: What was wrong or needs improvement
            correction: What should be done correctly
            provided_by: Who provided feedback ("human" or agent_id)
            task_id: Optional task ID
        
        Returns:
            Feedback recording result with pattern extraction and rule generation info
        """
        try:
            # Parse context
            context_dict = json.loads(context) if isinstance(context, str) else context
            
            # Validate feedback type
            try:
                fb_type = FeedbackType(feedback_type.lower())
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid feedback_type: {feedback_type}. Must be one of: correction, improvement, confirmation, rejection"
                }
            
            # Record feedback
            feedback = feedback_recorder.record_feedback(
                feedback_type=fb_type,
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
            
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in context parameter"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def find_applicable_rules(
        context: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find rules applicable to current context.
        
        Args:
            context: JSON string with current context (task_type, error_type, etc.)
            error: Optional error message if error occurred
        
        Returns:
            List of applicable rules sorted by confidence and success rate
        """
        try:
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
                        "success_rate": r.success_rate(),
                        "trigger": r.trigger.value,
                        "condition": r.condition,
                        "action": r.action
                    }
                    for r in rules
                ]
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in context parameter"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def apply_rule(
        rule_id: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Apply a learned rule.
        
        Args:
            rule_id: ID of rule to apply
            context: JSON string with current context
        
        Returns:
            Rule application result with action to take
        """
        try:
            context_dict = json.loads(context) if isinstance(context, str) else context
            
            rule = knowledge_base.get_rule(rule_id)
            if not rule:
                return {
                    "status": "error",
                    "message": f"Rule {rule_id} not found"
                }
            
            action = rule_applier.apply_rule(rule, context_dict)
            
            return {
                "status": "success",
                "action": action
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in context parameter"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def record_rule_success(
        rule_id: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        Record whether rule application was successful.
        
        Args:
            rule_id: ID of rule that was applied
            success: Whether rule application was successful
        
        Returns:
            Success recording result
        """
        try:
            rule_applier.record_rule_success(rule_id, success)
            
            return {
                "status": "success",
                "message": f"Rule {rule_id} success recorded: {success}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def get_learning_stats() -> Dict[str, Any]:
        """
        Get statistics about the learning system.
        
        Returns:
            Statistics about feedback, patterns, and rules
        """
        try:
            all_feedback = feedback_recorder.get_feedback(limit=1000)
            all_rules = knowledge_base.get_all_rules()
            
            # Extract patterns for stats
            patterns = pattern_extractor.extract_patterns(all_feedback)
            
            # Calculate rules by trigger
            from agents.specializations.learning_agent.types import RuleTrigger
            rules_by_trigger = {}
            if all_rules:
                for trigger in RuleTrigger:
                    rules_by_trigger[trigger.value] = sum(1 for r in all_rules if r.trigger == trigger)
            
            return {
                "status": "success",
                "stats": {
                    "total_feedback": len(all_feedback),
                    "total_rules": len(all_rules),
                    "total_patterns": len(patterns),
                    "rules_by_trigger": rules_by_trigger,
                    "average_rule_confidence": sum(r.confidence for r in all_rules) / len(all_rules) if all_rules else 0.0,
                    "rules_with_success": sum(1 for r in all_rules if r.success_rate() > 0) if all_rules else 0
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

