"""Load settings from environment and config files."""
import os
import json
from pathlib import Path
from typing import Dict, Any


class Settings:
    """Load settings from environment and config files."""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or environment."""
        # Defaults from context documents
        self.defaults: Dict[str, Any] = {
            "server": {
                "host": "192.168.86.47",
                "port": 4242,
                "user": "unarmedpuppy",
                "connect_script": "scripts/connect-server.sh"
            },
            "sonarr": {
                "api_key": os.getenv("SONARR_API_KEY", "dd7148e5a3dd4f7aa0c579194f45edff"),
                "base_url": "http://127.0.0.1:8989",
                "container": "media-download-sonarr"
            },
            "radarr": {
                "api_key": os.getenv("RADARR_API_KEY", "afb58cf1eaee44208099b403b666e29c"),
                "base_url": "http://127.0.0.1:7878",
                "container": "media-download-radarr"
            },
            "nzbget": {
                "username": os.getenv("NZBGET_USERNAME", "nzbget"),
                "password": os.getenv("NZBGET_PASSWORD", "nzbget"),
                "host": "media-download-gluetun",
                "port": 6789
            },
            "qbittorrent": {
                "username": os.getenv("QBITTORRENT_USERNAME", "admin"),
                "password": os.getenv("QBITTORRENT_PASSWORD", "adminadmin"),
                "host": "media-download-gluetun",
                "port": 8080
            }
        }
        
        # Override with config file if exists
        if self.config_file.exists():
            with open(self.config_file) as f:
                file_config = json.load(f)
                # Deep merge
                for key, value in file_config.items():
                    if key in self.defaults and isinstance(value, dict):
                        self.defaults[key].update(value)
                    else:
                        self.defaults[key] = value
    
    def get(self, service: str, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.defaults.get(service, {}).get(key, default)
    
    def get_service_config(self, service: str) -> Dict[str, Any]:
        """Get entire service configuration."""
        return self.defaults.get(service, {})


# Global settings instance
settings = Settings()

