"""Quality evaluation for agent outputs."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .types import QualityReport, QualityIssue, IssueSeverity, IssueCategory

class QualityChecker:
    """Evaluates quality of agent outputs."""
    
    def __init__(self, rule_applier=None):
        self.rule_applier = rule_applier
    
    def check_quality(
        self,
        agent_id: str,
        output_type: str,
        output_content: str,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """Check quality of agent output."""
        issues = []
        rules_applied = []
        
        # Apply learned rules if available
        if self.rule_applier and context:
            applicable_rules = self.rule_applier.find_applicable_rules(context)
            for rule in applicable_rules:
                rules_applied.append(rule.rule_id)
                # Check if rule flags an issue
                rule_issues = self._check_rule(rule, output_content, context)
                issues.extend(rule_issues)
        
        # Run standard quality checks
        standard_issues = self._run_standard_checks(output_type, output_content)
        issues.extend(standard_issues)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(issues)
        
        report = QualityReport(
            report_id=f"report-{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            task_id=task_id,
            output_type=output_type,
            output_content=output_content,
            quality_score=quality_score,
            issues=issues,
            rules_applied=rules_applied,
            created_at=datetime.now(),
            reviewed_by="critiquing-agent"
        )
        
        return report
    
    def _run_standard_checks(
        self,
        output_type: str,
        output_content: str
    ) -> List[QualityIssue]:
        """Run standard quality checks."""
        issues = []
        
        # Code quality checks
        if output_type == "code":
            issues.extend(self._check_code_quality(output_content))
        
        # Documentation checks
        if output_type == "documentation":
            issues.extend(self._check_documentation_quality(output_content))
        
        # Plan checks
        if output_type == "plan":
            issues.extend(self._check_plan_quality(output_content))
        
        return issues
    
    def _check_code_quality(self, code: str) -> List[QualityIssue]:
        """Check code quality."""
        issues = []
        
        # Check for common issues
        if "TODO" in code or "FIXME" in code:
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.CODE_QUALITY,
                description="Code contains TODO or FIXME comments",
                location=None,
                suggestion="Complete or remove TODO/FIXME comments",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        # Check for error handling
        if "try:" in code and "except:" not in code:
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.CODE_QUALITY,
                description="Try block without except clause",
                location=None,
                suggestion="Add proper exception handling",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _check_documentation_quality(self, doc: str) -> List[QualityIssue]:
        """Check documentation quality."""
        issues = []
        
        # Check for minimum length
        if len(doc) < 100:
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.LOW,
                category=IssueCategory.DOCUMENTATION,
                description="Documentation is very short",
                location=None,
                suggestion="Add more detail to documentation",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _check_plan_quality(self, plan: str) -> List[QualityIssue]:
        """Check plan quality."""
        issues = []
        
        # Check for required sections
        required_sections = ["Overview", "Steps", "Testing"]
        for section in required_sections:
            if section not in plan:
                issues.append(QualityIssue(
                    issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.DOCUMENTATION,
                    description=f"Plan missing {section} section",
                    location=None,
                    suggestion=f"Add {section} section to plan",
                    rule_applied=None,
                    detected_at=datetime.now()
                ))
        
        return issues
    
    def _check_rule(
        self,
        rule,
        output_content: str,
        context: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Check if rule flags an issue."""
        issues = []
        
        # Apply rule and check result
        action = self.rule_applier.apply_rule(rule, context)
        
        # If rule action indicates an issue, create issue
        if action.get("action", {}).get("type") == "flag_issue":
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.CODE_QUALITY,
                description=action.get("action", {}).get("description", "Rule flagged issue"),
                location=None,
                suggestion=action.get("action", {}).get("suggestion", "Apply rule correction"),
                rule_applied=rule.rule_id,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _calculate_quality_score(self, issues: List[QualityIssue]) -> float:
        """Calculate quality score from issues."""
        if not issues:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            IssueSeverity.CRITICAL: 0.5,
            IssueSeverity.HIGH: 0.3,
            IssueSeverity.MEDIUM: 0.15,
            IssueSeverity.LOW: 0.05
        }
        
        total_penalty = sum(
            severity_weights.get(issue.severity, 0.1)
            for issue in issues
        )
        
        # Score is 1.0 minus penalty (capped at 0.0)
        score = max(0.0, 1.0 - total_penalty)
        
        return score

