"""
Capability Mapping for AgentCard Generation

Maps capabilities from prompts to AgentCard format and provides
specialization-specific capability mappings.
"""

from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import capability extractor
try:
    from agents.registry.capability_extractor import (
        get_base_capabilities,
        get_specialization_capabilities,
        combine_capabilities,
        get_capabilities_for_agent
    )
except ImportError:
    # Fallback for direct execution
    from capability_extractor import (
        get_base_capabilities,
        get_specialization_capabilities,
        combine_capabilities,
        get_capabilities_for_agent
    )


# Specialization-specific capability mappings
# These are additional capabilities beyond what's in prompts
SPECIALIZATION_EXTRA_CAPABILITIES: Dict[str, List[str]] = {
    "server-management": [
        "deployment",
        "troubleshooting",
        "system_monitoring",
        "container_orchestration",
        "infrastructure_management"
    ],
    "media-download": [
        "sonarr_management",
        "radarr_management",
        "download_client_management",
        "media_organization",
        "queue_management"
    ],
    "database": [
        "database_management",
        "migrations",
        "backup_restore",
        "query_optimization",
        "schema_management"
    ],
    "general": []
}


def get_specialization_extra_capabilities(specialization: str) -> List[str]:
    """
    Get extra capabilities for a specialization.
    
    Args:
        specialization: Specialization name
    
    Returns:
        List of additional capabilities
    """
    return SPECIALIZATION_EXTRA_CAPABILITIES.get(specialization, [])


def map_capabilities_to_agentcard(
    specialization: str = "general",
    include_extra: bool = True
) -> List[str]:
    """
    Map capabilities from prompts to AgentCard format.
    
    Args:
        specialization: Agent specialization
        include_extra: Whether to include extra specialization capabilities
    
    Returns:
        List of capability strings for AgentCard
    """
    # Get capabilities from prompts
    capabilities = get_capabilities_for_agent(specialization)
    
    # Add extra specialization capabilities if requested
    if include_extra and specialization:
        extra = get_specialization_extra_capabilities(specialization)
        capabilities.extend(extra)
    
    # Remove duplicates and sort
    return sorted(list(set(capabilities)))


def get_capability_summary(capabilities: List[str]) -> Dict[str, int]:
    """
    Get summary statistics for capabilities.
    
    Args:
        capabilities: List of capability strings
    
    Returns:
        Dictionary with counts by category
    """
    summary = {
        'total': len(capabilities),
        'skills': 0,
        'mcp_tools': 0,
        'domain_knowledge': 0,
        'other': 0
    }
    
    # Categorize capabilities
    for cap in capabilities:
        if cap.startswith('troubleshoot-') or cap.startswith('standard-') or \
           cap.startswith('deploy-') or cap.startswith('add-') or \
           cap.startswith('cleanup-') or cap.startswith('system-') or \
           cap.startswith('agent-'):
            summary['skills'] += 1
        elif '_management' in cap or '_monitoring' in cap or \
             '_operations' in cap or '_coordination' in cap or \
             cap.endswith('_tools'):
            summary['mcp_tools'] += 1
        elif '_administration' in cap or '_orchestration' in cap or \
             cap in ['docker', 'linux', 'networking', 'git']:
            summary['domain_knowledge'] += 1
        else:
            summary['other'] += 1
    
    return summary


def format_capabilities_for_agentcard(capabilities: List[str]) -> List[str]:
    """
    Format capabilities for AgentCard (ensure proper format).
    
    Args:
        capabilities: List of capability strings
    
    Returns:
        Formatted list of capabilities
    """
    formatted = []
    
    for cap in capabilities:
        # Ensure snake_case or kebab-case
        # Remove special characters, normalize
        cap_clean = cap.strip().lower()
        
        # Skip empty
        if not cap_clean:
            continue
        
        formatted.append(cap_clean)
    
    # Remove duplicates and sort
    return sorted(list(set(formatted)))


if __name__ == "__main__":
    # Test the mapping
    print("Testing Capability Mapping\n")
    
    print("Server Management Agent Capabilities:")
    server_caps = map_capabilities_to_agentcard("server-management")
    print(f"  Total: {len(server_caps)}")
    print(f"  Sample: {server_caps[:15]}")
    print()
    
    summary = get_capability_summary(server_caps)
    print("Capability Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

