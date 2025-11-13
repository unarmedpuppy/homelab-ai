"""
Skill Management Tools for MCP Server

Provides tools for agents to propose new skills and manage skill proposals.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server


def register_skill_management_tools(server: Server):
    """Register skill management tools with MCP server."""
    
    @server.tool()
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

