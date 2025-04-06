"""Configuration management for Solo RPG Helper."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from sologm.utils.errors import ConfigError

# Create a logger for this module
logger = logging.getLogger(__name__)


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
            logger.debug("Creating new Config instance")
            cls._instance = cls(config_path)
        elif config_path is not None:
            # Reinitialize with new path if specified
            logger.debug(f"Reinitializing Config with new path: {config_path}")
            cls._instance = cls(config_path)
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        self.base_dir = Path.home() / ".sologm"
        self.config_path = config_path or self.base_dir / "config.yaml"
        logger.debug(f"Initializing Config with path: {self.config_path}")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        # Create base directory if it doesn't exist
        if not self.base_dir.exists():
            logger.debug(f"Creating base directory: {self.base_dir}")
            self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create default config if it doesn't exist
        if not self.config_path.exists():
            logger.debug(f"Config file not found, creating default at: {self.config_path}")
            self._create_default_config()
        else:
            logger.debug(f"Loading existing config from: {self.config_path}")

        # Load config
        try:
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded configuration with {len(self._config)} keys")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigError(f"Failed to load configuration: {e}") from e

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        # Create default SQLite database path in .sologm directory
        default_db_path = self.base_dir / "sologm.db"
        default_db_url = f"sqlite:///{default_db_path}"
        logger.debug(f"Using default database URL: {default_db_url}")

        default_config = {
            "anthropic_api_key": "",
            "default_interpretations": 5,
            "oracle_retries": 2,
            "debug": False,
            "database_url": default_db_url,
        }

        try:
            logger.debug(f"Writing default configuration to: {self.config_path}")
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)
            self._config = default_config
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
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
            logger.debug(f"Using environment variable {env_key} for config key: {key}")
            return env_value

        # Special case for API keys
        if key.endswith("_api_key"):
            # Check for environment variable without prefix
            api_env_key = f"{key[:-8].upper()}_API_KEY"
            api_env_value = os.environ.get(api_env_key)
            if api_env_value is not None:
                logger.debug(f"Using environment variable {api_env_key} for API key: {key}")
                return api_env_value

        # Fall back to config file
        value = self._config.get(key, default)
        if key.endswith("_api_key"):
            # Don't log actual API key values
            logger.debug(f"Using config file value for API key: {key}")
        else:
            logger.debug(f"Using config file value for key: {key}={value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        if key.endswith("_api_key"):
            # Don't log actual API key values
            logger.debug(f"Setting config value for API key: {key}")
        else:
            logger.debug(f"Setting config value: {key}={value}")
        self._config[key] = value
        self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            logger.debug(f"Saving configuration to: {self.config_path}")
            with open(self.config_path, "w") as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigError(f"Failed to save configuration: {e}") from e


def get_config() -> Config:
    """Get the global Config instance.

    Returns:
        The singleton Config instance
    """
    logger.debug("Getting global Config instance")
    return Config.get_instance()
