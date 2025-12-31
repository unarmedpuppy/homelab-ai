"""Skill discovery and execution tools.

This is the core of the skill-based agent architecture. Instead of hardcoding
capabilities as Python functions, the agent discovers and uses skills from
the agents/skills/ directory - the same skills used by human operators.

Tools:
- list_skills: List all available skills with descriptions
- read_skill: Read a skill's SKILL.md content
- search_skills: Search skills by keyword

The agent workflow:
1. Receive task
2. Call list_skills to see available capabilities
3. Call read_skill for relevant skill(s)
4. Follow the instructions in the skill using run_shell and file tools
5. Complete the task
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

from .registry import register_tool

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Skills directory - can be overridden for different deployments
# In Docker, this should be mounted from the host
SKILLS_DIR = os.getenv(
    "AGENT_SKILLS_DIR",
    "/app/agents/skills"  # Default for Docker mount
)

# Fallback for local development
if not os.path.exists(SKILLS_DIR):
    # Try relative to this file
    _local_skills = Path(__file__).parent.parent.parent.parent / "agents" / "skills"
    if _local_skills.exists():
        SKILLS_DIR = str(_local_skills)


# =============================================================================
# YAML Frontmatter Parser
# =============================================================================

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from skill markdown.
    
    Returns:
        (frontmatter_dict, content_without_frontmatter)
    """
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                # Simple YAML parsing (key: value format)
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip()
                body = parts[2].strip()
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
    
    return frontmatter, body


def get_skill_info(skill_path: Path) -> Optional[dict]:
    """
    Get skill information from its SKILL.md file.
    
    Returns dict with: name, description, when_to_use, script, path
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None
    
    try:
        content = skill_md.read_text()
        frontmatter, _ = parse_frontmatter(content)
        
        return {
            "name": frontmatter.get("name", skill_path.name),
            "description": frontmatter.get("description", "No description"),
            "when_to_use": frontmatter.get("when_to_use", ""),
            "script": frontmatter.get("script", ""),
            "path": str(skill_path),
        }
    except Exception as e:
        logger.warning(f"Failed to read skill {skill_path}: {e}")
        return None


# =============================================================================
# List Skills Tool
# =============================================================================

def _list_skills(arguments: dict, working_dir: str) -> str:
    """List all available skills with descriptions."""
    category = arguments.get("category", "")
    
    if not os.path.exists(SKILLS_DIR):
        return f"Error: Skills directory not found at {SKILLS_DIR}"
    
    skills = []
    skills_path = Path(SKILLS_DIR)
    
    for skill_dir in sorted(skills_path.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue
            
        info = get_skill_info(skill_dir)
        if info:
            # Filter by category if specified
            if category and category.lower() not in info["name"].lower():
                if category.lower() not in info.get("description", "").lower():
                    continue
            skills.append(info)
    
    if not skills:
        return "No skills found" + (f" matching '{category}'" if category else "")
    
    # Format output
    output = f"Available Skills ({len(skills)} total):\n"
    output += "=" * 50 + "\n\n"
    
    for skill in skills:
        output += f"## {skill['name']}\n"
        output += f"   {skill['description']}\n"
        if skill.get("when_to_use"):
            output += f"   When: {skill['when_to_use']}\n"
        if skill.get("script"):
            output += f"   Script: {skill['script']}\n"
        output += "\n"
    
    output += "\nUse read_skill(name) to get full instructions for any skill."
    
    return output


register_tool(
    name="list_skills",
    description="List all available skills. Skills are reusable workflows for common tasks like deployment, Docker management, SSH, backups, etc. Call this FIRST to discover what capabilities are available.",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Optional filter by category/keyword (e.g., 'docker', 'deploy', 'backup')"
            }
        },
        "required": []
    },
    handler=_list_skills
)


# =============================================================================
# Read Skill Tool
# =============================================================================

def _read_skill(arguments: dict, working_dir: str) -> str:
    """Read a skill's full SKILL.md content."""
    name = arguments.get("name", "")
    
    if not name:
        return "Error: skill name is required"
    
    if not os.path.exists(SKILLS_DIR):
        return f"Error: Skills directory not found at {SKILLS_DIR}"
    
    # Find the skill (case-insensitive, supports partial match)
    skills_path = Path(SKILLS_DIR)
    skill_path = None
    
    # Exact match first
    exact = skills_path / name
    if exact.exists() and exact.is_dir():
        skill_path = exact
    else:
        # Partial match
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir() and name.lower() in skill_dir.name.lower():
                skill_path = skill_dir
                break
    
    if not skill_path:
        # List similar skills
        similar = []
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                # Check if any word matches
                skill_words = skill_dir.name.lower().replace("-", " ").split()
                name_words = name.lower().replace("-", " ").split()
                if any(nw in sw or sw in nw for nw in name_words for sw in skill_words):
                    similar.append(skill_dir.name)
        
        error = f"Error: Skill '{name}' not found."
        if similar:
            error += f"\n\nDid you mean one of these?\n- " + "\n- ".join(similar[:5])
        return error
    
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return f"Error: Skill found but SKILL.md missing at {skill_path}"
    
    try:
        content = skill_md.read_text()
        
        # Also check for scripts in the skill directory
        scripts = list(skill_path.glob("*.sh")) + list(skill_path.glob("*.py"))
        
        output = f"# Skill: {skill_path.name}\n"
        output += f"# Path: {skill_path}\n"
        if scripts:
            output += f"# Scripts: {', '.join(s.name for s in scripts)}\n"
        output += "\n" + "=" * 50 + "\n\n"
        output += content
        
        return output
        
    except Exception as e:
        return f"Error reading skill: {e}"


