"""Shared test fixtures for CLI utility tests."""

from unittest.mock import Mock

import pytest
from rich.console import Console

# Import all fixtures from central conftest
from sologm.tests.conftest import *  # noqa: F401, F403


# CLI-specific fixtures
@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    # Set a default width for the console to avoid type errors
    mock.width = 80
    return mock


# Explicitly expose the helper functions needed for testing
@pytest.fixture
def display_helpers():
    """Expose display helper functions for testing."""
    from sologm.cli.utils.display import (
        _create_dice_rolls_panel,
        _create_empty_oracle_panel,
        _create_events_panel,
    )

    return {
        "create_empty_oracle_panel": _create_empty_oracle_panel,
        "create_dice_rolls_panel": _create_dice_rolls_panel,
        "create_events_panel": _create_events_panel,
    }
