"""Configuration management for Solo RPG Helper."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from sologm.utils.errors import ConfigError


class Config:
    """Configuration manager for Solo RPG Helper."""

    _instance = None

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> "Config":
        """Get or create the singleton Config instance.

        Args:
            config_path: Optional path to config file. If provided while instance
                exists, will reinitialize with new path.

        Returns:
            The singleton Config instance
        """
        if cls._instance is None:
            cls._instance = cls(config_path)
        elif config_path is not None:
            # Reinitialize with new path if specified
            cls._instance = cls(config_path)
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        self.base_dir = Path.home() / ".sologm"
        self.config_path = config_path or self.base_dir / "config.yaml"
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create default config if it doesn't exist
        if not self.config_path.exists():
            self._create_default_config()

        # Load config
        try:
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}") from e

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        # Create default SQLite database path in .sologm directory
        default_db_path = self.base_dir / "sologm.db"
        default_db_url = f"sqlite:///{default_db_path}"

        default_config = {
            "anthropic_api_key": "",
            "default_interpretations": 5,
            "oracle_retries": 2,
            "debug": False,
            "database_url": default_db_url,
        }

        try:
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)
            self._config = default_config
        except Exception as e:
            raise ConfigError(f"Failed to create default configuration: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key doesn't exist.

        Returns:
            Configuration value.
        """
        # Check environment variables first (with SOLOGM_ prefix)
        env_key = f"SOLOGM_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        # Special case for API keys
        if key.endswith("_api_key"):
            # Check for environment variable without prefix
            api_env_key = f"{key[:-8].upper()}_API_KEY"
            api_env_value = os.environ.get(api_env_key)
            if api_env_value is not None:
                return api_env_value

        # Fall back to config file
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._config[key] = value
        self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}") from e


def get_config() -> Config:
    """Get the global Config instance.

    Returns:
        The singleton Config instance
    """
    return Config.get_instance()
