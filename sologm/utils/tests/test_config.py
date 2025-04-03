"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import yaml

from sologm.utils.config import Config


def test_config_initialization():
    """Test that Config initializes correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "config.yaml"
        config = Config(temp_path)

        # Check that the config file was created
        assert temp_path.exists()

        # Check that the config has default values
        with open(temp_path, "r") as f:
            data = yaml.safe_load(f)

        assert "anthropic_api_key" in data
        assert "default_interpretations" in data
        assert "debug" in data


def test_config_get():
    """Test getting configuration values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "config.yaml"

        # Create a config file with test values
        test_config = {
            "test_key": "test_value",
            "anthropic_api_key": "test_api_key",
        }

        with open(temp_path, "w") as f:
            yaml.dump(test_config, f)

        config = Config(temp_path)

        # Test getting existing key
        assert config.get("test_key") == "test_value"

        # Test getting non-existent key with default
        assert config.get("non_existent", "default") == "default"

        # Test getting non-existent key without default
        assert config.get("non_existent") is None


def test_config_set():
    """Test setting configuration values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "config.yaml"
        config = Config(temp_path)

        # Set a new value
        config.set("new_key", "new_value")

        # Check that the value was saved
        assert config.get("new_key") == "new_value"

        # Check that the value was written to the file
        with open(temp_path, "r") as f:
            data = yaml.safe_load(f)

        assert data["new_key"] == "new_value"


def test_config_environment_variables():
    """Test that environment variables override config values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "config.yaml"

        # Create a config file with test values
        test_config = {
            "test_key": "file_value",
            "anthropic_api_key": "file_api_key",
        }

        with open(temp_path, "w") as f:
            yaml.dump(test_config, f)

        # Set environment variables
        os.environ["SOLOGM_TEST_KEY"] = "env_value"
        os.environ["ANTHROPIC_API_KEY"] = "env_api_key"

        config = Config(temp_path)

        # Test that environment variables take precedence
        assert config.get("test_key") == "env_value"
        assert config.get("anthropic_api_key") == "env_api_key"

        # Clean up
        del os.environ["SOLOGM_TEST_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
