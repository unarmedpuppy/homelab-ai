"""
Quality Check Tools for MCP Server

Provides tools for agents to automatically check code quality after making edits.
This addresses the issue where agents leave errors behind without catching them.
"""

import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


def _detect_project_type(file_path: Path) -> Optional[str]:
    """Detect project type based on file structure."""
    # Check for common project indicators
    if (file_path / "package.json").exists():
        return "node"
    elif (file_path / "requirements.txt").exists() or (file_path / "pyproject.toml").exists():
        return "python"
    elif (file_path / "Cargo.toml").exists():
        return "rust"
    elif (file_path / "go.mod").exists():
        return "go"
    return None


def _check_typescript_errors(file_paths: List[str]) -> Dict[str, Any]:
    """Check for TypeScript errors in modified files."""
    errors = []
    warnings = []
    
    # Find TypeScript projects
    ts_projects = set()
    for file_path in file_paths:
        path = Path(file_path)
        # Find nearest tsconfig.json
        for parent in path.parents:
            if (parent / "tsconfig.json").exists():
                ts_projects.add(parent)
                break
    
    for project_dir in ts_projects:
        try:
            # Run tsc --noEmit to check for errors
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # Parse TypeScript errors
                for line in result.stderr.split("\n"):
                    if "error TS" in line:
                        errors.append({
                            "file": str(project_dir.relative_to(project_root)),
                            "error": line.strip()
                        })
                    elif "warning TS" in line:
                        warnings.append({
                            "file": str(project_dir.relative_to(project_root)),
                            "warning": line.strip()
                        })
        except subprocess.TimeoutExpired:
            errors.append({
                "file": str(project_dir.relative_to(project_root)),
                "error": "TypeScript check timed out"
            })
        except Exception as e:
            # TypeScript not available or other error
            pass
    
    return {
        "errors": errors,
        "warnings": warnings,
        "has_errors": len(errors) > 0,
        "has_warnings": len(warnings) > 0
    }


