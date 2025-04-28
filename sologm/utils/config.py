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
        # Define base_dir first as it's used for default config path
        self.base_dir = Path.home() / ".sologm"
        self.config_path = config_path or self.base_dir / "config.yaml"
        # Store config_file path for potential use elsewhere (like logger)
        self.config_file = self.config_path
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
            logger.debug(
                f"Config file not found, creating default at: {self.config_path}"
            )
            # Call _create_default_config WITHOUT the base_dir argument
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

    # Removed base_dir argument here
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        # Use self.base_dir directly
        # --- Database Default ---
        default_db_path = self.base_dir / "sologm.db"
        default_db_url = f"sqlite:///{default_db_path}"
        logger.debug(f"Using default database URL: {default_db_url}")

        # --- New: Define default log settings using self.base_dir ---
        default_log_file_path = self.base_dir / "sologm.log"
        default_log_max_bytes = 5 * 1024 * 1024  # 5 MB
        default_log_backup_count = 1

        default_config = {
            "anthropic_api_key": "",
            "default_interpretations": 5,
            "oracle_retries": 2,
            "debug": False,
            "database_url": default_db_url,
            # --- Add logging config defaults (flat keys) ---
            "log_file_path": str(default_log_file_path),  # Store as string
            "log_max_bytes": default_log_max_bytes,
            "log_backup_count": default_log_backup_count,
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
        """Get configuration value using flat keys.

        Args:
            key: Configuration key (e.g., 'database_url', 'log_file_path').
            default: Default value if key doesn't exist.

        Returns:
            Configuration value.
        """
        # Check environment variables first (using flat key)
        env_key = f"SOLOGM_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            logger.debug(f"Using environment variable {env_key} for config key: {key}")
            # Attempt to convert common types from env vars
            if env_value.isdigit():
                return int(env_value)
            if env_value.lower() in ["true", "false"]:
                return env_value.lower() == "true"
            return env_value

        # Special case for API keys (remains the same)
        if key.endswith("_api_key"):
            # Check for environment variable without prefix
            api_env_key = f"{key[:-8].upper()}_API_KEY"
            api_env_value = os.environ.get(api_env_key)
            if api_env_value is not None:
                logger.debug(
                    f"Using environment variable {api_env_key} for API key: {key}"
                )
                return api_env_value

        # Fall back to config file (direct lookup)
        value = self._config.get(key, default)
        # Log appropriately (avoid logging full API keys)
        log_value = "****" if key.endswith("_api_key") else value
        if key in self._config:
            logger.debug(f"Using config file value for key: {key}={log_value}")
        else:
            logger.debug(
                f"Key '{key}' not found in config file, using default: {log_value}"
            )
            return default
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
        # Direct assignment for flat keys
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
