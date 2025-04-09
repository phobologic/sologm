"""Shared test fixtures for CLI utility tests."""

from unittest.mock import Mock, MagicMock

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
    test_game,
    test_scene,
    # Don't import test_events since we need to redefine it
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
    initialize_event_sources,  # Make sure we have event sources initialized
)
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.event import Event
from sologm.models.event_source import EventSource


@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    # Set a default width for the console to avoid type errors
    mock.width = 80
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def oracle_manager(mock_anthropic_client, db_session):
    """Create an OracleManager with a test session."""
    from sologm.core.oracle import OracleManager

    return OracleManager(anthropic_client=mock_anthropic_client, session=db_session)


@pytest.fixture
def test_events(db_session, test_game, test_scene):
    """Create test events with source_id instead of source."""
    # Get the source ID for "manual"
    source_obj = (
        db_session.query(EventSource).filter(EventSource.name == "manual").first()
    )
    if not source_obj:
        # Create it if it doesn't exist
        source_obj = EventSource.create(name="manual")
        db_session.add(source_obj)
        db_session.commit()

    events = [
        Event.create(
            game_id=test_game.id,
            scene_id=test_scene.id,
            description=f"Test event {i}",
            source_id=source_obj.id,
        )
        for i in range(1, 3)
    ]
    db_session.add_all(events)
    db_session.commit()
    return events


# Explicitly expose the helper functions needed for testing
@pytest.fixture
def display_helpers():
    """Expose display helper functions for testing."""
    from sologm.cli.utils.display import (
        _create_empty_oracle_panel,
        _create_dice_rolls_panel,
        _create_events_panel,
    )

    return {
        "create_empty_oracle_panel": _create_empty_oracle_panel,
        "create_dice_rolls_panel": _create_dice_rolls_panel,
        "create_events_panel": _create_events_panel,
    }
