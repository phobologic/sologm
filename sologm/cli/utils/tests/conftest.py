"""Shared test fixtures for CLI utility tests."""

from unittest.mock import Mock

import pytest
from rich.console import Console

# Import common fixtures from central conftest
from sologm.tests.conftest import (
    db_engine,
    db_session,
    database_session,
    mock_anthropic_client,
    test_game,
    test_act,
    test_scene,
    test_events,
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources,
)

# Import core fixtures that might be needed
from sologm.core.tests.conftest import (
    game_manager,
    act_manager,
    scene_manager,
    event_manager,
    oracle_manager,
    dice_manager,
)


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
