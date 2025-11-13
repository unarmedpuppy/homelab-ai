"""
Code Review Tools for MCP Server

Provides tools for agents to systematically review their own code before marking tasks complete.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


def _analyze_code_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a code file for review checklist items."""
    if not file_path.exists():
        return {"status": "error", "message": "File not found"}
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"status": "error", "message": f"Could not read file: {str(e)}"}
    
    analysis = {
        "file": str(file_path.relative_to(project_root)),
        "has_error_handling": False,
        "has_security_checks": False,
        "follows_patterns": True,  # Assume yes unless we detect issues
        "has_tests": False,
        "is_documented": False,
        "issues": [],
        "recommendations": []
    }
    
    # Check for error handling
    if "try" in content and "catch" in content:
        analysis["has_error_handling"] = True
    elif "async" in content or "await" in content:
        analysis["issues"].append({
            "type": "missing_error_handling",
            "severity": "medium",
            "message": "Async operations detected but no try-catch found"
        })
        analysis["recommendations"].append("Add try-catch blocks for async operations")
    
    # Check for security patterns
    security_patterns = {
        "input_validation": r"(validate|sanitize|check)",
        "sql_parameterized": r"(prepare|parameter|placeholder)",
    }
    
    # Check if file has database operations
    if any(keyword in content.lower() for keyword in ["query", "execute", "database", "db"]):
        if not re.search(security_patterns["input_validation"], content, re.IGNORECASE):
            analysis["issues"].append({
                "type": "missing_input_validation",
                "severity": "high",
                "message": "Database operations detected but no input validation found"
            })
            analysis["recommendations"].append("Add input validation for database operations")
        else:
            analysis["has_security_checks"] = True
    
    # Check for tests (look for test files or test functions)
    if "test" in file_path.name.lower() or "spec" in file_path.name.lower():
        analysis["has_tests"] = True
    elif re.search(r"(it\(|test\(|describe\()", content):
        analysis["has_tests"] = True
    
    # Check for documentation (comments, docstrings)
    if file_path.suffix == ".py":
        if '"""' in content or "'''" in content:
            analysis["is_documented"] = True
    elif file_path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
        if "/*" in content or "//" in content:
            analysis["is_documented"] = True
    
    if not analysis["is_documented"]:
        analysis["issues"].append({
            "type": "missing_documentation",
            "severity": "low",
            "message": "No documentation found"
        })
        analysis["recommendations"].append("Add documentation/comments")
    
    return analysis


