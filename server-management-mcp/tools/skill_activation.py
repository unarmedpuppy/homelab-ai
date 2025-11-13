"""
Skill Auto-Activation Tools for MCP Server

Provides tools for agents to discover and activate relevant skills based on context.
This addresses the critical issue where skills sit unused unless explicitly activated.
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


# Paths
SKILLS_DIR = project_root / "server-management-skills"
SKILLS_README = SKILLS_DIR / "README.md"


def _load_skill_metadata(skill_dir: Path) -> Optional[Dict[str, Any]]:
    """Load skill metadata from SKILL.md frontmatter."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None
    
    try:
        content = skill_file.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                return metadata
    except Exception:
        pass
    
    return None


def _load_all_skills() -> List[Dict[str, Any]]:
    """Load all skills with their metadata."""
    skills = []
    
    if not SKILLS_DIR.exists():
        return skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        
        # Skip proposals directory
        if skill_dir.name == "proposals":
            continue
        
        metadata = _load_skill_metadata(skill_dir)
        if metadata:
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir.relative_to(project_root)),
                **metadata
            })
    
    return skills


def _match_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False


def _match_patterns(text: str, patterns: List[str]) -> bool:
    """Check if text matches any regex patterns."""
    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        except Exception:
            continue
    return False


def _get_skill_keywords(skill: Dict[str, Any]) -> List[str]:
    """Extract keywords from skill metadata."""
    keywords = []
    
    # Add skill name (split by hyphens)
    name_parts = skill.get("name", "").split("-")
    keywords.extend(name_parts)
    
    # Add description words
    description = skill.get("description", "")
    if description:
        # Extract important words (skip common words)
        words = re.findall(r'\b\w+\b', description.lower())
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "must", "can", "this", "that", "these", "those"}
        keywords.extend([w for w in words if w not in common_words and len(w) > 3])
    
    # Add category
    category = skill.get("category", "")
    if category:
        keywords.append(category)
    
    return list(set(keywords))  # Remove duplicates


def _suggest_relevant_skills(
    prompt_text: str = "",
    file_paths: List[str] = None,
    task_description: str = ""
) -> List[Dict[str, Any]]:
    """
    Suggest relevant skills based on context.
    
    Args:
        prompt_text: Current prompt or question
        file_paths: Files being edited or referenced
        task_description: Description of current task
    
    Returns:
        List of relevant skills with match reasons
    """
    all_skills = _load_all_skills()
    relevant_skills = []
    
    # Combine all context
    context_text = f"{prompt_text} {task_description}".lower()
    if file_paths:
        context_text += " " + " ".join(file_paths).lower()
    
    # Skill-specific keyword mappings
    skill_keywords = {
        "standard-deployment": ["deploy", "deployment", "deploying", "git", "push", "restart", "service"],
        "deploy-new-service": ["new service", "new app", "setup", "configure", "docker-compose", "new application"],
        "add-subdomain": ["subdomain", "domain", "traefik", "routing", "homepage", "cloudflare"],
        "troubleshoot-container-failure": ["container", "docker", "failing", "error", "crash", "unhealthy", "troubleshoot"],
        "troubleshoot-stuck-downloads": ["download", "stuck", "queue", "sonarr", "radarr", "nzbget", "qbittorrent"],
        "system-health-check": ["health", "check", "system", "status", "verify", "monitoring"],
        "cleanup-disk-space": ["disk", "space", "cleanup", "full", "storage", "prune"],
        "add-root-folder": ["root folder", "radarr", "sonarr", "media", "folder"],
    }
    
    # Check each skill
    for skill in all_skills:
        skill_name = skill.get("name", "")
        match_reasons = []
        score = 0
        
        # Check skill-specific keywords
        if skill_name in skill_keywords:
            keywords = skill_keywords[skill_name]
            for keyword in keywords:
                if keyword in context_text:
                    match_reasons.append(f"Keyword match: '{keyword}'")
                    score += 2
        
        # Check general keywords from skill metadata
        skill_keywords_list = _get_skill_keywords(skill)
        for keyword in skill_keywords_list[:10]:  # Limit to top 10 keywords
            if keyword in context_text:
                match_reasons.append(f"Skill keyword: '{keyword}'")
                score += 1
        
        # Check file path patterns
        if file_paths:
            for file_path in file_paths:
                # Check if file path suggests skill usage
                if "docker-compose" in file_path.lower() and "deploy" in context_text:
                    if skill_name in ["standard-deployment", "deploy-new-service"]:
                        match_reasons.append("File path suggests deployment")
                        score += 2
                
                if "traefik" in file_path.lower() or "routing" in file_path.lower():
                    if skill_name == "add-subdomain":
                        match_reasons.append("File path suggests subdomain configuration")
                        score += 2
        
        # Check category match
        category = skill.get("category", "")
        if category:
            if category in context_text:
                match_reasons.append(f"Category match: '{category}'")
                score += 1
        
        # If score > 0, skill is relevant
        if score > 0:
            relevant_skills.append({
                "skill_name": skill_name,
                "description": skill.get("description", ""),
                "category": category,
                "path": skill.get("path", ""),
                "match_score": score,
                "match_reasons": match_reasons,
                "when_to_use": skill.get("when_to_use", ""),
            })
    
    # Sort by match score (highest first)
    relevant_skills.sort(key=lambda x: x["match_score"], reverse=True)
    
    return relevant_skills


