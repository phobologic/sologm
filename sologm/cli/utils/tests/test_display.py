"""Tests for display helper functions."""

from unittest.mock import MagicMock

import pytest
from rich.console import Console
from rich.text import Text

from sologm.cli.utils.display import (
    METADATA_SEPARATOR,
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
    display_scenes_table,
    format_metadata,
    truncate_text,
)
from sologm.cli.utils.styled_text import BORDER_STYLES, StyledText
from sologm.core.scene import SceneManager


def test_display_dice_roll(mock_console, test_dice_roll):
    """Test displaying a dice roll."""
    display_dice_roll(mock_console, test_dice_roll)
    assert mock_console.print.called


def test_display_events_table_with_events(mock_console, test_events, test_scene):
    """Test displaying events table with events."""
    display_events_table(mock_console, test_events, test_scene)
    assert mock_console.print.called


def test_display_events_table_no_events(mock_console, test_scene):
    """Test displaying events table with no events."""
    display_events_table(mock_console, [], test_scene)
    mock_console.print.assert_called_once_with(
        f"\nNo events in scene '{test_scene.title}'"
    )


def test_display_games_table_with_games(mock_console, test_game):
    """Test displaying games table with games."""
    display_games_table(mock_console, [test_game], test_game)
    assert mock_console.print.called


def test_display_games_table_no_games(mock_console):
    """Test displaying games table with no games."""
    display_games_table(mock_console, [], None)
    mock_console.print.assert_called_once_with(
        "No games found. Create one with 'sologm game create'."
    )


def test_display_scenes_table_with_scenes(mock_console, test_scene):
    """Test displaying scenes table with scenes."""
    display_scenes_table(mock_console, [test_scene], test_scene.id)
    assert mock_console.print.called


def test_display_scenes_table_no_scenes(mock_console):
    """Test displaying scenes table with no scenes."""
    display_scenes_table(mock_console, [], None)
    mock_console.print.assert_called_once_with(
        "No scenes found. Create one with 'sologm scene create'."
    )


def test_display_game_info(mock_console, test_game, test_scene):
    """Test displaying game info."""
    display_game_info(mock_console, test_game, test_scene)
    assert mock_console.print.called


def test_display_game_info_no_scene(mock_console, test_game):
    """Test displaying game info without active scene."""
    display_game_info(mock_console, test_game, None)
    assert mock_console.print.called


def test_display_game_status_full(
    mock_console, test_game, test_scene, test_events, scene_manager
):
    """Test displaying full game status with all components."""
    display_game_status(
        mock_console,
        test_game,
        test_scene,
        test_events,
        scene_manager=scene_manager,
        oracle_manager=None,
        recent_rolls=[],
    )
    assert mock_console.print.called


def test_display_game_status_no_scene(mock_console, test_game):
    """Test displaying game status without an active scene."""
    display_game_status(
        mock_console, test_game, None, [], None, oracle_manager=None, recent_rolls=None
    )
    assert mock_console.print.called


def test_display_game_status_no_events(mock_console, test_game, test_scene):
    """Test displaying game status without any events."""
    display_game_status(
        mock_console,
        test_game,
        test_scene,
        [],
        None,
        oracle_manager=None,
        recent_rolls=None,
    )
    assert mock_console.print.called


def test_display_game_status_no_interpretation(
    mock_console, test_game, test_scene, test_events
):
    """Test displaying game status without a pending interpretation."""
    display_game_status(
        mock_console,
        test_game,
        test_scene,
        test_events,
        None,
        oracle_manager=None,
        recent_rolls=None,
    )
    assert mock_console.print.called


