"""Tests for the RichRenderer class."""

# Add necessary imports
from typing import List  # Added for Interpretation list type hint
import pytest
from unittest.mock import MagicMock
from rich.console import Console
from rich.panel import Panel  # Import Panel for assertion

from sologm.cli.rendering.rich_renderer import RichRenderer
from sologm.models.dice import DiceRoll
from sologm.models.game import Game  # <-- Added import
from sologm.models.oracle import Interpretation
from sologm.models.scene import Scene


# Add mock_console fixture if not already present globally
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width for consistent testing if needed
    console.width = 100
    return console


# --- Adapted Test (Red Phase - Expecting Failure) ---
def test_display_dice_roll(mock_console: MagicMock, test_dice_roll: DiceRoll):
    """Test displaying a dice roll using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call will raise NotImplementedError initially, causing the test to fail.
    renderer.display_dice_roll(test_dice_roll)

    # This assertion will only be reached once the implementation is added (Green Phase).
    mock_console.print.assert_called()
    # Verify that a Panel object was printed
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- Tests for display_interpretation (Moved & Adapted) ---


def test_display_interpretation(
    mock_console: MagicMock, test_interpretations: List[Interpretation]
):
    """Test displaying an interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation(test_interpretations[0])

    # Assertions will run after implementation
    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


def test_display_interpretation_selected(
    mock_console: MagicMock, test_interpretations: List[Interpretation]
):
    """Test displaying a selected interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation(test_interpretations[0], selected=True)

    # Assertions will run after implementation
    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


# --- Add other tests below ---


# --- Tests for display_game_info (Moved & Adapted) ---


def test_display_game_info(mock_console: MagicMock, test_game: Game, test_scene: Scene):
    """Test displaying game info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_game_info(test_game, test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


def test_display_game_info_no_scene(mock_console: MagicMock, test_game: Game):
    """Test displaying game info without active scene using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_game_info(test_game, None)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- End Tests for display_game_info ---


# --- Tests for display_act_info (Moved & Adapted) ---


def test_display_act_info(mock_console: MagicMock, test_act: Act, test_game: Game):
    """Test displaying act info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_act_info(test_act, test_game.name)

    # Assertions will run after implementation
    # Expecting two prints: one for the main act panel, one for the scenes panel/table
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert isinstance(args2[0], Panel)


# --- End Tests for display_act_info ---


def test_display_scene_info(mock_console: MagicMock, test_scene: Scene):
    """Test displaying scene info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_scene_info(test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
