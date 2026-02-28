"""Tests for configuration."""

import json
import time
from pathlib import Path

import pytest

from chaobot.config.schema import Config, ProviderConfig
from chaobot.config.manager import ConfigManager


def test_default_config() -> None:
    """Test default configuration."""
    config = Config()
    assert config.agents.defaults.model == "anthropic/claude-3-5-sonnet-20241022"
    assert config.agents.defaults.provider == "openrouter"


def test_provider_config() -> None:
    """Test provider configuration."""
    config = ProviderConfig()
    assert config.enabled is True
    assert config.timeout == 60
    assert config.max_retries == 3


def test_config_manager_init(tmp_path: Path) -> None:
    """Test config manager initialization."""
    manager = ConfigManager(config_dir=tmp_path)
    manager.initialize()

    assert manager.config_path.exists()
    assert manager.workspace_path.exists()


def test_config_save_and_load(tmp_path: Path) -> None:
    """Test saving and loading configuration."""
    manager = ConfigManager(config_dir=tmp_path)
    manager.initialize()

    # Load config
    config = manager.load()
    config.agents.defaults.model = "test-model"

    # Save config
    manager.save(config)

    # Reload and verify
    config2 = manager.load(reload=True)
    assert config2.agents.defaults.model == "test-model"


def test_config_hot_reload(tmp_path: Path) -> None:
    """Test configuration hot-reload."""
    manager = ConfigManager(config_dir=tmp_path)
    manager.initialize()

    # Load initial config
    config1 = manager.load()
    initial_model = config1.agents.defaults.model

    # Modify config file directly
    config_path = tmp_path / "config.json"
    with open(config_path) as f:
        data = json.load(f)

    data["agents"]["defaults"]["model"] = "modified-model"

    with open(config_path, "w") as f:
        json.dump(data, f)

    # Wait a bit for mtime to change
    time.sleep(0.1)

    # Load again (should detect modification)
    assert manager.is_config_modified() is True

    config2 = manager.load()
    assert config2.agents.defaults.model == "modified-model"


def test_config_cache(tmp_path: Path) -> None:
    """Test configuration caching."""
    manager = ConfigManager(config_dir=tmp_path)
    manager.initialize()

    # Load config twice
    config1 = manager.load()
    config2 = manager.load()

    # Should be the same cached object
    assert config1 is config2

    # Force reload should create new object
    config3 = manager.load(reload=True)
    assert config3 is not config1