register_tool(
    name="read_skill",
    description="Read the full content of a skill's SKILL.md file. This gives you detailed instructions on how to accomplish a task. Always read the relevant skill before attempting a task.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The skill name (e.g., 'standard-deployment', 'connect-server', 'docker')"
            }
        },
        "required": ["name"]
    },
    handler=_read_skill
)


# =============================================================================
# Search Skills Tool
# =============================================================================

def _search_skills(arguments: dict, working_dir: str) -> str:
    """Search skills by keyword in name, description, and content."""
    query = arguments.get("query", "")
    
    if not query:
        return "Error: search query is required"
    
    if not os.path.exists(SKILLS_DIR):
        return f"Error: Skills directory not found at {SKILLS_DIR}"
    
    skills_path = Path(SKILLS_DIR)
    matches = []
    query_lower = query.lower()
    query_words = query_lower.replace("-", " ").split()
    
    for skill_dir in skills_path.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        try:
            content = skill_md.read_text()
            frontmatter, body = parse_frontmatter(content)
            
            # Calculate relevance score
            score = 0
            name = frontmatter.get("name", skill_dir.name).lower()
            description = frontmatter.get("description", "").lower()
            when_to_use = frontmatter.get("when_to_use", "").lower()
            
            # Exact match in name = highest score
            if query_lower in name:
                score += 10
            
            # Word matches in name
            for word in query_words:
                if word in name:
                    score += 5
            
            # Matches in description
            if query_lower in description:
                score += 3
            for word in query_words:
                if word in description:
                    score += 2
            
            # Matches in when_to_use
            if query_lower in when_to_use:
                score += 2
            
            # Matches in body content
            if query_lower in body.lower():
                score += 1
            
            if score > 0:
                matches.append({
                    "name": frontmatter.get("name", skill_dir.name),
                    "description": frontmatter.get("description", "No description"),
                    "when_to_use": when_to_use,
                    "score": score,
                    "path": str(skill_dir),
                })
                
        except Exception as e:
            logger.warning(f"Failed to search skill {skill_dir}: {e}")
    
    if not matches:
        return f"No skills found matching '{query}'.\n\nTry:\n- list_skills() to see all available skills\n- Different keywords"
    
    # Sort by relevance
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    # Format output
    output = f"Skills matching '{query}' ({len(matches)} found):\n"
    output += "=" * 50 + "\n\n"
    
    for match in matches[:10]:  # Top 10
        output += f"## {match['name']} (relevance: {match['score']})\n"
        output += f"   {match['description']}\n"
        if match.get("when_to_use"):
            output += f"   When: {match['when_to_use']}\n"
        output += "\n"
    
    output += "\nUse read_skill(name) to get full instructions."
    
    return output


register_tool(
    name="search_skills",
    description="Search for skills by keyword. Searches skill names, descriptions, and content. Use this when you're not sure which skill to use for a task.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'docker restart', 'deploy', 'backup')"
            }
        },
        "required": ["query"]
    },
    handler=_search_skills
)
