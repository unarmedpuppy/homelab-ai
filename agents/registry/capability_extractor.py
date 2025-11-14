"""
Capability Extractor for AgentCard Generation

Extracts capabilities from agent prompts and maps them to AgentCard format.
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Paths
PROMPTS_DIR = project_root / "agents" / "prompts"
SKILLS_DIR = project_root / "agents" / "skills"


def extract_skills_from_prompt(prompt_content: str) -> List[str]:
    """Extract skill names from prompt content."""
    skills = []
    
    # Pattern: Skills listed with backticks
    # Format: - `skill-name` - Description
    skill_pattern = r'- `([a-z0-9-]+)`'
    
    # Find "Available Skills" section
    available_skills_match = re.search(
        r'## Available Skills.*?(?=##|\Z)',
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if available_skills_match:
        skills_section = available_skills_match.group(0)
        found_skills = re.findall(skill_pattern, skills_section)
        skills.extend(found_skills)
    
    # Pattern 2: Skills in "Relevant Skills" section (server.md format)
    relevant_skills_match = re.search(
        r'### Relevant Skills.*?(?=###|\Z)',
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if relevant_skills_match:
        skills_section = relevant_skills_match.group(0)
        found_skills = re.findall(skill_pattern, skills_section)
        skills.extend(found_skills)
    
    # Also check "Skills - How to Use" section
    skills_section_match = re.search(
        r'## Skills.*?(?=##|\Z)',
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if skills_section_match:
        skills_section = skills_section_match.group(0)
        found_skills = re.findall(skill_pattern, skills_section)
        skills.extend(found_skills)
    
    # Remove duplicates and return
    return list(set(skills))


def extract_mcp_tool_categories_from_prompt(prompt_content: str) -> List[str]:
    """Extract MCP tool category names from prompt content."""
    categories = []
    
    # Pattern: Category name followed by (N tools)
    # Examples:
    # - Memory management (9 tools)
    # - Docker management (8 tools)
    # - **Activity Monitoring** (4 tools)
    category_pattern = r'[-*]\s+(?:\*\*)?([A-Za-z\s]+?)(?:\*\*)?\s*\((\d+)\s+tools?\)'
    
    # Find MCP Tools section
    mcp_section_match = re.search(
        r'## MCP Tools.*?(?=##|\Z)',
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if mcp_section_match:
        mcp_section = mcp_section_match.group(0)
        matches = re.finditer(category_pattern, mcp_section)
        for match in matches:
            category_name = match.group(1).strip()
            # Convert to snake_case for AgentCard
            category_snake = category_name.lower().replace(' ', '_')
            categories.append(category_snake)
    
    # Also check "Relevant MCP Tools" section (server.md format)
    relevant_tools_match = re.search(
        r'### Relevant MCP Tools.*?(?=###|\Z)',
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if relevant_tools_match:
        tools_section = relevant_tools_match.group(0)
        # Extract category headers (e.g., "1. **Docker Management** (8 tools)")
        category_headers = re.finditer(
            r'\d+\.\s+\*\*([A-Za-z\s]+?)\*\*\s*\((\d+)\s+tools?\)',
            tools_section
        )
        for match in category_headers:
            category_name = match.group(1).strip()
            category_snake = category_name.lower().replace(' ', '_')
            categories.append(category_snake)
    
    # Remove duplicates and return
    return list(set(categories))


def extract_domain_knowledge_from_prompt(prompt_content: str) -> List[str]:
    """Extract domain knowledge items from prompt content."""
    knowledge = []
    
    # Pattern: Domain knowledge section
    # Format: - Item 1
    #         - Item 2
    knowledge_pattern = r'### Domain Knowledge.*?(?=###|##|\Z)'
    
    knowledge_match = re.search(
        knowledge_pattern,
        prompt_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if knowledge_match:
        knowledge_section = knowledge_match.group(0)
        # Extract list items (but stop at next section)
        # Look for lines starting with - that are not headers
        lines = knowledge_section.split('\n')
        in_list = False
        for line in lines:
            # Stop if we hit another section
            if line.startswith('##') or line.startswith('---'):
                break
            # Extract list items
            if line.strip().startswith('-'):
                item = line.strip()[1:].strip()
                # Skip if it's a header or empty
                if item and not item.startswith('#'):
                    # Clean up the item
                    item_clean = item.split('-')[0].strip() if '-' in item else item
                    # Convert to snake_case
                    item_snake = item_clean.lower().replace(' ', '_').replace(' and ', '_').replace(',', '').replace('&', 'and')
                    # Remove special characters
                    item_snake = re.sub(r'[^a-z0-9_]', '', item_snake)
                    # Remove multiple underscores
                    item_snake = re.sub(r'_+', '_', item_snake).strip('_')
                    if item_snake:
                        knowledge.append(item_snake)
    
    return knowledge


def get_all_skills_from_directory() -> List[str]:
    """Get all skill names from skills directory."""
    skills = []
    
    if not SKILLS_DIR.exists():
        return skills
    
    # Get all skill directories
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skills.append(skill_dir.name)
    
    return sorted(skills)


def extract_capabilities_from_prompt(prompt_path: Path) -> Dict[str, List[str]]:
    """
    Extract all capabilities from a prompt file.
    
    Returns:
        Dictionary with keys: 'skills', 'mcp_tool_categories', 'domain_knowledge'
    """
    if not prompt_path.exists():
        return {
            'skills': [],
            'mcp_tool_categories': [],
            'domain_knowledge': []
        }
    
    content = prompt_path.read_text()
    
    return {
        'skills': extract_skills_from_prompt(content),
        'mcp_tool_categories': extract_mcp_tool_categories_from_prompt(content),
        'domain_knowledge': extract_domain_knowledge_from_prompt(content)
    }


def get_base_capabilities() -> Dict[str, List[str]]:
    """Get base capabilities from base.md prompt."""
    base_prompt = PROMPTS_DIR / "base.md"
    return extract_capabilities_from_prompt(base_prompt)


def get_specialization_capabilities(specialization: str) -> Dict[str, List[str]]:
    """
    Get specialization-specific capabilities.
    
    Args:
        specialization: Specialization name (e.g., 'server-management')
    
    Returns:
        Dictionary with capabilities
    """
    # Map specializations to prompt files
    specialization_map = {
        'server-management': 'server.md',
        'server': 'server.md',
        'media-download': None,  # No specific prompt yet
        'database': None,  # No specific prompt yet
    }
    
    prompt_file = specialization_map.get(specialization)
    
    if not prompt_file:
        return {
            'skills': [],
            'mcp_tool_categories': [],
            'domain_knowledge': []
        }
    
    prompt_path = PROMPTS_DIR / prompt_file
    return extract_capabilities_from_prompt(prompt_path)


def combine_capabilities(
    base_capabilities: Dict[str, List[str]],
    specialization_capabilities: Optional[Dict[str, List[str]]] = None
) -> List[str]:
    """
    Combine base and specialization capabilities into a single list.
    
    Args:
        base_capabilities: Capabilities from base prompt
        specialization_capabilities: Optional specialization-specific capabilities
    
    Returns:
        Combined list of capability strings for AgentCard
    """
    all_capabilities = set()
    
    # Add base capabilities
    for category in ['skills', 'mcp_tool_categories', 'domain_knowledge']:
        all_capabilities.update(base_capabilities.get(category, []))
    
    # Add specialization capabilities if provided
    if specialization_capabilities:
        for category in ['skills', 'mcp_tool_categories', 'domain_knowledge']:
            all_capabilities.update(specialization_capabilities.get(category, []))
    
    # Also add all skills from skills directory (comprehensive list)
    all_skills = get_all_skills_from_directory()
    all_capabilities.update(all_skills)
    
    return sorted(list(all_capabilities))


def get_capabilities_for_agent(
    specialization: str = "general",
    include_all_skills: bool = True
) -> List[str]:
    """
    Get complete capability list for an agent.
    
    Args:
        specialization: Agent specialization
        include_all_skills: Whether to include all skills from directory
    
    Returns:
        List of capability strings for AgentCard
    """
    # Get base capabilities
    base_caps = get_base_capabilities()
    
    # Get specialization capabilities
    if specialization and specialization != "general":
        spec_caps = get_specialization_capabilities(specialization)
    else:
        spec_caps = None
    
    # Combine
    capabilities = combine_capabilities(base_caps, spec_caps)
    
    return capabilities


if __name__ == "__main__":
    # Test the extractor
    print("Testing Capability Extractor\n")
    
    print("Base Capabilities:")
    base = get_base_capabilities()
    print(f"  Skills: {base['skills']}")
    print(f"  MCP Tool Categories: {base['mcp_tool_categories']}")
    print(f"  Domain Knowledge: {base['domain_knowledge']}")
    print()
    
    print("Server Management Capabilities:")
    server = get_specialization_capabilities("server-management")
    print(f"  Skills: {server['skills']}")
    print(f"  MCP Tool Categories: {server['mcp_tool_categories']}")
    print(f"  Domain Knowledge: {server['domain_knowledge']}")
    print()
    
    print("Combined Capabilities for Server Management Agent:")
    combined = get_capabilities_for_agent("server-management")
    print(f"  Total: {len(combined)} capabilities")
    print(f"  Sample: {combined[:10]}...")

