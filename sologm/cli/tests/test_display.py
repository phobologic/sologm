"""Tests for display helper functions."""

from datetime import datetime, timezone
from typing import List
from unittest.mock import Mock, MagicMock

import pytest
from rich.console import Console

from sologm.cli.display import (
    _calculate_truncation_length,
    _create_events_panel,
    _create_game_header_panel,
    _create_oracle_panel,
    _create_scene_panels_grid,
    display_dice_roll,
    display_events_table,
    display_game_info,
    display_game_status,
    display_games_table,
    display_interpretation,
    display_interpretation_set,
    truncate_text,
)
from sologm.core.dice import DiceRoll
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene, SceneStatus


@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    # Set a default width for the console to avoid type errors
    mock.width = 80
    return mock


@pytest.fixture
def sample_game() -> Game:
    """Create a sample game for testing."""
    # Create a mock Game object that's not tied to SQLAlchemy
    game = MagicMock(spec=Game)
    game.id = "game-1"
    game.name = "Test Game"
    game.description = "A test game"
    game.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    game.modified_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    # Make scenes a property that returns a list with 2 items
    game.scenes = MagicMock()
    game.scenes.__len__.return_value = 2
    return game


@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing."""
    return Scene(
        id="scene-1",
        title="Test Scene",
        description="A test scene",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status=SceneStatus.ACTIVE,
        game_id="test-game",
        sequence=1,
    )


@pytest.fixture
def sample_events() -> List[Event]:
    """Create a list of sample events for testing."""
    return [
        Event(
            id="event-1",
            description="Test event 1",
            source="manual",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            game_id="test-game",
            scene_id="test-scene",
        ),
        Event(
            id="event-2",
            description="Test event 2",
            source="oracle",
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            game_id="test-game",
            scene_id="test-scene",
        ),
    ]


@pytest.fixture
def sample_dice_roll() -> DiceRoll:
    """Create a sample dice roll for testing."""
    return DiceRoll(
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
        total=12,
        reason="Test roll",
    )


@pytest.fixture
def sample_interpretation() -> Interpretation:
    """Create a sample interpretation for testing."""
    return Interpretation(
        id="interp-1",
        title="Test Interpretation",
        description="A test interpretation",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_interpretation_set(sample_interpretation) -> InterpretationSet:
    """Create a sample interpretation set for testing."""
    # Create a mock InterpretationSet that's not tied to SQLAlchemy
    interp_set = MagicMock(spec=InterpretationSet)
    interp_set.id = "set-1"
    interp_set.context = "Test context"
    interp_set.oracle_results = "Test results"
    # Create a mock for interpretations that behaves like a list
    interpretations_mock = MagicMock()
    interpretations_mock.__len__.return_value = 1
    interpretations_mock.__iter__.return_value = iter([sample_interpretation])
    interpretations_mock.__getitem__.return_value = sample_interpretation
    interp_set.interpretations = interpretations_mock
    # Instead of selected_interpretation which doesn't exist
    interp_set.selected_interpretation_id = sample_interpretation.id
    interp_set.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interp_set.scene_id = "test-scene"
    return interp_set


def test_display_dice_roll(mock_console, sample_dice_roll):
    """Test displaying a dice roll."""
    display_dice_roll(mock_console, sample_dice_roll)
    assert mock_console.print.called


def test_display_events_table_with_events(mock_console, sample_events):
    """Test displaying events table with events."""
    display_events_table(mock_console, sample_events, "Test Scene")
    assert mock_console.print.called


def test_display_events_table_no_events(mock_console):
    """Test displaying events table with no events."""
    display_events_table(mock_console, [], "Test Scene")
    mock_console.print.assert_called_once_with("\nNo events in scene 'Test Scene'")


def test_display_games_table_with_games(mock_console, sample_game):
    """Test displaying games table with games."""
    display_games_table(mock_console, [sample_game], sample_game)
    assert mock_console.print.called


def test_display_games_table_no_games(mock_console):
    """Test displaying games table with no games."""
    display_games_table(mock_console, [], None)
    mock_console.print.assert_called_once_with(
        "No games found. Create one with 'sologm game create'."
    )


def test_display_game_info(mock_console, sample_game, sample_scene):
    """Test displaying game info."""
    display_game_info(mock_console, sample_game, sample_scene)
    assert mock_console.print.called


def test_display_game_info_no_scene(mock_console, sample_game):
    """Test displaying game info without active scene."""
    display_game_info(mock_console, sample_game, None)
    assert mock_console.print.called


def test_display_game_status_full(
    mock_console, sample_game, sample_scene, sample_events
):
    """Test displaying full game status with all components."""
    # Create a mock SceneManager
    scene_manager = MagicMock(spec=SceneManager)
    scene_manager.get_previous_scene.return_value = None
    
    current_interpretation = {
        "context": "Test context",
        "selected_interpretation": None,
    }
    display_game_status(
        mock_console,
        sample_game,
        sample_scene,
        sample_events,
        current_interpretation,
        scene_manager=scene_manager,
        oracle_manager=None,
    )
    assert mock_console.print.called


def test_display_game_status_no_scene(mock_console, sample_game):
    """Test displaying game status without an active scene."""
    display_game_status(mock_console, sample_game, None, [], None, oracle_manager=None)
    assert mock_console.print.called


def test_display_game_status_no_events(mock_console, sample_game, sample_scene):
    """Test displaying game status without any events."""
    display_game_status(
        mock_console, sample_game, sample_scene, [], None, oracle_manager=None
    )
    assert mock_console.print.called


def test_display_game_status_no_interpretation(
    mock_console, sample_game, sample_scene, sample_events
):
    """Test displaying game status without a pending interpretation."""
    display_game_status(
        mock_console,
        sample_game,
        sample_scene,
        sample_events,
        None,
        oracle_manager=None,
    )
    assert mock_console.print.called


def test_display_game_status_selected_interpretation(
    mock_console, sample_game, sample_scene, sample_events
):
    """Test displaying game status with a selected interpretation."""
    # Create a mock SceneManager
    scene_manager = MagicMock(spec=SceneManager)
    scene_manager.get_previous_scene.return_value = None
    
    current_interpretation = {
        "context": "Test context",
        "selected_interpretation": 0,
    }
    display_game_status(
        mock_console,
        sample_game,
        sample_scene,
        sample_events,
        current_interpretation,
        scene_manager=scene_manager,
        oracle_manager=None,
    )
    assert mock_console.print.called


def test_calculate_truncation_length(mock_console):
    """Test the truncation length calculation."""
    # Test with a valid console width
    mock_console.width = 100
    result = _calculate_truncation_length(mock_console)
    assert result == 90  # 100 - 10

    # Test with a small console width
    mock_console.width = 30
    result = _calculate_truncation_length(mock_console)
    assert result == 40  # min value

    # Test with an invalid console width
    mock_console.width = None
    result = _calculate_truncation_length(mock_console)
    assert result == 40  # default value


def test_create_game_header_panel(sample_game):
    """Test creating the game header panel."""
    panel = _create_game_header_panel(sample_game)
    assert panel is not None
    assert panel.title is None
    assert panel.border_style == "blue"


def test_create_scene_panels_grid(sample_game, sample_scene):
    """Test creating the scene panels grid."""
    # Test with active scene but no scene manager
    grid = _create_scene_panels_grid(sample_game, sample_scene, None)
    assert grid is not None

    # Test with no active scene
    grid = _create_scene_panels_grid(sample_game, None, None)
    assert grid is not None


def test_create_events_panel(sample_events):
    """Test creating the events panel."""
    # Test with events
    panel = _create_events_panel(sample_events, 60)
    assert panel is not None
    assert panel.title == f"Recent Events ({len(sample_events)} shown)"
    assert panel.border_style == "green"

    # Test with no events
    panel = _create_events_panel([], 60)
    assert panel is not None
    assert panel.title == "Recent Events (0 shown)"


def test_create_oracle_panel(sample_game, sample_scene):
    """Test creating the oracle panel."""
    # Test with no interpretation reference
    panel = _create_oracle_panel(sample_game, sample_scene, None, 60)
    assert panel is None

    # Create a mock oracle manager
    oracle_manager = MagicMock()
    oracle_manager.get_current_interpretation_set.return_value = None
    oracle_manager.get_most_recent_interpretation.return_value = None

    # Test with oracle manager
    panel = _create_oracle_panel(sample_game, sample_scene, oracle_manager, 60)
    assert panel is None


def test_display_interpretation(mock_console, sample_interpretation):
    """Test displaying an interpretation."""
    display_interpretation(mock_console, sample_interpretation)
    assert mock_console.print.called


def test_display_interpretation_selected(mock_console, sample_interpretation):
    """Test displaying a selected interpretation."""
    display_interpretation(mock_console, sample_interpretation, selected=True)
    assert mock_console.print.called


def test_display_interpretation_set(mock_console, sample_interpretation_set):
    """Test displaying an interpretation set."""
    display_interpretation_set(mock_console, sample_interpretation_set)
    assert mock_console.print.called


def test_display_interpretation_set_no_context(mock_console, sample_interpretation_set):
    """Test displaying an interpretation set without context."""
    display_interpretation_set(
        mock_console, sample_interpretation_set, show_context=False
    )
    assert mock_console.print.called


def test_truncate_text():
    """Test the truncate_text function."""
    # Short text should remain unchanged
    assert truncate_text("Short text", 20) == "Short text"

    # Long text should be truncated with ellipsis
    long_text = "This is a very long text that should be truncated"
    assert truncate_text(long_text, 20) == "This is a very lo..."

    # Edge case: max_length <= 3
    assert truncate_text("Any text", 3) == "..."
