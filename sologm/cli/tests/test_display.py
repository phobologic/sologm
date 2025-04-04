"""Tests for display helper functions."""

from datetime import datetime, timezone
from typing import List
from unittest.mock import Mock

import pytest
from rich.console import Console

from sologm.cli.display import (
    display_dice_roll,
    display_events_table,
    display_game_info,
    display_games_table,
    display_interpretation,
    display_interpretation_set,
)
from sologm.core.dice import DiceRoll
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene


@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    return mock


@pytest.fixture
def sample_game() -> Game:
    """Create a sample game for testing."""
    return Game(
        id="game-1",
        name="Test Game",
        description="A test game",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        scenes=["scene-1", "scene-2"],
    )


@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing."""
    return Scene(
        id="scene-1",
        title="Test Scene",
        description="A test scene",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status="active",
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
        ),
        Event(
            id="event-2",
            description="Test event 2",
            source="oracle",
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
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
    return InterpretationSet(
        id="set-1",
        context="Test context",
        oracle_results="Test results",
        interpretations=[sample_interpretation],
        selected_interpretation=0,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


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


def test_display_interpretation_set_no_context(
    mock_console, sample_interpretation_set
):
    """Test displaying an interpretation set without context."""
    display_interpretation_set(
        mock_console, sample_interpretation_set, show_context=False
    )
    assert mock_console.print.called
