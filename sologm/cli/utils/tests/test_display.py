"""Tests for display helper functions."""

from rich.text import Text

from sologm.cli.utils.display import (
    METADATA_SEPARATOR,
    format_metadata,
    truncate_text,
)
from sologm.cli.utils.styled_text import StyledText

# --- test_display_dice_roll removed, moved to test_rich_renderer.py ---


# --- test_display_events_table_* removed, moved to test_rich_renderer.py ---


# --- test_display_games_table_* removed, moved to test_rich_renderer.py ---


# --- test_display_interpretation_selected removed, moved to test_rich_renderer.py ---


# --- test_display_interpretation_set removed, moved to test_rich_renderer.py ---


# --- test_display_interpretation_set_no_context removed, moved to test_rich_renderer.py ---


# --- test_display_game_status_* and helper tests removed, moved to test_rich_renderer.py ---


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


# --- test_display_interpretation_status removed, moved to test_rich_renderer.py ---


# --- test_display_act_ai_generation_results removed, moved to test_rich_renderer.py ---


# --- test_display_act_completion_success removed, moved to test_rich_renderer.py ---


# --- test_display_act_edited_content_preview removed, moved to test_rich_renderer.py ---


# --- test_display_act_ai_feedback_prompt removed, moved to test_rich_renderer.py ---
