"""Critiquing Agent Tools for MCP Server

Provides tools for reviewing agent outputs, detecting issues, and providing quality feedback.
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

# Try to import critiquing agent modules
try:
    from agents.specializations.critiquing_agent.quality_checker import QualityChecker
    from agents.specializations.critiquing_agent.issue_detector import IssueDetector
    from agents.specializations.critiquing_agent.feedback_generator import FeedbackGenerator
    from agents.specializations.learning_agent.rule_applier import RuleApplier
    from agents.specializations.learning_agent.knowledge_base import KnowledgeBase
    CRITIQUING_AVAILABLE = True
except ImportError as e:
    CRITIQUING_AVAILABLE = False
    print(f"⚠️  Warning: Critiquing Agent modules not available: {e}")


def register_critiquing_tools(server: Server):
    """Register critiquing agent MCP tools."""
    
    if not CRITIQUING_AVAILABLE:
        return
    
    # Initialize components
    learning_storage = project_root / "agents" / "specializations" / "learning_agent" / "data"
    knowledge_base = KnowledgeBase(learning_storage)
    rule_applier = RuleApplier(knowledge_base)
    
    quality_checker = QualityChecker(rule_applier)
    issue_detector = IssueDetector()
    feedback_generator = FeedbackGenerator()
    
    @server.tool()
    @with_automatic_logging()
    async def review_agent_output(
        agent_id: str,
        output_type: str,
        output_content: str,
        task_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review agent output and provide feedback.
        
        Args:
            agent_id: ID of agent that produced output
            output_type: Type of output (code, documentation, plan, etc.)
            output_content: The output content to review
            task_id: Optional task ID
            context: Optional JSON string with context (task_type, error_type, etc.)
        
        Returns:
            Quality report with issues and feedback
        """
        try:
            context_dict = json.loads(context) if isinstance(context, str) else context or {}
            
            # Check quality
            report = quality_checker.check_quality(
                agent_id=agent_id,
                output_type=output_type,
                output_content=output_content,
                task_id=task_id,
                context=context_dict
            )
            
            # Generate feedback
            feedback = feedback_generator.generate_feedback(report, send_to_agent=True)
            
            return {
                "status": "success",
                "report_id": report.report_id,
                "quality_score": report.quality_score,
                "issues_count": len(report.issues),
                "feedback": feedback
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
    async def check_output_quality(
        output_type: str,
        output_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check quality of output without full review.
        
        Args:
            output_type: Type of output (code, documentation, plan, etc.)
            output_content: The output content to check
            context: Optional JSON string with context
        
        Returns:
            Quick quality check with issues found
        """
        try:
            context_dict = json.loads(context) if isinstance(context, str) else context or {}
            
            # Detect issues
            issues = issue_detector.detect_issues(
                output_type=output_type,
                output_content=output_content,
                context=context_dict
            )
            
            return {
                "status": "success",
                "issues_count": len(issues),
                "issues": [
                    {
                        "severity": i.severity.value,
                        "category": i.category.value,
                        "description": i.description,
                        "suggestion": i.suggestion
                    }
                    for i in issues
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

