"""Detect issues in agent outputs."""

from typing import List, Dict, Any, Optional
from .types import QualityIssue, IssueSeverity, IssueCategory
from datetime import datetime
import uuid
import re

class IssueDetector:
    """Detects issues in agent outputs."""
    
    def detect_issues(
        self,
        output_type: str,
        output_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[QualityIssue]:
        """Detect issues in output."""
        issues = []
        
        # Type-specific detection
        if output_type == "code":
            issues.extend(self._detect_code_issues(output_content))
        elif output_type == "documentation":
            issues.extend(self._detect_documentation_issues(output_content))
        elif output_type == "plan":
            issues.extend(self._detect_plan_issues(output_content))
        
        # General issues
        issues.extend(self._detect_general_issues(output_content))
        
        return issues
    
    def _detect_code_issues(self, code: str) -> List[QualityIssue]:
        """Detect code-specific issues."""
        issues = []
        
        # Check for hardcoded values
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                description="Hardcoded password detected",
                location=None,
                suggestion="Use environment variables or secure storage",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        # Check for SQL injection risks
        if re.search(r'execute\s*\([^)]*\+', code, re.IGNORECASE):
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.SECURITY,
                description="Potential SQL injection risk",
                location=None,
                suggestion="Use parameterized queries",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _detect_documentation_issues(self, doc: str) -> List[QualityIssue]:
        """Detect documentation issues."""
        issues = []
        
        # Check for examples
        if "example" not in doc.lower() and "usage" not in doc.lower():
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.LOW,
                category=IssueCategory.DOCUMENTATION,
                description="Documentation missing examples",
                location=None,
                suggestion="Add usage examples",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _detect_plan_issues(self, plan: str) -> List[QualityIssue]:
        """Detect plan issues."""
        issues = []
        
        # Check for testing section
        if "test" not in plan.lower() and "testing" not in plan.lower():
            issues.append(QualityIssue(
                issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.TESTING,
                description="Plan missing testing strategy",
                location=None,
                suggestion="Add testing section to plan",
                rule_applied=None,
                detected_at=datetime.now()
            ))
        
        return issues
    
    def _detect_general_issues(self, content: str) -> List[QualityIssue]:
        """Detect general issues."""
        issues = []
        
        # Check for placeholder text
        placeholders = ["TODO", "FIXME", "XXX", "HACK"]
        for placeholder in placeholders:
            if placeholder in content:
                issues.append(QualityIssue(
                    issue_id=f"issue-{uuid.uuid4().hex[:8]}",
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.CODE_QUALITY,
                    description=f"Content contains {placeholder} placeholder",
                    location=None,
                    suggestion=f"Complete or remove {placeholder}",
                    rule_applied=None,
                    detected_at=datetime.now()
                ))
        
        return issues

