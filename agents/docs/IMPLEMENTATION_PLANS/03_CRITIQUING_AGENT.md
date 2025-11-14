# Implementation Plan: Critiquing Agent

**Priority**: ⭐⭐⭐ HIGH  
**Estimated Time**: 1-2 weeks  
**Status**: Planning

---

## Overview

Create a dedicated Critiquing Agent specialization that reviews agent outputs, flags issues, applies learned rules, and provides quality control.

---

## Goals

1. **Quality Review**: Review agent outputs systematically
2. **Issue Detection**: Flag problems automatically
3. **Rule Application**: Apply learned rules from Learning Agent
4. **Feedback Generation**: Provide actionable feedback
5. **Quality Assurance**: Ensure consistent quality

---

## Architecture

### Components

```
agents/specializations/critiquing-agent/
├── __init__.py
├── prompt.md                    # Critiquing agent prompt
├── quality_checker.py           # Quality evaluation
├── issue_detector.py            # Detect issues
├── rule_applier.py             # Apply learned rules
└── feedback_generator.py       # Generate feedback
```

### Flow

```
Agent Output
    ↓
Critiquing Agent Receives
    ↓
┌──────────────────────┐
│ 1. REVIEW             │ → Analyze output
│    - Check quality    │ → Evaluate
│    - Check rules      │ → Apply learned rules
│    - Check standards  │ → Compare to standards
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 2. DETECT            │ → Find issues
│    - Identify problems│ → Flag issues
│    - Categorize      │ → Classify issues
│    - Prioritize      │ → Rank by severity
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. APPLY RULES       │ → Use learned rules
│    - Check rules     │ → Find applicable rules
│    - Apply rules     │ → Use rules
│    - Verify          │ → Check results
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 4. GENERATE FEEDBACK │ → Provide feedback
│    - Create feedback │ → Write feedback
│    - Send to agent   │ → Communicate
│    - Record          │ → Store for learning
└──────────────────────┘
```

---

## Implementation Steps

### Step 1: Define Quality Metrics

**File**: `agents/specializations/critiquing-agent/types.py`

```python
"""Type definitions for critiquing agent."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class IssueSeverity(Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"  # Must fix
    HIGH = "high"  # Should fix
    MEDIUM = "medium"  # Consider fixing
    LOW = "low"  # Nice to fix

class IssueCategory(Enum):
    """Categories of issues."""
    CODE_QUALITY = "code_quality"
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"

@dataclass
class QualityIssue:
    """Represents a quality issue found."""
    issue_id: str
    severity: IssueSeverity
    category: IssueCategory
    description: str
    location: Optional[str]  # File, line, etc.
    suggestion: str  # How to fix
    rule_applied: Optional[str]  # Rule ID if rule applied
    detected_at: datetime

@dataclass
class QualityReport:
    """Quality report for agent output."""
    report_id: str
    agent_id: str
    task_id: Optional[str]
    output_type: str  # "code", "documentation", "plan", etc.
    output_content: str
    quality_score: float  # 0.0 to 1.0
    issues: List[QualityIssue]
    rules_applied: List[str]
    created_at: datetime
    reviewed_by: str  # "critiquing-agent"
```

---

### Step 2: Implement Quality Checker

**File**: `agents/specializations/critiquing-agent/quality_checker.py`

```python
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
```

---

### Step 3: Implement Issue Detector

**File**: `agents/specializations/critiquing-agent/issue_detector.py`

```python
"""Detect issues in agent outputs."""

from typing import List, Dict, Any
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
```

---

### Step 4: Implement Feedback Generator

**File**: `agents/specializations/critiquing-agent/feedback_generator.py`

```python
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
            from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
            from pathlib import Path
            import sys
            
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            storage_path = project_root / "agents" / "specializations" / "learning-agent" / "data"
            recorder = FeedbackRecorder(storage_path)
            
            # Record each issue as feedback
            for issue in report.issues:
                recorder.record_feedback(
                    feedback_type="correction",
                    agent_id=report.agent_id,
                    context={
                        "output_type": report.output_type,
                        "task_id": report.task_id
                    },
                    issue=issue.description,
                    correction=issue.suggestion,
                    provided_by="critiquing-agent"
                )
        except Exception:
            # Fail silently if learning agent unavailable
            pass
```