def register_skill_activation_tools(server: Server):
    """Register skill activation tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def suggest_relevant_skills(
        prompt_text: str = "",
        file_paths: str = "",
        task_description: str = ""
    ) -> Dict[str, Any]:
        """
        Suggest relevant skills based on current context (prompt, files, task).
        
        This tool analyzes your current context and suggests which skills you should
        check and use. This addresses the critical issue where skills sit unused
        unless explicitly activated.
        
        Args:
            prompt_text: Your current prompt or question (what you're asking Claude)
            file_paths: Comma-separated list of file paths you're working with
            task_description: Description of your current task
        
        Returns:
            List of relevant skills with match reasons and when to use them
        
        Example:
            suggest_relevant_skills(
                prompt_text="How do I deploy code changes?",
                file_paths="apps/my-app/docker-compose.yml",
                task_description="Deploy latest changes to production"
            )
        """
        # Parse file paths
        file_list = []
        if file_paths:
            file_list = [f.strip() for f in file_paths.split(",") if f.strip()]
        
        # Get relevant skills
        relevant_skills = _suggest_relevant_skills(
            prompt_text=prompt_text,
            file_paths=file_list,
            task_description=task_description
        )
        
        # Format response
        if not relevant_skills:
            return {
                "status": "success",
                "message": "No relevant skills found for current context. Check server-management-skills/README.md for all available skills.",
                "skills": [],
                "suggestion": "Review server-management-skills/README.md to see all available skills."
            }
        
        # Format skill activation reminder
        reminder_lines = [
            "🎯 SKILL ACTIVATION CHECK",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        
        for skill in relevant_skills[:3]:  # Top 3 most relevant
            reminder_lines.append(f"✅ {skill['skill_name']} - {skill['description']}")
            if skill['match_reasons']:
                reminder_lines.append(f"   Match: {', '.join(skill['match_reasons'][:2])}")
            reminder_lines.append(f"   Path: {skill['path']}/SKILL.md")
            reminder_lines.append("")
        
        reminder_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        reminder_lines.append("⚠️ IMPORTANT: Check and use these skills BEFORE implementing!")
        reminder_lines.append("   Skills provide tested workflows and best practices.")
        reminder_lines.append("   Don't reinvent the wheel - use existing skills!")
        
        reminder = "\n".join(reminder_lines)
        
        return {
            "status": "success",
            "message": f"Found {len(relevant_skills)} relevant skill(s)",
            "skills": relevant_skills,
            "activation_reminder": reminder,
            "suggestion": f"Check these skills before proceeding: {', '.join([s['skill_name'] for s in relevant_skills[:3]])}"
        }
    
    @server.tool()
    @with_automatic_logging()
    async def get_skill_activation_reminder(
        context_summary: str
    ) -> Dict[str, Any]:
        """
        Get a formatted skill activation reminder based on context summary.
        
        Use this before starting work to get a reminder of which skills to check.
        This helps ensure skills are actually used instead of sitting unused.
        
        Args:
            context_summary: Brief summary of what you're about to work on
        
        Returns:
            Formatted reminder with relevant skills to check
        
        Example:
            get_skill_activation_reminder(
                context_summary="Deploying code changes to trading-bot service"
            )
        """
        relevant_skills = _suggest_relevant_skills(
            prompt_text=context_summary,
            task_description=context_summary
        )
        
        if not relevant_skills:
            return {
                "status": "success",
                "reminder": "No specific skills match your context. Review server-management-skills/README.md for all available skills.",
                "skills": []
            }
        
        # Build reminder
        reminder_lines = [
            "🎯 SKILL ACTIVATION CHECK",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "Before starting work, check these relevant skills:",
            ""
        ]
        
        for i, skill in enumerate(relevant_skills[:5], 1):  # Top 5
            reminder_lines.append(f"{i}. **{skill['skill_name']}**")
            reminder_lines.append(f"   Description: {skill['description']}")
            if skill['when_to_use']:
                reminder_lines.append(f"   When to use: {skill['when_to_use']}")
            reminder_lines.append(f"   Path: `{skill['path']}/SKILL.md`")
            reminder_lines.append("")
        
        reminder_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        reminder_lines.append("⚠️ CRITICAL: Load and review these skills BEFORE implementing!")
        reminder_lines.append("   Skills provide tested workflows that prevent mistakes.")
        reminder_lines.append("   Don't skip this step - it saves time and ensures quality!")
        
        reminder = "\n".join(reminder_lines)
        
        return {
            "status": "success",
            "reminder": reminder,
            "skills": relevant_skills[:5],
            "count": len(relevant_skills)
        }

