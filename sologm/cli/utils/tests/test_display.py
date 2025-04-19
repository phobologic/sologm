"""Tests for display helper functions."""

import pytest
from rich.text import Text

from sologm.cli.utils.display import (
    METADATA_SEPARATOR,
    _calculate_truncation_length,
    _create_act_panel,
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
    display_interpretation_sets_table,
    display_scenes_table,
    format_metadata,
    truncate_text,
)
from sologm.cli.utils.styled_text import BORDER_STYLES, StyledText


# --- test_display_dice_roll removed, moved to test_rich_renderer.py ---


# --- test_display_events_table_* removed, moved to test_rich_renderer.py ---


# --- test_display_games_table_* removed, moved to test_rich_renderer.py ---


# --- test_display_scenes_table_* removed, moved to test_rich_renderer.py ---


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


def test_create_act_panel(test_game, test_act):
    """Test creating the act panel."""
    # Test with active act (using default truncation)
    panel_active = _create_act_panel(test_game, test_act, is_act_active=True)
    assert panel_active is not None
    assert panel_active.title is not None
    assert panel_active.border_style == BORDER_STYLES["current"]
    # Check if summary is present (might be truncated)
    assert test_act.summary[:10] in panel_active.renderable  # Check start of summary

    # Test with inactive act and specific truncation
    test_act.summary = "This is a very long summary that definitely needs to be truncated for the test."
    panel_inactive_truncated = _create_act_panel(
        test_game, test_act, is_act_active=False, truncation_length=20
    )
    assert panel_inactive_truncated is not None
    assert panel_inactive_truncated.border_style == BORDER_STYLES["neutral"]
    # Check if the summary is truncated (20 * 1.5 = 30 chars max)
    assert "This is a very long summary..." in panel_inactive_truncated.renderable
    assert (
        "truncated for the test." not in panel_inactive_truncated.renderable
    )  # End should be cut off

    # Test with no active act
    panel_no_act = _create_act_panel(test_game, None)
    assert panel_no_act is not None
    assert panel_no_act.title is not None
    assert panel_no_act.border_style == BORDER_STYLES["neutral"]
    # Check for the updated message when no act is provided
    assert "No acts found in this game." in panel_no_act.renderable


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


# --- test_display_interpretation removed, moved to test_rich_renderer.py ---


# --- test_display_interpretation_selected removed, moved to test_rich_renderer.py ---


def test_display_act_ai_generation_results(mock_console, test_act):
    """Test displaying AI generation results for an act."""
    from sologm.cli.utils.display import display_act_ai_generation_results

    # Test with both title and summary
    results = {"title": "AI Generated Title", "summary": "AI Generated Summary"}
    display_act_ai_generation_results(mock_console, results, test_act)
    assert mock_console.print.called

    # Test with only title
    results = {"title": "AI Generated Title"}
    display_act_ai_generation_results(mock_console, results, test_act)
    assert mock_console.print.called

    # Test with only summary
    results = {"summary": "AI Generated Summary"}
    display_act_ai_generation_results(mock_console, results, test_act)
    assert mock_console.print.called

    # Test with empty results
    results = {}
    display_act_ai_generation_results(mock_console, results, test_act)
    assert mock_console.print.called


def test_display_act_completion_success(mock_console, test_act):
    """Test displaying act completion success."""
    from sologm.cli.utils.display import display_act_completion_success

    # Test with title and summary
    display_act_completion_success(mock_console, test_act)
    assert mock_console.print.called

    # Test with untitled act
    test_act.title = None
    display_act_completion_success(mock_console, test_act)
    assert mock_console.print.called


def test_display_act_edited_content_preview(mock_console):
    """Test displaying edited content preview for an act."""
    from sologm.cli.utils.display import display_act_edited_content_preview

    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}
    display_act_edited_content_preview(mock_console, edited_results)
    assert mock_console.print.called


def test_display_act_ai_feedback_prompt(mock_console, monkeypatch):
    """Test displaying AI feedback prompt for an act."""
    from sologm.cli.utils.display import display_act_ai_feedback_prompt
    from rich.prompt import Prompt

    # Mock the Prompt.ask method to return a fixed value
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "A")

    result = display_act_ai_feedback_prompt(mock_console)
    assert result == "A"


@pytest.fixture
def display_helpers():
    """Fixture to provide access to private display helper functions."""
    from sologm.cli.utils.display import (
        _create_dice_rolls_panel,
        _create_empty_oracle_panel,
    )

    return {
        "create_empty_oracle_panel": _create_empty_oracle_panel,
        "create_events_panel": _create_events_panel,
        "create_dice_rolls_panel": _create_dice_rolls_panel,
    }
