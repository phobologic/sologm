"""Shared test fixtures for CLI utility tests."""

from unittest.mock import Mock

import pytest
from rich.console import Console

# Import fixtures from core tests to reuse them
from sologm.core.tests.conftest import (
    db_engine,
    db_session,
    database_session,
    game_manager,
    scene_manager,
    event_manager,
    dice_manager,
    oracle_manager,
    test_game,
    test_scene,
    test_events,
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
)


@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    # Set a default width for the console to avoid type errors
    mock.width = 80
    return mock