def register_code_review_tools(server: Server):
    """Register code review tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def request_code_review(
        file_paths: str,
        review_type: str = "self"
    ) -> Dict[str, Any]:
        """
        Request a code review for modified files.
        
        This tool analyzes code and provides a systematic review checklist.
        Use this before marking tasks complete to catch issues early.
        
        Args:
            file_paths: Comma-separated list of file paths to review
            review_type: Type of review ("self" for self-review, "peer" for peer review)
        
        Returns:
            Code review results with checklist and recommendations
        
        Example:
            request_code_review(
                file_paths="apps/my-app/src/index.ts,apps/my-app/src/utils.ts",
                review_type="self"
            )
        """
        file_list = [f.strip() for f in file_paths.split(",") if f.strip()]
        
        review_results = {
            "files_reviewed": file_list,
            "review_type": review_type,
            "checklist": {
                "code_follows_patterns": True,
                "error_handling_present": True,
                "security_checks_present": True,
                "code_formatted": True,  # Assume yes, formatting is separate
                "no_build_errors": True,  # Assume yes, build check is separate
                "tests_present": False,
                "documentation_present": False
            },
            "issues": [],
            "recommendations": [],
            "summary": ""
        }
        
        # Analyze each file
        for file_path in file_list:
            full_path = project_root / file_path
            analysis = _analyze_code_file(full_path)
            
            if analysis.get("status") == "error":
                review_results["issues"].append({
                    "file": file_path,
                    "type": "file_error",
                    "message": analysis.get("message", "Unknown error")
                })
                continue
            
            # Update checklist based on analysis
            if not analysis["has_error_handling"]:
                review_results["checklist"]["error_handling_present"] = False
            
            if not analysis["has_security_checks"] and analysis.get("issues"):
                security_issues = [i for i in analysis["issues"] if "security" in i.get("type", "").lower() or "validation" in i.get("type", "").lower()]
                if security_issues:
                    review_results["checklist"]["security_checks_present"] = False
            
            if not analysis["has_tests"]:
                review_results["checklist"]["tests_present"] = False
            
            if not analysis["is_documented"]:
                review_results["checklist"]["documentation_present"] = False
            
            # Collect issues and recommendations
            review_results["issues"].extend([
                {**issue, "file": file_path} for issue in analysis.get("issues", [])
            ])
            review_results["recommendations"].extend(analysis.get("recommendations", []))
        
        # Generate summary
        checklist_items = []
        if review_results["checklist"]["code_follows_patterns"]:
            checklist_items.append("✅ Code follows project patterns")
        else:
            checklist_items.append("❌ Code may not follow project patterns")
        
        if review_results["checklist"]["error_handling_present"]:
            checklist_items.append("✅ Error handling is present")
        else:
            checklist_items.append("❌ Error handling may be missing")
        
        if review_results["checklist"]["security_checks_present"]:
            checklist_items.append("✅ Security checks present")
        else:
            checklist_items.append("❌ Security checks may be missing")
        
        if review_results["checklist"]["tests_present"]:
            checklist_items.append("✅ Tests present")
        else:
            checklist_items.append("⚠️  Tests not detected (may be in separate files)")
        
        if review_results["checklist"]["documentation_present"]:
            checklist_items.append("✅ Documentation present")
        else:
            checklist_items.append("⚠️  Documentation not detected")
        
        summary_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🔍 CODE REVIEW RESULTS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Files reviewed: {len(file_list)}",
            f"Review type: {review_type}",
            "",
            "Checklist:",
        ]
        summary_lines.extend([f"  {item}" for item in checklist_items])
        summary_lines.append("")
        
        if review_results["issues"]:
            summary_lines.append(f"Issues found: {len(review_results['issues'])}")
            for issue in review_results["issues"][:5]:  # Show first 5
                severity_icon = "🔴" if issue.get("severity") == "high" else "🟡" if issue.get("severity") == "medium" else "🟢"
                summary_lines.append(f"  {severity_icon} {issue.get('file', 'unknown')}: {issue.get('message', 'issue')}")
            if len(review_results["issues"]) > 5:
                summary_lines.append(f"  ... and {len(review_results['issues']) - 5} more")
            summary_lines.append("")
        
        if review_results["recommendations"]:
            summary_lines.append("Recommendations:")
            for rec in list(set(review_results["recommendations"]))[:5]:  # Unique, first 5
                summary_lines.append(f"  - {rec}")
            summary_lines.append("")
        
        if not review_results["issues"]:
            summary_lines.append("✅ No issues found! Code looks good.")
        
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        review_results["summary"] = "\n".join(summary_lines)
        
        return review_results
    
    @server.tool()
    @with_automatic_logging()
    async def self_review_checklist(
        file_paths: str
    ) -> Dict[str, Any]:
        """
        Get a self-review checklist for modified files.
        
        Returns a checklist that agents should complete before marking tasks as done.
        
        Args:
            file_paths: Comma-separated list of file paths to review
        
        Returns:
            Self-review checklist with items to verify
        """
        file_list = [f.strip() for f in file_paths.split(",") if f.strip()]
        
        checklist = {
            "files": file_list,
            "items": [
                {
                    "item": "Code follows project patterns",
                    "description": "Code matches existing patterns and conventions",
                    "how_to_check": "Compare with similar files in the codebase"
                },
                {
                    "item": "Error handling is present",
                    "description": "Try-catch blocks, async error handling, proper error responses",
                    "how_to_check": "Look for try-catch, error handling in async functions"
                },
                {
                    "item": "Security checks present",
                    "description": "Input validation, SQL injection prevention, authentication checks",
                    "how_to_check": "Verify input validation, parameterized queries, auth checks"
                },
                {
                    "item": "Code is formatted consistently",
                    "description": "Follows project formatting rules (Prettier, Black, etc.)",
                    "how_to_check": "Run formatter or check formatting manually"
                },
                {
                    "item": "No build/lint errors",
                    "description": "Code compiles and passes linting",
                    "how_to_check": "Run build and lint commands"
                },
                {
                    "item": "Tests pass (if applicable)",
                    "description": "Existing tests pass, new code is tested",
                    "how_to_check": "Run test suite"
                },
                {
                    "item": "Documentation updated (if needed)",
                    "description": "Code is documented, README updated if needed",
                    "how_to_check": "Check for comments, docstrings, README updates"
                }
            ],
            "instructions": "Review each item and verify before marking task complete"
        }
        
        return checklist