def _check_python_errors(file_paths: List[str]) -> Dict[str, Any]:
    """Check for Python syntax/lint errors."""
    errors = []
    warnings = []
    
    # Filter Python files
    python_files = [f for f in file_paths if f.endswith(".py")]
    
    for file_path in python_files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
        
        try:
            # Check syntax with compile
            with open(full_path, "r", encoding="utf-8") as f:
                compile(f.read(), file_path, "exec")
        except SyntaxError as e:
            errors.append({
                "file": file_path,
                "line": e.lineno,
                "error": f"SyntaxError: {e.msg}"
            })
        except Exception:
            pass
        
        # Try running pylint or flake8 if available
        try:
            result = subprocess.run(
                ["python", "-m", "pylint", "--errors-only", file_path],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                for line in result.stdout.split("\n"):
                    if ":" in line and "error" in line.lower():
                        errors.append({
                            "file": file_path,
                            "error": line.strip()
                        })
        except Exception:
            # Linter not available
            pass
    
    return {
        "errors": errors,
        "warnings": warnings,
        "has_errors": len(errors) > 0,
        "has_warnings": len(warnings) > 0
    }


def _check_error_handling(file_paths: List[str]) -> Dict[str, Any]:
    """Check for missing error handling patterns."""
    issues = []
    
    # Patterns to check
    risky_patterns = {
        "async_without_try_catch": r"async\s+(def|function)\s+\w+.*?:\s*(?!.*try)",
        "database_call_no_error": r"(prisma|db|database)\.\w+\([^)]*\)(?!.*catch)",
        "api_call_no_error": r"(fetch|axios|request)\([^)]*\)(?!.*catch)",
    }
    
    for file_path in file_paths:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
        
        # Only check code files
        if not any(full_path.suffix in [".py", ".ts", ".tsx", ".js", ".jsx"]):
            continue
        
        try:
            content = full_path.read_text(encoding="utf-8")
            
            # Check for async functions without try-catch
            async_funcs = re.findall(r"async\s+(def|function)\s+(\w+)", content)
            for match in async_funcs:
                func_name = match[1]
                # Check if function has try-catch
                func_pattern = rf"async\s+(def|function)\s+{func_name}.*?{{(.*?)}}"
                func_match = re.search(func_pattern, content, re.DOTALL)
                if func_match and "try" not in func_match.group(2):
                    issues.append({
                        "file": file_path,
                        "type": "missing_error_handling",
                        "message": f"Async function '{func_name}' may need error handling",
                        "severity": "medium"
                    })
        except Exception:
            pass
    
    return {
        "issues": issues,
        "has_issues": len(issues) > 0,
        "count": len(issues)
    }


def _check_security_patterns(file_paths: List[str]) -> Dict[str, Any]:
    """Check for common security issues."""
    issues = []
    
    security_patterns = {
        "sql_injection": [
            r"query\([^)]*\+.*\)",  # String concatenation in queries
            r"execute\([^)]*\+.*\)",  # String concatenation in execute
        ],
        "no_input_validation": [
            r"(req\.(body|query|params)\.\w+)(?!.*validate)",  # No validation before use
        ],
        "hardcoded_secrets": [
            r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded secrets
        ],
    }
    
    for file_path in file_paths:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
        
        # Only check code files
        if not any(full_path.suffix in [".py", ".ts", ".tsx", ".js", ".jsx"]):
            continue
        
        try:
            content = full_path.read_text(encoding="utf-8")
            
            # Check for SQL injection patterns
            for pattern in security_patterns["sql_injection"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues.append({
                        "file": file_path,
                        "type": "potential_sql_injection",
                        "message": "Potential SQL injection: String concatenation in query",
                        "severity": "high",
                        "line": content[:match.start()].count("\n") + 1
                    })
            
            # Check for hardcoded secrets
            for pattern in security_patterns["hardcoded_secrets"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues.append({
                        "file": file_path,
                        "type": "hardcoded_secret",
                        "message": "Potential hardcoded secret detected",
                        "severity": "high",
                        "line": content[:match.start()].count("\n") + 1
                    })
        except Exception:
            pass
    
    return {
        "issues": issues,
        "has_issues": len(issues) > 0,
        "count": len(issues)
    }


def register_quality_check_tools(server: Server):
    """Register quality check tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def check_code_quality(
        file_paths: str,
        check_types: str = "all"
    ) -> Dict[str, Any]:
        """
        Check code quality for modified files.
        
        This tool runs quality checks on files to catch errors, missing error handling,
        and security issues immediately after edits.
        
        Args:
            file_paths: Comma-separated list of file paths to check
            check_types: Types of checks to run (comma-separated: "build,lint,errors,security,handling" or "all")
        
        Returns:
            Quality check results with errors, warnings, and recommendations
        
        Example:
            check_code_quality(
                file_paths="apps/my-app/src/index.ts,apps/my-app/src/utils.ts",
                check_types="all"
            )
        """
        file_list = [f.strip() for f in file_paths.split(",") if f.strip()]
        check_list = [c.strip() for c in check_types.split(",")] if check_types != "all" else ["build", "lint", "errors", "security", "handling"]
        
        results = {
            "files_checked": file_list,
            "checks_performed": [],
            "errors": [],
            "warnings": [],
            "security_issues": [],
            "error_handling_issues": [],
            "has_errors": False,
            "has_warnings": False,
            "has_issues": False,
            "recommendations": []
        }
        
        # Check TypeScript errors
        if "errors" in check_list or "build" in check_list or "all" in check_list:
            ts_results = _check_typescript_errors(file_list)
            if ts_results["has_errors"]:
                results["errors"].extend(ts_results["errors"])
                results["has_errors"] = True
            if ts_results["has_warnings"]:
                results["warnings"].extend(ts_results["warnings"])
                results["has_warnings"] = True
            results["checks_performed"].append("typescript_errors")
        
        # Check Python errors
        if "errors" in check_list or "lint" in check_list or "all" in check_list:
            py_results = _check_python_errors(file_list)
            if py_results["has_errors"]:
                results["errors"].extend(py_results["errors"])
                results["has_errors"] = True
            if py_results["has_warnings"]:
                results["warnings"].extend(py_results["warnings"])
                results["has_warnings"] = True
            results["checks_performed"].append("python_errors")
        
        # Check error handling
        if "handling" in check_list or "all" in check_list:
            handling_results = _check_error_handling(file_list)
            if handling_results["has_issues"]:
                results["error_handling_issues"].extend(handling_results["issues"])
                results["has_issues"] = True
            results["checks_performed"].append("error_handling")
        
        # Check security patterns
        if "security" in check_list or "all" in check_list:
            security_results = _check_security_patterns(file_list)
            if security_results["has_issues"]:
                results["security_issues"].extend(security_results["issues"])
                results["has_issues"] = True
            results["checks_performed"].append("security_patterns")
        
        # Generate recommendations
        if results["has_errors"]:
            results["recommendations"].append("Fix TypeScript/Python errors before proceeding")
        
        if results["has_warnings"]:
            results["recommendations"].append("Review warnings - they may indicate issues")
        
        if results["security_issues"]:
            high_severity = [i for i in results["security_issues"] if i.get("severity") == "high"]
            if high_severity:
                results["recommendations"].append("URGENT: Fix security issues immediately")
        
        if results["error_handling_issues"]:
            results["recommendations"].append("Consider adding error handling for async operations")
        
        # Format summary
        summary_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📋 QUALITY CHECK RESULTS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Files checked: {len(file_list)}",
            f"Checks performed: {', '.join(results['checks_performed'])}",
            ""
        ]
        
        if results["has_errors"]:
            summary_lines.append(f"❌ Errors: {len(results['errors'])}")
            for error in results["errors"][:5]:  # Show first 5
                summary_lines.append(f"   - {error.get('file', 'unknown')}: {error.get('error', 'error')}")
            if len(results["errors"]) > 5:
                summary_lines.append(f"   ... and {len(results['errors']) - 5} more")
            summary_lines.append("")
        
        if results["has_warnings"]:
            summary_lines.append(f"⚠️  Warnings: {len(results['warnings'])}")
            summary_lines.append("")
        
        if results["security_issues"]:
            summary_lines.append(f"🔒 Security Issues: {len(results['security_issues'])}")
            for issue in results["security_issues"][:3]:  # Show first 3
                summary_lines.append(f"   - {issue.get('file', 'unknown')}: {issue.get('message', 'issue')}")
            summary_lines.append("")
        
        if results["error_handling_issues"]:
            summary_lines.append(f"⚠️  Error Handling: {len(results['error_handling_issues'])} potential issues")
            summary_lines.append("")
        
        if not results["has_errors"] and not results["has_warnings"] and not results["has_issues"]:
            summary_lines.append("✅ No issues found!")
        else:
            summary_lines.append("💡 Recommendations:")
            for rec in results["recommendations"]:
                summary_lines.append(f"   - {rec}")
        
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        results["summary"] = "\n".join(summary_lines)
        
        return results
    
    @server.tool()
    @with_automatic_logging()
    async def check_build_errors(
        project_path: str = "."
    ) -> Dict[str, Any]:
        """
        Check for build errors in a project.
        
        Detects project type and runs appropriate build check.
        
        Args:
            project_path: Path to project directory (relative to repo root)
        
        Returns:
            Build check results
        """
        project_dir = project_root / project_path
        
        if not project_dir.exists():
            return {
                "status": "error",
                "message": f"Project path not found: {project_path}"
            }
        
        project_type = _detect_project_type(project_dir)
        
        if project_type == "node":
            # Try npm/pnpm build
            try:
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    return {
                        "status": "error",
                        "has_errors": True,
                        "output": result.stderr,
                        "message": "Build failed"
                    }
                else:
                    return {
                        "status": "success",
                        "has_errors": False,
                        "message": "Build successful"
                    }
            except subprocess.TimeoutExpired:
                return {
                    "status": "timeout",
                    "message": "Build check timed out"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Could not run build: {str(e)}"
                }
        
        return {
            "status": "unknown",
            "message": f"Unknown project type or build system not detected"
        }

