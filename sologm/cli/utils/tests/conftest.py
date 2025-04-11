"""Shared test fixtures for CLI utility tests."""

from unittest.mock import MagicMock, Mock

import pytest
from rich.console import Console

# Import fixtures from core tests to reuse them
from sologm.core.tests.conftest import (
    test_scene,
)
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.act import Act  # Import Act model
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


# If test_act fixture isn't being properly imported, define it here
@pytest.fixture
def test_act(db_session, test_game):
    """Create a test act if not already imported."""

    # Check if we already have an act for this game
    existing_act = db_session.query(Act).filter(Act.game_id == test_game.id).first()
    if existing_act:
        return existing_act

    act = Act.create(
        game_id=test_game.id,
        title="Test Act",
        description="A test act",
        sequence=1,
    )
    act.is_active = True
    db_session.add(act)
    db_session.commit()
    return act


@pytest.fixture
def test_scene(db_session, test_act):
    """Create a test scene."""
    from sologm.models.scene import Scene

    # Check if we already have a scene for this act
    existing_scene = db_session.query(Scene).filter(Scene.act_id == test_act.id).first()
    if existing_scene:
        return existing_scene

    scene = Scene.create(
        act_id=test_act.id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
    )
    scene.is_active = True
    db_session.add(scene)
    db_session.commit()
    return scene


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
        _create_dice_rolls_panel,
        _create_empty_oracle_panel,
        _create_events_panel,
    )

    return {
        "create_empty_oracle_panel": _create_empty_oracle_panel,
        "create_dice_rolls_panel": _create_dice_rolls_panel,
        "create_events_panel": _create_events_panel,
    }
