"""Generate feedback from quality reports."""

from typing import Dict, Any, List
from .types import QualityReport, QualityIssue, IssueSeverity

class FeedbackGenerator:
    """Generates feedback from quality reports."""
    
    def generate_feedback(
        self,
        report: QualityReport,
        send_to_agent: bool = True
    ) -> Dict[str, Any]:
        """Generate feedback from quality report."""
        feedback = {
            "report_id": report.report_id,
            "agent_id": report.agent_id,
            "task_id": report.task_id,
            "quality_score": report.quality_score,
            "summary": self._generate_summary(report),
            "issues": self._format_issues(report.issues),
            "recommendations": self._generate_recommendations(report),
            "rules_applied": report.rules_applied
        }
        
        # Send to agent if requested
        if send_to_agent:
            self._send_to_agent(report.agent_id, feedback)
        
        # Record for learning
        self._record_for_learning(report)
        
        return feedback
    
    def _generate_summary(self, report: QualityReport) -> str:
        """Generate summary of quality report."""
        critical_count = sum(1 for i in report.issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in report.issues if i.severity == IssueSeverity.HIGH)
        
        summary = f"Quality Score: {report.quality_score:.2f}/1.0\n"
        summary += f"Total Issues: {len(report.issues)}\n"
        summary += f"Critical: {critical_count}, High: {high_count}\n"
        
        if report.quality_score >= 0.9:
            summary += "✅ Quality is excellent"
        elif report.quality_score >= 0.7:
            summary += "⚠️ Quality is good but has some issues"
        else:
            summary += "❌ Quality needs improvement"
        
        return summary
    
    def _format_issues(self, issues: List[QualityIssue]) -> List[Dict[str, Any]]:
        """Format issues for feedback."""
        return [
            {
                "severity": issue.severity.value,
                "category": issue.category.value,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "location": issue.location,
                "rule_applied": issue.rule_applied
            }
            for issue in sorted(issues, key=lambda i: (
                i.severity.value == "critical",
                i.severity.value == "high",
                i.severity.value == "medium",
                i.severity.value == "low"
            ), reverse=True)
        ]
    
    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Critical issues first
        critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"Fix {len(critical_issues)} critical issue(s) immediately")
        
        # High priority issues
        high_issues = [i for i in report.issues if i.severity == IssueSeverity.HIGH]
        if high_issues:
            recommendations.append(f"Address {len(high_issues)} high priority issue(s)")
        
        # Category-specific recommendations
        categories = {}
        for issue in report.issues:
            cat = issue.category.value
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        for category, count in categories.items():
            if count > 0:
                recommendations.append(f"Review {category} ({count} issue(s))")
        
        return recommendations
    
    def _send_to_agent(self, agent_id: str, feedback: Dict[str, Any]):
        """Send feedback to agent via communication protocol."""
        # Use agent communication protocol
        try:
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from agents.communication import send_agent_message
            send_agent_message(
                from_agent="critiquing-agent",
                to_agent=agent_id,
                type="notification",
                priority="high" if feedback["quality_score"] < 0.7 else "medium",
                subject="Quality Review Feedback",
                content=self._format_feedback_message(feedback)
            )
        except Exception:
            # Fail silently if communication unavailable
            pass
    
    def _format_feedback_message(self, feedback: Dict[str, Any]) -> str:
        """Format feedback as message."""
        message = f"# Quality Review Feedback\n\n"
        message += f"{feedback['summary']}\n\n"
        message += f"## Issues Found\n\n"
        
        for issue in feedback["issues"]:
            message += f"### {issue['severity'].upper()}: {issue['description']}\n"
            message += f"**Suggestion**: {issue['suggestion']}\n\n"
        
        if feedback["recommendations"]:
            message += f"## Recommendations\n\n"
            for rec in feedback["recommendations"]:
                message += f"- {rec}\n"
        
        return message
    
    def _record_for_learning(self, report: QualityReport):
        """Record issues for learning agent."""
        # Send to learning agent for pattern extraction
        try:
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
            from agents.specializations.learning_agent.types import FeedbackType
            
            storage_path = project_root / "agents" / "specializations" / "learning_agent" / "data"
            recorder = FeedbackRecorder(storage_path)
            
            # Record each issue as feedback
            for issue in report.issues:
                recorder.record_feedback(
                    feedback_type=FeedbackType.CORRECTION,
                    agent_id=report.agent_id,
                    context={
                        "output_type": report.output_type,
                        "task_id": report.task_id,
                        "issue_category": issue.category.value
                    },
                    issue=issue.description,
                    correction=issue.suggestion,
                    provided_by="critiquing-agent"
                )
        except Exception:
            # Fail silently if learning agent unavailable
            pass

