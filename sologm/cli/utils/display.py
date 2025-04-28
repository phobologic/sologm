"""Display helpers for CLI output."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sologm.cli.utils.styled_text import StyledText

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Format strings for consistent metadata presentation
METADATA_SEPARATOR = " • "


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to max_length and add ellipsis if needed.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation
    Returns:
        Truncated text with ellipsis if needed
    """
    logger.debug(f"Truncating text of length {len(text)} to max_length {max_length}")

    # Handle edge cases
    if not text:
        return ""
    if max_length <= 3:
        logger.debug("Max length too small, returning ellipsis only")
        return "..."
    if len(text) <= max_length:
        logger.debug("Text already within max length, returning unchanged")
        return text

    # Ensure we keep exactly max_length characters including the ellipsis
    logger.debug(f"Truncating text to {max_length - 3} chars plus ellipsis")
    return text[: max_length - 3] + "..."


# --- display_dice_roll removed, moved to RichRenderer ---


# --- display_interpretation removed, moved to RichRenderer ---


# --- display_events_table removed, moved to RichRenderer ---


# --- display_games_table removed, moved to RichRenderer ---


# --- display_scenes_table removed, moved to RichRenderer ---


# --- display_interpretation_set removed, moved to RichRenderer ---


# --- display_game_status and its helpers removed, moved to RichRenderer ---


def format_metadata(items: Dict[str, Any]) -> str:
    """Format metadata items consistently.

    Args:
        items: Dictionary of metadata key-value pairs

    Returns:
        Formatted metadata string with consistent separators
    """
    # This function is kept for backward compatibility
    # It returns a plain string version of the styled metadata
    return StyledText.format_metadata(items, METADATA_SEPARATOR).plain


# --- display_interpretation_status removed, moved to RichRenderer ---


# --- display_act_ai_generation_results removed, moved to RichRenderer ---


# --- display_act_completion_success removed, moved to RichRenderer ---


# --- display_act_ai_feedback_prompt removed, moved to RichRenderer ---


# --- display_act_edited_content_preview removed, moved to RichRenderer ---


def get_event_context_header(
    game_name: str,
    scene_title: str,
    scene_description: str,
    recent_events: Optional[List] = None,
    act_info: Optional[str] = None,
) -> str:
    """Create a context header for event editing.

    Args:
        game_name: Name of the current game
        scene_title: Title of the current scene
        scene_description: Description of the current scene
        recent_events: Optional list of recent events
        act_info: Optional act information string

    Returns:
        Formatted context header as a string
    """
    # Create context information for the editor
    # This returns a plain string as it's used for editor context headers
    context_info = f"Game: {game_name}\n"

    if act_info:
        context_info += f"Act: {act_info}\n"

    context_info += (
        f"Scene: {scene_title}\n\nScene Description:\n{scene_description}\n\n"
    )

    # Add recent events if any
    if recent_events:
        context_info += "Recent Events:\n"
        for i, event in enumerate(recent_events, 1):
            # Get the source name instead of the source object
            source_name = (
                event.source.name
                if hasattr(event.source, "name")
                else str(event.source)
            )
            context_info += f"{i}. [{source_name}] {event.description}\n"
        context_info += "\n"

    return context_info
