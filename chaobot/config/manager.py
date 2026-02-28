"""Configuration manager."""

import json
import time
from pathlib import Path

from chaobot.config.schema import Config


class ConfigManager:
    """Manages configuration loading and saving with hot-reload support."""

    _cached_config: Config | None = None
    _cached_mtime: float = 0.0

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            config_dir: Directory for config files. Defaults to ~/.chaobot
        """
        self.config_dir = config_dir or Path.home() / ".chaobot"
        self.config_path = self.config_dir / "config.json"
        self.workspace_path = self.config_dir / "workspace"

    def initialize(self) -> None:
        """Initialize config directory and default config."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Create default config if not exists
        if not self.config_path.exists():
            default_config = self._create_default_config()
            self.save(default_config)

        # Create HEARTBEAT.md
        heartbeat_path = self.workspace_path / "HEARTBEAT.md"
        if not heartbeat_path.exists():
            heartbeat_path.write_text(self._get_default_heartbeat())

    def load(self, reload: bool = False) -> Config:
        """Load configuration from file with optional hot-reload.

        Args:
            reload: Force reload from disk even if cached

        Returns:
            Config object
        """
        if not self.config_path.exists():
            self.initialize()

        # Check if file has been modified
        current_mtime = self.config_path.stat().st_mtime

        # Return cached config if not modified and not forcing reload
        if not reload and ConfigManager._cached_config is not None:
            if current_mtime <= ConfigManager._cached_mtime:
                return ConfigManager._cached_config

        # Load from disk
        with open(self.config_path) as f:
            data = json.load(f)

        config = Config(**data)
        config.config_path = self.config_path
        config.workspace_path = self.workspace_path

        # Update cache
        ConfigManager._cached_config = config
        ConfigManager._cached_mtime = current_mtime

        return config

    def is_config_modified(self) -> bool:
        """Check if config file has been modified since last load.

        Returns:
            True if config has been modified
        """
        if not self.config_path.exists():
            return True

        current_mtime = self.config_path.stat().st_mtime
        return current_mtime > ConfigManager._cached_mtime

    def save(self, config: Config) -> None:
        """Save configuration to file.

        Args:
            config: Config object to save
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert to dict and remove internal fields
        data = config.model_dump(exclude={"config_path", "workspace_path"})

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _create_default_config(self) -> Config:
        """Create default configuration."""
        return Config()

    def _get_default_heartbeat(self) -> str:
        """Get default HEARTBEAT.md content."""
        return """# HEARTBEAT.md

This file contains periodic tasks that chaobot will execute automatically.

## Periodic Tasks

- [ ] Check weather forecast and send a summary
- [ ] Scan inbox for urgent emails

Add your own tasks here. The agent will check this file every 30 minutes.
"""
