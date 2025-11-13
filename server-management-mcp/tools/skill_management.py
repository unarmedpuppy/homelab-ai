"""
Skill Management Tools for MCP Server

Provides tools for agents to propose new skills and manage skill proposals.
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


def register_skill_management_tools(server: Server):
    """Register skill management tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def propose_skill(
        name: str,
        description: str,
        category: str,
        use_cases: str,
        workflow_steps: str,
        mcp_tools_required: str,
        examples: str = "",
        prerequisites: str = "",
        related_skills: str = ""
    ) -> Dict[str, Any]:
        """
        Propose a new skill for the skills library.
        
        Args:
            name: Skill name (kebab-case, e.g., "rollback-deployment")
            description: Brief description of what the skill does
            category: Skill category (deployment, troubleshooting, maintenance, configuration)
            use_cases: When to use this skill (clear use cases)
            workflow_steps: Step-by-step workflow using MCP tools
            mcp_tools_required: Comma-separated list of MCP tools needed
            examples: Real-world examples (optional)
            prerequisites: What's needed before using this skill (optional)
            related_skills: Related skills to reference (optional)
        
        Returns:
            Skill proposal info and file path
        """
        # Create proposals directory
        proposals_dir = project_root / "server-management-skills" / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse MCP tools
        tools_list = [t.strip() for t in mcp_tools_required.split(',')]
        
        # Create skill proposal
        proposal_content = f"""---
name: {name}
description: {description}
category: {category}
status: proposal
proposed_date: {datetime.now().strftime("%Y-%m-%d")}
mcp_tools_required:
{chr(10).join(f'  - {tool}' for tool in tools_list)}
prerequisites:
{chr(10).join(f'  - {p.strip()}' for p in prerequisites.split(',')) if prerequisites else '  - None'}
---

# Skill Proposal: {name}

## Description

{description}

## Category

{category}

## When to Use This Skill

{use_cases}

## Workflow Steps

{workflow_steps}

## MCP Tools Required

{chr(10).join(f'- `{tool}`' for tool in tools_list)}

## Examples

{examples if examples else "No examples provided"}

## Prerequisites

{prerequisites if prerequisites else "None"}

## Related Skills

{related_skills if related_skills else "None"}

## Status

**Status**: PROPOSAL
**Proposed Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Next Steps**: Review and test workflow

## Review Notes

_Review notes will be added here_

---

**Proposal Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        # Write proposal file
        proposal_path = proposals_dir / f"{name}.md"
        proposal_path.write_text(proposal_content)
        
        # Update proposals index if it exists
        index_path = proposals_dir / "README.md"
        if index_path.exists():
            index_content = index_path.read_text()
        else:
            index_content = """# Skill Proposals

List of skill proposals awaiting review.

## Proposals

