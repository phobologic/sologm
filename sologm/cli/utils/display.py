"""Display helpers for CLI output."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.cli.utils.styled_text import BORDER_STYLES, StyledText
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene, SceneManager
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.scene import SceneStatus

if TYPE_CHECKING:
    from sologm.core.oracle import OracleManager

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


def display_game_status(
    console: Console,
    game: Game,
    latest_act: Optional[Act],
    latest_scene: Optional[Scene],
    recent_events: List[Event],
    scene_manager: Optional[SceneManager] = None,
    oracle_manager: Optional["OracleManager"] = None,
    recent_rolls: Optional[List[DiceRoll]] = None,
    is_act_active: bool = False,  # Default to False if no act
    is_scene_active: bool = False,  # Default to False if no scene
) -> None:
    """Display comprehensive game status in a compact layout.

    Shows the latest act and scene, indicating their active status.

    Args:
        console: Rich console instance
        game: Current game
        latest_act: The most recent act in the game.
        latest_scene: The most recent scene in the latest act.
        recent_events: Recent events (limited list, typically from latest scene).
        scene_manager: Optional scene manager for additional context (like prev scene).
        oracle_manager: Optional oracle manager for interpretation context.
        recent_rolls: Optional list of recent dice rolls (typically from latest scene).
        is_act_active: Whether the latest_act is flagged as active.
        is_scene_active: Whether the latest_scene is flagged as active.
    """
    logger.debug(
        f"Displaying game status for {game.id} with {len(recent_events)} events. "
        f"Latest Act: {latest_act.id if latest_act else 'None'} (Active: {is_act_active}). "
        f"Latest Scene: {latest_scene.id if latest_scene else 'None'} (Active: {is_scene_active})."
    )

    # Calculate display dimensions
    truncation_length = _calculate_truncation_length(console)

    # Display game header
    console.print(_create_game_header_panel(game, console))

    # Display act panel (pass latest act, its status, and truncation_length)
    console.print(
        _create_act_panel(
            game, latest_act, is_act_active, truncation_length=truncation_length
        )
    )

    # Create and display the main grid with scene and events info
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column("Left", ratio=1)
    grid.add_column("Right", ratio=1)

    # Add scene panels and events panel to main grid (pass latest scene and its status)
    left_grid = _create_scene_panels_grid(
        game, latest_scene, scene_manager, console, is_scene_active
    )
    events_panel = _create_events_panel(recent_events, truncation_length)
    grid.add_row(left_grid, events_panel)
    console.print(grid)

    # Create a new grid for oracle and dice rolls
    logger.debug("Creating bottom grid for oracle and dice rolls")
    bottom_grid = Table.grid(expand=True, padding=(0, 1))
    bottom_grid.add_column("Oracle", ratio=7)  # 70% width
    bottom_grid.add_column("Dice", ratio=3)  # 30% width

    # Create oracle panel (always show, but may be empty)
    logger.debug("Creating oracle panel")
    oracle_panel = (
        _create_oracle_panel(
            game,
            latest_scene,  # Use latest_scene
            oracle_manager,
            truncation_length,
        )
        or _create_empty_oracle_panel()
    )
    logger.debug(f"Oracle panel created: {oracle_panel is not None}")

    # Create dice rolls panel
    logger.debug(f"Creating dice rolls panel with {len(recent_rolls or [])} rolls")
    dice_panel = _create_dice_rolls_panel(recent_rolls or [])
    logger.debug(f"Dice panel created: {dice_panel is not None}")

    # Add panels to the bottom grid
    logger.debug("Adding panels to bottom grid")
    bottom_grid.add_row(oracle_panel, dice_panel)
    logger.debug("Printing bottom grid with oracle and dice panels")
    console.print(bottom_grid)


def _calculate_truncation_length(console: Console) -> int:
    """Calculate appropriate truncation length based on console width."""
    logger.debug("Calculating appropriate truncation length for console")
    try:
        console_width = console.width
        logger.debug(f"Console width detected: {console_width} characters")
        # Calculate appropriate truncation length based on console width
        # Since we're using a two-column layout, each column gets roughly half the width
        # Subtract some space for borders, padding, and formatting
        truncation_length = max(40, int(console_width) - 10)
        logger.debug(
            f"Using truncation length of {truncation_length} "
            f"characters for event descriptions"
        )
        return truncation_length
    except (TypeError, ValueError) as e:
        # Default to a reasonable truncation length if console width is not available
        logger.debug(
            f"Could not determine console width due to error: {e}, using default value"
        )
        return 40


def _create_act_panel(
    game: Game,
    latest_act: Optional[Act] = None,
    is_act_active: bool = False,
    truncation_length: int = 80,  # Add parameter with a default
) -> Panel:
    """Create a panel showing the latest act information."""
    st = StyledText

    panel_title_text = "Latest Act"  # Always refer to latest
    border_style = BORDER_STYLES["neutral"]  # Default border

    if not latest_act:
        # No acts found
        panel_content = st.subtitle(
            "No acts found in this game. Create one with 'sologm act create'."
        )
        return Panel(
            panel_content,
            title=st.title(panel_title_text),
            border_style=border_style,
            expand=True,
            title_align="left",
        )

    # Set border if active
    if is_act_active:
        border_style = BORDER_STYLES["current"]  # Use current border if active

    # Create panel content with act information
    panel_content = Text()
    # ... (use latest_act to build title_text) ...
    if latest_act.title:
        title_text = st.title(f"Act {latest_act.sequence}: {latest_act.title}")
    else:
        untitled_text = Text("Untitled Act", style="italic")
        title_text = st.combine(st.title(f"Act {latest_act.sequence}: "), untitled_text)
    panel_content.append(title_text)

    if latest_act.summary:
        # Calculate a max length suitable for a full-width panel
        # Let's use 1.5 times the base truncation length as an example
        max_summary_length = int(truncation_length * 1.5)
        logger.debug(f"Truncating act summary to max length {max_summary_length}")
        truncated_summary = truncate_text(
            latest_act.summary, max_length=max_summary_length
        )
        panel_content.append("\n")
        panel_content.append(truncated_summary)  # Append the truncated summary

    # Add metadata including status
    metadata = {
        "Status": st.success("Active") if is_act_active else st.warning("Inactive"),
        "Scenes": len(latest_act.scenes) if hasattr(latest_act, "scenes") else 0,
        "Created": latest_act.created_at.strftime("%Y-%m-%d"),
    }
    panel_content.append("\n")
    panel_content.append(st.format_metadata(metadata))

    return Panel(
        panel_content,
        title=st.title(panel_title_text),
        border_style=border_style,  # Use dynamic border
        expand=True,
        title_align="left",
    )


def _create_game_header_panel(game: Game, console: Optional[Console] = None) -> Panel:
    """Create the game info header panel.

    Args:
        game: The game to display information for
        console: Optional console instance to determine width for text truncation

    Returns:
        A Panel containing the game header information
    """
    logger.debug(f"Creating game header panel for game {game.id}")

    st = StyledText

    # Create metadata with consistent formatting
    metadata = {
        "Created": game.created_at.strftime("%Y-%m-%d"),
        "Acts": len(game.acts) if hasattr(game, "acts") else 0,
        "Scenes": sum(len(act.scenes) for act in game.acts)
        if hasattr(game, "acts")
        else len(game.scenes),
    }

    # Create a title with consistent styling
    panel_title = st.combine(
        st.title_blue(game.name),
        " (",
        st.title_timestamp(game.slug),
        ") ",
        st.timestamp(game.id),
    )

    # Create content with consistent styling
    # Truncate description to fit approximately 3 lines based on console width
    console_width = 80  # Default fallback width

    if console:
        # Use the provided console instance
        console_width = console.width
        logger.debug(f"Using provided console width: {console_width}")
    else:
        # Fall back to trying to get a console if none was provided
        logger.debug("No console provided, attempting to determine width")
        try:
            from rich.console import get_console

            console_width = get_console().width
        except Exception:
            logger.debug("Could not determine console width, using default of 80")

    # Calculate chars per line (accounting for margins/padding)
    chars_per_line = max(40, console_width - 10)
    # For 3 lines, allow roughly 3x that many characters
    max_desc_length = chars_per_line * 3

    truncated_description = truncate_text(game.description, max_length=max_desc_length)
    logger.debug(
        f"Truncated game description from {len(game.description)} to {len(truncated_description)} chars"
    )

    # Create content with styled text
    content = Text()
    content.append(truncated_description)
    content.append("\n")

    # Add metadata with dim style
    metadata_text = st.format_metadata(metadata)
    metadata_text.stylize("dim")
    content.append(metadata_text)

    logger.debug("Game header panel created")
    return Panel(
        content,
        title=panel_title,
        expand=True,
        border_style=BORDER_STYLES["game_info"],
        title_align="left",
    )


def _create_scene_panels_grid(
    game: Game,
    latest_scene: Optional[Scene],
    scene_manager: Optional[SceneManager],
    console: Optional[Console] = None,
    is_scene_active: bool = False,
) -> Table:
    """Create a grid containing latest and previous scene panels.

    Args:
        game: The game to display information for
        latest_scene: The most recent scene in the latest act.
        scene_manager: Optional scene manager for retrieving previous scene.
        console: Optional console instance to determine width for text truncation.
        is_scene_active: Whether the latest_scene is flagged as active.

    Returns:
        A Table grid containing the scene panels.
    """
    logger.debug(
        f"Creating scene panels grid for game {game.id} (Latest Scene Active: {is_scene_active})"
    )

    st = StyledText

    # Calculate truncation length for scene descriptions
    console_width = 80  # Default fallback width
    if console:
        console_width = console.width
        logger.debug(f"Using provided console width: {console_width}")

    # For scene descriptions in a two-column layout, use about 1/3 of console width
    # This accounts for the panel taking up roughly half the screen, minus borders/padding
    chars_per_line = max(30, int(console_width / 3))
    # Allow for about 4 lines of text
    max_desc_length = chars_per_line * 8

    logger.debug(
        f"Chars per line: {chars_per_line}, Max description length: {max_desc_length}"
    )

    # Determine title and border for the latest scene panel
    latest_scene_title_text = "Latest Scene"
    latest_scene_border_style = BORDER_STYLES["neutral"]  # Default border

    # Create latest scene panel
    scenes_content = Text()
    if latest_scene:
        logger.debug(f"Including latest scene {latest_scene.id} in panel")
        # ... (use latest_scene to build content, act_info, truncated_description) ...
        truncated_description = truncate_text(
            latest_scene.description, max_length=max_desc_length
        )
        logger.debug(
            f"Truncated latest scene description from {len(latest_scene.description)} to {len(truncated_description)} chars"
        )
        act_info = ""
        if hasattr(latest_scene, "act") and latest_scene.act:
            act_title = latest_scene.act.title or "Untitled Act"
            act_info = f"Act {latest_scene.act.sequence}: {act_title}\n"

        scenes_content = st.combine(
            st.subtitle(act_info) if act_info else Text(),
            st.title(latest_scene.title),
            "\n",
            truncated_description,
        )

        # Determine status string and border style
        if latest_scene.status == SceneStatus.COMPLETED:
            status_string = st.success("Completed")
            latest_scene_border_style = BORDER_STYLES["success"]
        elif is_scene_active:
            status_string = st.success("Active")
            latest_scene_border_style = BORDER_STYLES["current"]
        else:
            status_string = st.warning("Inactive")
            latest_scene_border_style = BORDER_STYLES["neutral"]

        # Add metadata including status
        metadata = {
            "Status": status_string,
            "Sequence": latest_scene.sequence,
            "Created": latest_scene.created_at.strftime("%Y-%m-%d"),
        }
        scenes_content.append("\n")
        scenes_content.append(st.format_metadata(metadata))

    else:
        logger.debug("No latest scene to display")
        scenes_content = st.subtitle("No scenes found in this context")
        latest_scene_title_text = "Scene Status"  # Adjust title if no scene at all

    scenes_panel = Panel(
        scenes_content,
        title=st.title(latest_scene_title_text),
        border_style=latest_scene_border_style,  # Use dynamic border
        title_align="left",
        expand=True,  # Ensure panel expands to fill available width
    )

    # Create previous scene panel (logic remains similar, finds scene before latest_scene)
    prev_scene = None
    if latest_scene and scene_manager:
        logger.debug(
            f"Attempting to get previous scene for latest scene {latest_scene.id}"
        )
        prev_scene = scene_manager.get_previous_scene(latest_scene.id)

    prev_scene_content = Text()
    if prev_scene:
        logger.debug(f"Including previous scene {prev_scene.id} in panel")
        # ... (get truncated_description, act_info for prev_scene) ...
        truncated_description = truncate_text(
            prev_scene.description, max_length=max_desc_length
        )
        logger.debug(
            f"Truncated previous scene description from {len(prev_scene.description)} to {len(truncated_description)} chars"
        )
        act_info = ""
        if hasattr(prev_scene, "act") and prev_scene.act:
            act_title = prev_scene.act.title or "Untitled Act"
            act_info = f"Act {prev_scene.act.sequence}: {act_title}\n"

        prev_scene_content = st.combine(
            st.subtitle(act_info) if act_info else Text(),
            st.title(prev_scene.title),
            "\n",
            truncated_description,
        )
        # Add metadata for previous scene (status is just its stored status)
        prev_metadata = {
            "Status": prev_scene.status.value,  # Display stored status
            "Sequence": prev_scene.sequence,
            "Created": prev_scene.created_at.strftime("%Y-%m-%d"),
        }
        prev_scene_content.append("\n")
        prev_scene_content.append(st.format_metadata(prev_metadata))
    else:
        logger.debug("No previous scene to display")
        prev_scene_content = st.subtitle("No previous scene")

    prev_scene_panel = Panel(
        prev_scene_content,
        title=st.title("Previous Scene"),
        border_style=BORDER_STYLES["game_info"],
        title_align="left",
        expand=True,  # Ensure panel expands to fill available width
    )

    # Create a nested grid for the left column to stack the scene panels
    left_grid = Table.grid(padding=(0, 1), expand=True)  # Make the grid expand
    left_grid.add_column(ratio=1)  # Use ratio to ensure column expands
    left_grid.add_row(scenes_panel)
    left_grid.add_row(prev_scene_panel)

    return left_grid


def _create_events_panel(recent_events: List[Event], truncation_length: int) -> Panel:
    """Create the recent events panel."""
    logger.debug(f"Creating events panel with {len(recent_events)} events")

    st = StyledText
    events_content = Text()

    if recent_events:
        # Calculate how many events we can reasonably show
        # Each event takes at least 3 lines (timestamp+source, description, blank)
        max_events_to_show = min(3, len(recent_events))  # Show at most 3 events
        logger.debug(f"Showing {max_events_to_show} of {len(recent_events)} events")

        events_shown = recent_events[:max_events_to_show]
        for i, event in enumerate(events_shown):
            # Get the source name instead of the source object
            source_name = (
                event.source.name
                if hasattr(event.source, "name")
                else str(event.source)
            )

            logger.debug(f"Adding event {event.id} to panel (source: {source_name})")

            # Add a newline between events
            if i > 0:
                events_content.append("\n\n")

            # Truncate long descriptions based on calculated width
            truncated_description = truncate_text(
                event.description, max_length=truncation_length
            )

            # Add event header with timestamp and source
            events_content.append(
                st.timestamp(event.created_at.strftime("%Y-%m-%d %H:%M"))
            )
            events_content.append(" ")
            events_content.append(st.category(f"({source_name})"))
            events_content.append("\n")
            events_content.append(truncated_description)
    else:
        logger.debug("No events to display in panel")
        events_content = st.subtitle("No recent events")

    # Create panel title
    panel_title = st.combine(
        st.title("Recent Events"), f" ({len(recent_events)} shown)"
    )

    # Use success border style for events as they represent completed actions
    return Panel(
        events_content,
        title=panel_title,
        border_style=BORDER_STYLES["success"],
        title_align="left",
    )


def _create_oracle_panel(
    game: Game,
    latest_scene: Optional[Scene],
    oracle_manager: Optional["OracleManager"],
    truncation_length: int,
) -> Optional[Panel]:
    """Create the oracle panel if applicable."""
    logger.debug(f"Creating oracle panel for game {game.id}")

    if not oracle_manager or not latest_scene:
        logger.debug("No oracle manager or latest scene, skipping oracle panel")
        return None

    # Check for current interpretation set using latest_scene.id
    current_interp_set = oracle_manager.get_current_interpretation_set(latest_scene.id)

    if current_interp_set:
        # Check if any interpretation is selected
        has_selection = any(
            interp.is_selected for interp in current_interp_set.interpretations
        )

        if not has_selection:
            logger.debug("Creating pending oracle panel")
            return _create_pending_oracle_panel(current_interp_set, truncation_length)

    # Try to get most recent interpretation using latest_scene.id
    recent_interp = oracle_manager.get_most_recent_interpretation(latest_scene.id)

    if recent_interp:
        logger.debug("Creating recent oracle panel")
        return _create_recent_oracle_panel(recent_interp[0], recent_interp[1])

    logger.debug("No oracle panel needed")
    return None


def _create_pending_oracle_panel(
    interp_set: InterpretationSet,
    truncation_length: int,
) -> Panel:
    """Create a panel for pending oracle interpretation."""
    logger.debug(f"Creating pending oracle panel for set {interp_set.id}")

    st = StyledText

    # Create panel content
    panel_content = Text()

    # Add header
    panel_content.append(st.warning("Open Oracle Interpretation:"))
    panel_content.append("\n")
    panel_content.append(st.subtitle("Context:"))
    panel_content.append(" ")
    panel_content.append(interp_set.context)
    panel_content.append("\n\n")

    # Add interpretation options
    for i, interp in enumerate(interp_set.interpretations, 1):
        logger.debug(f"Adding interpretation option {i}: {interp.id}")

        if i > 1:
            panel_content.append("\n\n")

        panel_content.append(st.title(f"{i}. {interp.title}"))
        panel_content.append("\n")
        panel_content.append(interp.description)

    # Add footer
    panel_content.append("\n\n")
    panel_content.append(
        st.subtitle("Use 'sologm oracle select' to choose an interpretation")
    )

    return Panel(
        panel_content,
        title=st.title("Pending Oracle Decision"),
        border_style=BORDER_STYLES["pending"],
        expand=True,
        title_align="left",
    )


def _create_recent_oracle_panel(
    interp_set: InterpretationSet,
    selected_interp: Interpretation,
) -> Panel:
    """Create a panel showing the most recent oracle interpretation."""
    logger.debug(
        f"Creating recent oracle panel for set {interp_set.id}, "
        f"interpretation {selected_interp.id}"
    )

    st = StyledText

    # Build the panel content
    panel_content = Text()

    # Add oracle results and context
    panel_content.append(st.subtitle("Oracle Results:"))
    panel_content.append(" ")
    panel_content.append(interp_set.oracle_results)
    panel_content.append("\n")
    panel_content.append(st.subtitle("Context:"))
    panel_content.append(" ")
    panel_content.append(interp_set.context)
    panel_content.append("\n\n")

    # Add selected interpretation
    panel_content.append(st.subtitle("Selected Interpretation:"))
    panel_content.append(" ")
    panel_content.append(st.title(selected_interp.title))
    panel_content.append("\n")
    panel_content.append(selected_interp.description)
    panel_content.append("\n\n")

    # Add other options header
    panel_content.append(st.subtitle("Other options were:"))

    # Add other interpretations that weren't selected
    for i, interp in enumerate(interp_set.interpretations, 1):
        if interp.id != selected_interp.id:
            panel_content.append("\n")
            panel_content.append(st.title(f"{i}. {interp.title}"))
            panel_content.append("\n")
            panel_content.append(interp.description)

    return Panel(
        panel_content,
        title=st.title("Previous Oracle Decision"),
        border_style=BORDER_STYLES["success"],
        expand=True,
        title_align="left",
    )


def _create_empty_oracle_panel() -> Panel:
    """Create an empty oracle panel when no oracle information is available."""
    logger.debug("Creating empty oracle panel")

    st = StyledText
    panel_content = st.subtitle("No oracle interpretations yet.")

    return Panel(
        panel_content,
        title=st.title("Oracle"),
        border_style=BORDER_STYLES["neutral"],
        expand=True,
        title_align="left",
    )


def _create_dice_rolls_panel(recent_rolls: List[DiceRoll]) -> Panel:
    """Create a panel showing recent dice rolls.

    Args:
        recent_rolls: List of recent dice rolls to display

    Returns:
        Panel containing formatted dice roll information
    """
    logger.debug(f"Creating dice rolls panel with {len(recent_rolls)} rolls")

    st = StyledText

    if not recent_rolls:
        logger.debug("No dice rolls to display")
        panel_content = st.subtitle("No recent dice rolls.")
    else:
        panel_content = Text()

        for i, roll in enumerate(recent_rolls):
            logger.debug(f"Formatting roll {i + 1}: {roll.notation} = {roll.total}")

            # Add spacing between rolls
            if i > 0:
                panel_content.append("\n\n")

            # Create roll header with notation and total
            roll_header = st.combine(
                st.title(roll.notation), " = ", st.success(str(roll.total))
            )
            panel_content.append(roll_header)

            # Add reason if available
            if roll.reason:
                logger.debug(f"Roll has reason: {roll.reason}")
                panel_content.append(" (")
                panel_content.append(st.subtitle(roll.reason))
                panel_content.append(")")

            # Add timestamp
            logger.debug(f"Roll timestamp: {roll.created_at}")
            panel_content.append("\n")
            panel_content.append(
                st.timestamp(roll.created_at.strftime("%Y-%m-%d %H:%M"))
            )

            # Add details for complex rolls
            if len(roll.individual_results) > 1:
                logger.debug(f"Roll has individual results: {roll.individual_results}")
                panel_content.append("\n")
                panel_content.append(st.category(str(roll.individual_results)))

    return Panel(
        panel_content,
        title=st.title("Recent Rolls"),
        border_style=BORDER_STYLES["neutral"],
        expand=True,
        title_align="left",
    )


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
