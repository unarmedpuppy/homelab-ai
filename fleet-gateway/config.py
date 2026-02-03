"""Configuration loading for Agent Gateway."""
import os
import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from models import GatewayConfig, AgentConfig, HealthCheckConfig

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> GatewayConfig:
    """
    Load gateway configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If not provided, uses CONFIG_PATH env var
                    or defaults to ./config.yaml

    Returns:
        GatewayConfig with health_check settings and agent registry

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config file has invalid structure
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        raise FileNotFoundError(f"Config file not found: {config_file}")

    logger.info(f"Loading configuration from: {config_file}")

    with open(config_file, "r") as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        raw_config = {}

    # Parse health_check section
    health_check_data = raw_config.get("health_check", {})
    health_check = HealthCheckConfig(**health_check_data)

    # Parse agents section
    agents_data = raw_config.get("agents", {})
    agents = {}

    for agent_id, agent_data in agents_data.items():
        try:
            agents[agent_id] = AgentConfig(**agent_data)
            logger.debug(f"Loaded agent config: {agent_id} -> {agents[agent_id].endpoint}")
        except ValidationError as e:
            logger.warning(f"Invalid agent config for '{agent_id}': {e}")
            continue

    config = GatewayConfig(
        health_check=health_check,
        agents=agents,
    )

    logger.info(f"Loaded {len(config.agents)} agents from config")

    return config


def get_config_path() -> str:
    """Get the config path from environment or default."""
    return os.getenv("CONFIG_PATH", "config.yaml")