---

### Step 5: Create Critiquing Agent Prompt

**File**: `agents/specializations/critiquing-agent/prompt.md`

```markdown
# Critiquing Agent - Specialized Agent Prompt

## Role

You are a Critiquing Agent specialized in quality control, issue detection, and providing constructive feedback.

## Responsibilities

1. **Review Outputs**: Review agent outputs systematically
2. **Detect Issues**: Identify problems and quality issues
3. **Apply Rules**: Apply learned rules from Learning Agent
4. **Generate Feedback**: Provide actionable feedback
5. **Ensure Quality**: Maintain consistent quality standards

## Workflow

### When Reviewing Output

1. Analyze output for quality
2. Check against learned rules
3. Detect issues systematically
4. Generate feedback
5. Send to agent
6. Record for learning

## Tools

- `review_output()` - Review agent output
- `check_quality()` - Check quality
- `detect_issues()` - Detect issues
- `generate_feedback()` - Generate feedback
```

---

### Step 6: Create MCP Tools

**File**: `agents/apps/agent-mcp/tools/critiquing.py`

```python
"""MCP tools for critiquing agent."""

from mcp.server import Server
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.specializations.critiquing_agent.quality_checker import QualityChecker
    from agents.specializations.critiquing_agent.issue_detector import IssueDetector
    from agents.specializations.critiquing_agent.feedback_generator import FeedbackGenerator
    from agents.specializations.learning_agent.rule_applier import RuleApplier
    from agents.specializations.learning_agent.knowledge_base import KnowledgeBase
    CRITIQUING_AVAILABLE = True
except ImportError:
    CRITIQUING_AVAILABLE = False

def register_critiquing_tools(server: Server):
    """Register critiquing agent MCP tools."""
    
    if not CRITIQUING_AVAILABLE:
        return
    
    # Initialize components
    learning_storage = project_root / "agents" / "specializations" / "learning-agent" / "data"
    knowledge_base = KnowledgeBase(learning_storage)
    rule_applier = RuleApplier(knowledge_base)
    
    quality_checker = QualityChecker(rule_applier)
    issue_detector = IssueDetector()
    feedback_generator = FeedbackGenerator()
    
    @server.tool()
    async def review_agent_output(
        agent_id: str,
        output_type: str,
        output_content: str,
        task_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Review agent output and provide feedback."""
        import json
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
    
    @server.tool()
    async def check_output_quality(
        output_type: str,
        output_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check quality of output without full review."""
        import json
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
```

---

## Integration Points

### 1. Integration with Learning Agent

- Receive learned rules
- Apply rules automatically
- Record issues for learning

### 2. Integration with Agents

- Agents request reviews
- Automatic reviews on output
- Feedback sent to agents

### 3. Integration with Communication

- Send feedback via messages
- Priority based on severity
- Track feedback delivery

---

## Testing Plan

### Unit Tests

1. **Quality Checking**
   - Test quality evaluation
   - Test score calculation
   - Test rule application

2. **Issue Detection**
   - Test issue detection
   - Test categorization
   - Test severity assignment

3. **Feedback Generation**
   - Test feedback creation
   - Test message formatting
   - Test recommendations

### Integration Tests

1. **Full Review Cycle**
   - Review output
   - Detect issues
   - Generate feedback
   - Send to agent

2. **Rule Application**
   - Apply learned rules
   - Verify rule application
   - Track success

---

## Success Criteria

1. ✅ Outputs reviewed systematically
2. ✅ Issues detected automatically
3. ✅ Rules applied from Learning Agent
4. ✅ Feedback generated and sent
5. ✅ Quality scores calculated
6. ✅ Integration with agents
7. ✅ Documentation complete

---

**Last Updated**: 2025-01-13  
**Status**: Planning Complete - Ready for Implementation