"""
        
        # Add to index
        new_entry = f"### `{name}`\n- **Category**: {category}\n- **Status**: PROPOSAL\n- **Proposed**: {datetime.now().strftime('%Y-%m-%d')}\n- **File**: `proposals/{name}.md`\n\n"
        
        if "## Proposals" in index_content:
            index_content = index_content.replace("## Proposals", f"## Proposals\n\n{new_entry}")
        else:
            index_content += new_entry
        
        index_path.write_text(index_content)
        
        return {
            "status": "success",
            "skill_name": name,
            "proposal_path": str(proposal_path.relative_to(project_root)),
            "message": f"Skill proposal created: {name}. Ready for review."
        }
    
    @server.tool()
    @with_automatic_logging()
    async def list_skill_proposals(
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List skill proposals.
        
        Args:
            category: Filter by category (optional)
            status: Filter by status (optional)
        
        Returns:
            List of skill proposals
        """
        proposals_dir = project_root / "server-management-skills" / "proposals"
        
        if not proposals_dir.exists():
            return {
                "status": "success",
                "count": 0,
                "proposals": []
            }
        
        proposals = []
        for proposal_file in proposals_dir.glob("*.md"):
            if proposal_file.name == "README.md":
                continue
            
            try:
                content = proposal_file.read_text()
                # Simple parsing (can be improved)
                if "name:" in content:
                    proposals.append({
                        "name": proposal_file.stem,
                        "file": str(proposal_file.relative_to(project_root)),
                        "status": "proposal"
                    })
            except Exception:
                continue
        
        # Filter by category/status if provided
        if category or status:
            # Would need to parse YAML frontmatter for proper filtering
            # For now, return all
            pass
        
        return {
            "status": "success",
            "count": len(proposals),
            "proposals": proposals
        }
    
    @server.tool()
    @with_automatic_logging()
    async def query_skills(
        category: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query existing skills.
        
        Args:
            category: Filter by category (optional)
            search_text: Search in skill names/descriptions (optional)
            limit: Maximum results
        
        Returns:
            List of matching skills
        """
        skills_dir = project_root / "server-management-skills"
        
        if not skills_dir.exists():
            return {
                "status": "success",
                "count": 0,
                "skills": []
            }
        
        skills = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name in ["proposals", ".git"]:
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            try:
                content = skill_file.read_text()
                # Simple parsing
                if "name:" in content:
                    # Extract name from frontmatter
                    name_line = [l for l in content.split('\n') if l.startswith('name:')]
                    skill_name = name_line[0].split('name:')[1].strip() if name_line else skill_dir.name
                    
                    # Extract category
                    category_line = [l for l in content.split('\n') if l.startswith('category:')]
                    skill_category = category_line[0].split('category:')[1].strip() if category_line else "unknown"
                    
                    # Filter
                    if category and category.lower() not in skill_category.lower():
                        continue
                    
                    if search_text and search_text.lower() not in content.lower():
                        continue
                    
                    skills.append({
                        "name": skill_name,
                        "category": skill_category,
                        "path": str(skill_file.relative_to(project_root))
                    })
            except Exception:
                continue
        
        # Limit results
        skills = skills[:limit]
        
        return {
            "status": "success",
            "count": len(skills),
            "skills": skills
        }
    
    @server.tool()
    @with_automatic_logging()
    async def analyze_patterns_for_skills(
        min_frequency: int = 3,
        severity: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze patterns in memory and identify candidates for skill creation.
        
        Args:
            min_frequency: Minimum frequency threshold (default: 3)
            severity: Filter by severity (low, medium, high) - optional
            limit: Maximum patterns to analyze (default: 10)
        
        Returns:
            List of pattern candidates with skill proposal suggestions
        """
        try:
            # Import memory system
            from agents.memory import get_memory
            
            memory = get_memory()
            
            # Query patterns
            patterns = memory.query_patterns(
                severity=severity,
                min_frequency=1,  # Get all patterns, filter later
                limit=limit * 2  # Get more to filter
            )
            
            # Filter candidates
            candidates = []
            for pattern in patterns:
                # Convert Row to dict if needed
                if hasattr(pattern, 'keys'):
                    pattern = dict(pattern)
                
                # Check frequency
                frequency = pattern.get("frequency", 0)
                if frequency < min_frequency:
                    continue
                
                # Check for solution
                solution = pattern.get("solution", "") or ""
                if not solution or len(solution) < 50:
                    continue
                
                # Check severity if specified
                if severity and pattern.get("severity", "").lower() != severity.lower():
                    continue
                
                # Get tags (may be stored as comma-separated string or list)
                tags = pattern.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',') if t.strip()]
                
                # Analyze solution for MCP tools
                mcp_tools = _extract_mcp_tools_from_text(solution)
                
                # Check if solution has workflow steps
                has_workflow = _has_workflow_structure(solution)
                
                candidates.append({
                    "pattern_name": pattern.get("name", ""),
                    "pattern_id": pattern.get("id"),
                    "frequency": frequency,
                    "severity": pattern.get("severity", ""),
                    "description": pattern.get("description", ""),
                    "solution": solution[:200] + "..." if len(solution) > 200 else solution,
                    "mcp_tools_found": mcp_tools,
                    "has_workflow": has_workflow,
                    "skill_suggestion": _suggest_skill_name(pattern.get("name", "")),
                    "category_suggestion": _suggest_category(tags, solution)
                })
            
            # Sort by frequency (descending)
            candidates.sort(key=lambda x: x["frequency"], reverse=True)
            candidates = candidates[:limit]
            
            return {
                "status": "success",
                "count": len(candidates),
                "candidates": candidates,
                "message": f"Found {len(candidates)} pattern(s) suitable for skill creation"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def auto_propose_skill_from_pattern(
        pattern_name: str,
        category: Optional[str] = None,
        review_required: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically create a skill proposal from a pattern.
        
        Args:
            pattern_name: Name of pattern to convert
            category: Skill category (optional, auto-detected if not provided)
            review_required: Require human review (default: True)
        
        Returns:
            Skill proposal details and file path
        """
        try:
            # Import memory system
            from agents.memory import get_memory
            
            memory = get_memory()
            
            # Find pattern
            patterns = memory.query_patterns(limit=100)
            pattern = None
            for p in patterns:
                # Convert Row to dict if needed
                if hasattr(p, 'keys'):
                    p = dict(p)
                
                if p.get("name", "").lower() == pattern_name.lower():
                    pattern = p
                    break
            
            if not pattern:
                return {
                    "status": "error",
                    "message": f"Pattern '{pattern_name}' not found"
                }
            
            # Extract information
            pattern_id = pattern.get("id")
            description = pattern.get("description", "") or ""
            solution = pattern.get("solution", "") or ""
            frequency = pattern.get("frequency", 0)
            severity = pattern.get("severity", "")
            tags = pattern.get("tags", [])
            
            # Handle tags (may be string or list)
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            
            # Generate skill name
            skill_name = _suggest_skill_name(pattern_name)
            
            # Auto-detect category if not provided
            if not category:
                category = _suggest_category(tags, solution)
            
            # Extract MCP tools from solution
            mcp_tools = _extract_mcp_tools_from_text(solution)
            
            # Generate workflow steps from solution
            workflow_steps = _generate_workflow_steps(solution, mcp_tools)
            
            # Generate use cases from description
            use_cases = _generate_use_cases(description, solution)
            
            # Create skill proposal
            proposal_result = await propose_skill(
                name=skill_name,
                description=f"Auto-generated from pattern: {pattern_name}. {description}",
                category=category,
                use_cases=use_cases,
                workflow_steps=workflow_steps,
                mcp_tools_required=", ".join(mcp_tools) if mcp_tools else "See workflow steps",
                examples=f"Pattern frequency: {frequency}, Severity: {severity}",
                prerequisites="See pattern prerequisites",
                related_skills=""
            )
            
            # Update proposal with pattern reference
            if proposal_result.get("status") == "success":
                proposal_path = project_root / proposal_result["proposal_path"]
                if proposal_path.exists():
                    content = proposal_path.read_text()
                    
                    # Add pattern reference to frontmatter
                    if "---" in content:
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml
                            metadata = yaml.safe_load(parts[1])
                            metadata["source_pattern"] = pattern_name
                            metadata["pattern_id"] = pattern_id
                            metadata["pattern_frequency"] = frequency
                            metadata["auto_generated"] = True
                            metadata["review_required"] = review_required
                            
                            # Rewrite with pattern reference
                            new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{parts[2]}"
                            proposal_path.write_text(new_content)
            
            return {
                "status": "success",
                "skill_name": skill_name,
                "pattern_name": pattern_name,
                "pattern_frequency": frequency,
                "proposal_path": proposal_result.get("proposal_path"),
                "message": f"Skill proposal '{skill_name}' auto-generated from pattern '{pattern_name}'",
                "review_required": review_required
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }


# Helper functions

def _extract_mcp_tools_from_text(text: str) -> List[str]:
    """Extract MCP tool names from text."""
    import re
    
    # Common MCP tool patterns
    tool_patterns = [
        r'(\w+_container_status)',
        r'(\w+_restart_container)',
        r'(\w+_view_logs)',
        r'(\w+_deploy)',
        r'(\w+_status)',
        r'(\w+_check_\w+)',
        r'(\w+_query_\w+)',
        r'(\w+_record_\w+)',
        r'(get_\w+)',
        r'(check_\w+)',
        r'(read_file)',
        r'(write_file)',
        r'(docker_\w+)',
        r'(git_\w+)',
        r'(memory_\w+)',
    ]
    
    tools = set()
    for pattern in tool_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        tools.update(matches)
    
    # Filter out common false positives
    false_positives = {'status', 'check', 'get', 'read', 'write'}
    tools = {t for t in tools if t.lower() not in false_positives}
    
    return sorted(list(tools))


def _has_workflow_structure(text: str) -> bool:
    """Check if text has workflow structure (numbered steps, etc.)."""
    import re
    
    # Check for numbered steps
    numbered_steps = re.findall(r'\d+\.\s+', text)
    if len(numbered_steps) >= 2:
        return True
    
    # Check for bullet points with actions
    action_words = ['use', 'call', 'check', 'verify', 'update', 'restart', 'deploy']
    action_count = sum(1 for word in action_words if word.lower() in text.lower())
    if action_count >= 3:
        return True
    
    return False


def _suggest_skill_name(pattern_name: str) -> str:
    """Suggest skill name from pattern name."""
    # Convert to kebab-case
    name = pattern_name.lower()
    name = name.replace(' ', '-')
    name = name.replace('_', '-')
    
    # Remove common prefixes/suffixes
    name = name.replace('pattern-', '')
    name = name.replace('-pattern', '')
    name = name.replace('resolution', 'resolve')
    name = name.replace('troubleshooting', 'troubleshoot')
    
    # Ensure it starts with verb if possible
    if not any(name.startswith(verb) for verb in ['resolve', 'troubleshoot', 'deploy', 'check', 'manage']):
        # Try to add verb
        if 'conflict' in name:
            name = f"resolve-{name}"
        elif 'failure' in name or 'error' in name:
            name = f"troubleshoot-{name}"
        elif 'deployment' in name:
            name = f"deploy-{name}"
    
    return name


def _suggest_category(tags: List[str], solution: str) -> str:
    """Suggest skill category from tags and solution."""
    # Check tags first
    tag_lower = [t.lower() for t in tags]
    
    if any(t in tag_lower for t in ['deployment', 'deploy', 'git']):
        return "deployment"
    elif any(t in tag_lower for t in ['troubleshoot', 'debug', 'error', 'failure']):
        return "troubleshooting"
    elif any(t in tag_lower for t in ['config', 'configuration', 'setup']):
        return "configuration"
    elif any(t in tag_lower for t in ['monitor', 'health', 'status']):
        return "monitoring"
    elif any(t in tag_lower for t in ['maintenance', 'cleanup', 'optimize']):
        return "maintenance"
    
    # Check solution text
    solution_lower = solution.lower()
    
    if any(word in solution_lower for word in ['deploy', 'git', 'commit', 'push']):
        return "deployment"
    elif any(word in solution_lower for word in ['troubleshoot', 'debug', 'error', 'log']):
        return "troubleshooting"
    elif any(word in solution_lower for word in ['config', 'docker-compose', 'port']):
        return "configuration"
    elif any(word in solution_lower for word in ['monitor', 'health', 'status', 'check']):
        return "monitoring"
    
    return "maintenance"  # Default


def _generate_workflow_steps(solution: str, mcp_tools: List[str]) -> str:
    """Generate workflow steps from solution text."""
    import re
    
    # Try to extract numbered steps
    steps = re.findall(r'\d+\.\s+(.+?)(?=\d+\.|$)', solution, re.DOTALL)
    
    if steps:
        workflow = "## Workflow Steps\n\n"
        for i, step in enumerate(steps, 1):
            step_clean = step.strip()
            # Replace tool mentions with code formatting
            for tool in mcp_tools:
                step_clean = re.sub(
                    rf'\b{tool}\b',
                    f'`{tool}()`',
                    step_clean,
                    flags=re.IGNORECASE
                )
            workflow += f"{i}. {step_clean}\n\n"
        return workflow
    
    # Fallback: create steps from solution
    workflow = "## Workflow Steps\n\n"
    workflow += "Based on the pattern solution:\n\n"
    workflow += solution
    workflow += "\n\n**Note**: This workflow was auto-generated. Please review and refine the steps."
    
    return workflow


def _generate_use_cases(description: str, solution: str) -> str:
    """Generate use cases from description and solution."""
    use_cases = "## When to Use This Skill\n\n"
    use_cases += f"Use this skill when: {description}\n\n"
    use_cases += "**Common scenarios**:\n"
    use_cases += "- When the pattern described above occurs\n"
    use_cases += "- When you need to apply the documented solution\n"
    use_cases += "\n**Note**: This use case was auto-generated from a pattern. Please review and add specific scenarios."
    
    return use_cases