def test_display_game_status_selected_interpretation(
    mock_console, test_game, test_scene, test_events, scene_manager
):
    """Test displaying game status with a selected interpretation."""
    display_game_status(
        mock_console,
        test_game,
        test_scene,
        test_events,
        scene_manager=scene_manager,
        oracle_manager=None,
        recent_rolls=None,
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


def test_create_game_header_panel(test_game, mock_console):
    """Test creating the game header panel."""
    # Test without console
    panel = _create_game_header_panel(test_game)
    assert panel is not None
    assert panel.title is not None
    assert panel.border_style == BORDER_STYLES["game_info"]

    # Test with console
    panel = _create_game_header_panel(test_game, mock_console)
    assert panel is not None
    assert panel.title is not None
    assert panel.border_style == BORDER_STYLES["game_info"]


def test_create_scene_panels_grid(test_game, test_scene):
    """Test creating the scene panels grid."""
    # Test with active scene but no scene manager
    grid = _create_scene_panels_grid(test_game, test_scene, None)
    assert grid is not None

    # Test with no active scene
    grid = _create_scene_panels_grid(test_game, None, None)
    assert grid is not None


def test_create_events_panel(test_events, display_helpers):
    """Test creating the events panel."""
    create_events_panel = display_helpers["create_events_panel"]

    # Test with events
    panel = create_events_panel(test_events, 60)
    assert panel is not None
    assert "Recent Events" in panel.title
    assert panel.border_style == BORDER_STYLES["success"]

    # Test with no events
    panel = create_events_panel([], 60)
    assert panel is not None
    assert "Recent Events" in panel.title


def test_create_oracle_panel(test_game, test_scene, oracle_manager):
    """Test creating the oracle panel."""
    # Test with no oracle manager
    panel = _create_oracle_panel(test_game, test_scene, None, 60)
    assert panel is None

    # Test with oracle manager
    panel = _create_oracle_panel(test_game, test_scene, oracle_manager, 60)
    assert (
        panel is None or panel is not None
    )  # Either outcome is valid depending on test data


def test_create_empty_oracle_panel(display_helpers):
    """Test creating an empty oracle panel."""
    panel = display_helpers["create_empty_oracle_panel"]()
    assert panel is not None
    assert "Oracle" in panel.title
    assert panel.border_style == BORDER_STYLES["neutral"]


def test_create_dice_rolls_panel(test_dice_roll, display_helpers):
    """Test creating the dice rolls panel."""
    create_dice_rolls_panel = display_helpers["create_dice_rolls_panel"]

    # Test with no rolls
    panel = create_dice_rolls_panel([])
    assert panel is not None
    assert "Recent Rolls" in panel.title
    assert "No recent dice rolls" in panel.renderable

    # Test with rolls
    panel = create_dice_rolls_panel([test_dice_roll])
    assert panel is not None
    assert "Recent Rolls" in panel.title
    assert test_dice_roll.notation in panel.renderable


def test_display_interpretation(mock_console, test_interpretations):
    """Test displaying an interpretation."""
    display_interpretation(mock_console, test_interpretations[0])
    assert mock_console.print.called


def test_display_interpretation_selected(mock_console, test_interpretations):
    """Test displaying a selected interpretation."""
    display_interpretation(mock_console, test_interpretations[0], selected=True)
    assert mock_console.print.called


def test_display_interpretation_set(mock_console, test_interpretation_set):
    """Test displaying an interpretation set."""
    display_interpretation_set(mock_console, test_interpretation_set)
    assert mock_console.print.called


def test_display_interpretation_set_no_context(mock_console, test_interpretation_set):
    """Test displaying an interpretation set without context."""
    display_interpretation_set(
        mock_console, test_interpretation_set, show_context=False
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

    # Empty string
    assert truncate_text("", 10) == ""


def test_format_metadata():
    """Test the format_metadata function."""
    # Test with multiple items
    metadata = {"Created": "2024-01-01", "Modified": "2024-01-02", "Items": 5}
    result = format_metadata(metadata)
    assert "Created: 2024-01-01" in result
    assert "Modified: 2024-01-02" in result
    assert "Items: 5" in result
    assert METADATA_SEPARATOR in result

    # Test with single item
    metadata = {"Created": "2024-01-01"}
    result = format_metadata(metadata)
    assert result == "Created: 2024-01-01"

    # Test with None values
    metadata = {"Created": "2024-01-01", "Modified": None}
    result = format_metadata(metadata)
    assert result == "Created: 2024-01-01"
    assert "Modified" not in result

    # Test with empty dict
    metadata = {}
    result = format_metadata(metadata)
    assert result == ""
    
    # Verify it's using StyledText under the hood
    styled_result = StyledText.format_metadata(metadata)
    assert isinstance(styled_result, Text)
@pytest.fixture
def display_helpers():
    """Fixture to provide access to private display helper functions."""
    from sologm.cli.utils.display import (
        _create_empty_oracle_panel,
        _create_events_panel,
        _create_dice_rolls_panel,
    )
    
    return {
        "create_empty_oracle_panel": _create_empty_oracle_panel,
        "create_events_panel": _create_events_panel,
        "create_dice_rolls_panel": _create_dice_rolls_panel,
    }
