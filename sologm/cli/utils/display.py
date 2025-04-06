"""Display helpers for CLI output."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene, SceneManager
from sologm.models.dice import DiceRoll

if TYPE_CHECKING:
    from sologm.core.oracle import OracleManager

logger = logging.getLogger(__name__)

# Border style constants based on content type
BORDER_STYLES = {
    "game_info": "blue",  # Game information
    "current": "cyan",  # Current/active content
    "success": "green",  # Success/completed content
    "pending": "yellow",  # Pending actions/decisions
    "neutral": "bright_black",  # Neutral information (like dice rolls)
}

# Text style constants based on data type
TEXT_STYLES = {
    "timestamp": "cyan",  # Timestamps and IDs
    "category": "magenta",  # Categories and sources
    "success": "green",  # Success indicators and selected items
    "warning": "yellow",  # Warnings and pending actions
    "title": "bold",  # Titles and important identifiers
    "subtitle": "dim",  # Supplementary information and descriptions
}

# Format strings for consistent metadata presentation
METADATA_FORMAT = "{key}: {value}"
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


def display_dice_roll(console: Console, roll: DiceRoll) -> None:
    """Display a dice roll result.

    Args:
        console: Rich console instance
        roll: DiceRoll model to display
    """
    logger.debug(f"Displaying dice roll: {roll.notation} (total: {roll.total})")
    logger.debug(
        f"Individual results: {roll.individual_results}, modifier: {roll.modifier}"
    )

    # Create title with consistent styling
    title = Text()
    if roll.reason:
        title.append(f"{roll.reason}: ", style=f"{TEXT_STYLES['title']} blue")
    title.append(roll.notation, style=TEXT_STYLES["title"])

    # Build details with consistent styling
    details = Text()
    if len(roll.individual_results) > 1:
        details.append("Rolls: ", style=TEXT_STYLES["subtitle"])
        details.append(str(roll.individual_results), style=TEXT_STYLES["timestamp"])
        details.append("\n")

    if roll.modifier != 0:
        details.append("Modifier: ", style=TEXT_STYLES["subtitle"])
        details.append(f"{roll.modifier:+d}", style=TEXT_STYLES["warning"])
        details.append("\n")

    details.append("Result: ", style=TEXT_STYLES["subtitle"])
    details.append(
        str(roll.total), style=f"{TEXT_STYLES['title']} {TEXT_STYLES['success']}"
    )

    # Add timestamp if available
    if roll.created_at:
        details.append("\nTime: ", style=TEXT_STYLES["subtitle"])
        details.append(roll.created_at.isoformat(), style=TEXT_STYLES["timestamp"])

    # Use consistent border style for dice rolls (neutral information)
    panel = Panel(
        details, title=title, border_style=BORDER_STYLES["neutral"], expand=False
    )
    console.print(panel)


def display_interpretation(
    console: Console, interp: Interpretation, selected: bool = False
) -> None:
    """Display a single interpretation.

    Args:
        console: Rich console instance
        interp: Interpretation to display
        selected: Whether this interpretation is selected
    """
    logger.debug(
        f"Displaying interpretation {interp.id} (selected: {interp.is_selected})"
    )
    logger.debug(
        f"Interpretation title: '{interp.title}', created: {interp.created_at}"
    )

    # Extract the numeric part of the ID if it follows the pattern "interp-N"
    id_number = interp.id.split("-")[1] if "-" in interp.id else interp.id[:8]

    # Format title with consistent styling
    title_line = f"[{TEXT_STYLES['title']}]{interp.title}[/{TEXT_STYLES['title']}]"
    if interp.is_selected or selected:
        title_line += (
            f" [{TEXT_STYLES['success']}](Selected)[/{TEXT_STYLES['success']}]"
        )

    # Determine border style based on selection status
    border_style = (
        BORDER_STYLES["success"]
        if (interp.is_selected or selected)
        else BORDER_STYLES["game_info"]
    )

    # Create panel with consistent styling
    panel = Panel(
        Text.from_markup(f"{title_line}\n{interp.description}"),
        title=Text.from_markup(
            f"[{TEXT_STYLES['timestamp']}]Interpretation {id_number}[/{TEXT_STYLES['timestamp']}]"
        ),
        border_style=border_style,
    )
    console.print(panel)
    console.print()


def display_events_table(
    console: Console, events: List[Event], scene_title: str
) -> None:
    """Display events in a formatted table.

    Args:
        console: Rich console instance
        events: List of events to display
        scene_title: Title of the scene
    """
    logger.debug(
        f"Displaying events table for scene '{scene_title}' with {len(events)} events"
    )
    if not events:
        logger.debug(f"No events to display for scene '{scene_title}'")
        console.print(f"\nNo events in scene '{scene_title}'")
        return

    logger.debug(f"Creating table with {len(events)} events")

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("Time", style=TEXT_STYLES["timestamp"])
    table.add_column("Source", style=TEXT_STYLES["category"])
    table.add_column("Description")

    # Add rows with consistent formatting
    for event in events:
        table.add_row(
            event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            event.source,
            truncate_text(event.description, max_length=80),
        )

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=f"[{TEXT_STYLES['title']}]Events in scene '{scene_title}'[/{TEXT_STYLES['title']}]",
        title_justify="left",
        border_style=BORDER_STYLES["game_info"],
    )
    console.print(panel)


def display_games_table(
    console: Console, games: List[Game], active_game: Optional[Game] = None
) -> None:
    """Display games in a formatted table.

    Args:
        console: Rich console instance
        games: List of games to display
        active_game: Currently active game, if any
    """
    logger.debug(f"Displaying games table with {len(games)} games")
    logger.debug(f"Active game: {active_game.id if active_game else 'None'}")
    if not games:
        logger.debug("No games found to display")
        console.print("No games found. Create one with 'sologm game create'.")
        return

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=TEXT_STYLES["timestamp"])
    table.add_column("Name", style=TEXT_STYLES["category"])
    table.add_column("Description")
    table.add_column("Scenes", justify="right")
    table.add_column("Current", style=TEXT_STYLES["success"], justify="center")

    # Add rows with consistent formatting
    for game in games:
        # Access scenes relationship directly
        scene_count = len(game.scenes)

        is_active = active_game and game.id == active_game.id
        active_marker = "✓" if is_active else ""

        # Use different styling for active game
        name_style = f"[{TEXT_STYLES['title']}]" if is_active else ""
        name_style_end = f"[/{TEXT_STYLES['title']}]" if is_active else ""

        table.add_row(
            game.id,
            f"{name_style}{game.name}{name_style_end}",
            game.description,
            str(scene_count),
            active_marker,
        )

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=f"[{TEXT_STYLES['title']}]Games[/{TEXT_STYLES['title']}]",
        title_align="left",
        border_style=BORDER_STYLES["game_info"],
    )
    console.print(panel)


def display_scenes_table(
    console: Console, scenes: List[Scene], active_scene_id: Optional[str] = None
) -> None:
    """Display scenes in a formatted table.

    Args:
        console: Rich console instance
        scenes: List of scenes to display
        active_scene_id: ID of the currently active scene, if any
    """
    logger.debug(f"Displaying scenes table with {len(scenes)} scenes")
    logger.debug(f"Active scene ID: {active_scene_id if active_scene_id else 'None'}")
    if not scenes:
        logger.debug("No scenes found to display")
        console.print("No scenes found. Create one with 'sologm scene create'.")
        return

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=TEXT_STYLES["timestamp"])
    table.add_column("Title", style=TEXT_STYLES["category"])
    table.add_column("Description")
    table.add_column("Status", style=TEXT_STYLES["success"])
    table.add_column("Current", style=TEXT_STYLES["success"], justify="center")
    table.add_column("Sequence", justify="right")

    # Add rows with consistent formatting
    for scene in scenes:
        is_active = active_scene_id and scene.id == active_scene_id
        active_marker = "✓" if is_active else ""

        # Use different styling for active scene
        title_style = f"[{TEXT_STYLES['title']}]" if is_active else ""
        title_style_end = f"[/{TEXT_STYLES['title']}]" if is_active else ""

        table.add_row(
            scene.id,
            f"{title_style}{scene.title}{title_style_end}",
            scene.description,
            scene.status.value,
            active_marker,
            str(scene.sequence),
        )

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=f"[{TEXT_STYLES['title']}]Scenes[/{TEXT_STYLES['title']}]",
        title_align="left",
        border_style=BORDER_STYLES["game_info"],
    )
    console.print(panel)


def display_game_info(
    console: Console, game: Game, active_scene: Optional[Scene] = None
) -> None:
    """Display detailed information about a game.

    Args:
        console: Rich console instance
        game: Game to display
        active_scene: Active scene, if any
    """
    logger.debug(
        f"Displaying game info for {game.id} with active scene: "
        f"{active_scene.id if active_scene else 'None'}"
    )

    # Access scenes relationship directly
    scene_count = len(game.scenes)
    logger.debug(f"Game details: name='{game.name}', scenes={scene_count}")

    # Create metadata with consistent formatting
    metadata = {
        "Created": game.created_at.strftime("%Y-%m-%d"),
        "Modified": game.modified_at.strftime("%Y-%m-%d"),
        "Scenes": scene_count,
    }

    # Create panel with consistent styling
    panel_content = (
        f"[{TEXT_STYLES['subtitle']}]{game.description}[/{TEXT_STYLES['subtitle']}]\n"
        f"{format_metadata(metadata)}"
    )

    if active_scene:
        panel_content += f"\nActive Scene: [{TEXT_STYLES['title']}]{active_scene.title}[/{TEXT_STYLES['title']}]"

    panel_title = (
        f"[{TEXT_STYLES['title']} bright_blue]{game.name}[/{TEXT_STYLES['title']} bright_blue] "
        f"([{TEXT_STYLES['title']} {TEXT_STYLES['timestamp']}]{game.slug}[/{TEXT_STYLES['title']} {TEXT_STYLES['timestamp']}]) "
        f"[{TEXT_STYLES['timestamp']}]{game.id}[/{TEXT_STYLES['timestamp']}]"
    )

    panel = Panel(
        panel_content, title=panel_title, border_style=BORDER_STYLES["game_info"]
    )

    console.print(panel)


def display_interpretation_set(
    console: Console,
    interp_set: InterpretationSet,
    show_context: bool = True,
) -> None:
    """Display a full interpretation set.

    Args:
        console: Rich console instance
        interp_set: InterpretationSet to display
        show_context: Whether to show context information
    """
    # Access interpretations relationship directly
    interpretation_count = len(interp_set.interpretations)

    logger.debug(
        f"Displaying interpretation set {interp_set.id} with "
        f"{interpretation_count} interpretations"
    )

    # Show context panel if requested
    if show_context:
        context_content = (
            f"[{TEXT_STYLES['subtitle']}]Context:[/{TEXT_STYLES['subtitle']}] {interp_set.context}\n"
            f"[{TEXT_STYLES['subtitle']}]Results:[/{TEXT_STYLES['subtitle']}] {interp_set.oracle_results}"
        )

        context_panel = Panel(
            context_content,
            title=f"[{TEXT_STYLES['title']}]Oracle Interpretations[/{TEXT_STYLES['title']}]",
            border_style=BORDER_STYLES["game_info"],
        )
        console.print(context_panel)
        console.print()

    # Display each interpretation
    for i, interp in enumerate(interp_set.interpretations, 1):
        display_interpretation(console, interp)

    # Show set ID with instruction
    instruction_panel = Panel(
        "Use this ID to select an interpretation with 'sologm oracle select'",
        title=f"[{TEXT_STYLES['timestamp']}]Interpretation Set: {interp_set.id}[/{TEXT_STYLES['timestamp']}]",
        border_style=BORDER_STYLES["pending"],
        expand=False,
    )
    console.print(instruction_panel)


def display_scene_info(console: Console, scene: Scene) -> None:
    """Display detailed information about a scene.

    Args:
        console: Rich console instance
        scene: Scene to display
    """
    logger.debug(f"Displaying scene info for {scene.id} (status: {scene.status.value})")
    logger.debug(
        f"Scene details: title='{scene.title}', sequence={scene.sequence}, "
        f"game_id={scene.game_id}"
    )

    # Create metadata with consistent formatting
    metadata = {
        "Status": scene.status.value,
        "Sequence": scene.sequence,
        "Created": scene.created_at.strftime("%Y-%m-%d"),
        "Modified": scene.modified_at.strftime("%Y-%m-%d"),
    }

    # Determine border style based on scene status
    border_style = BORDER_STYLES["current"]
    if scene.status.value == "COMPLETED":
        border_style = BORDER_STYLES["success"]

    # Create panel with consistent styling
    panel_content = (
        f"[{TEXT_STYLES['subtitle']}]{scene.description}[/{TEXT_STYLES['subtitle']}]\n"
        f"{format_metadata(metadata)}"
    )

    panel_title = (
        f"[{TEXT_STYLES['title']} bright_blue]{scene.title}[/{TEXT_STYLES['title']} bright_blue] "
        f"[{TEXT_STYLES['timestamp']}]({scene.id})[/{TEXT_STYLES['timestamp']}]"
    )

    panel = Panel(panel_content, title=panel_title, border_style=border_style)

    console.print(panel)


def display_game_status(
    console: Console,
    game: Game,
    active_scene: Optional[Scene],
    recent_events: List[Event],
    scene_manager: Optional[SceneManager] = None,
    oracle_manager: Optional["OracleManager"] = None,
) -> None:
    """Display comprehensive game status in a compact layout.

    Args:
        console: Rich console instance
        game: Current game
        active_scene: Active scene if any
        recent_events: Recent events (limited list)
        scene_manager: Optional scene manager for additional context
        oracle_manager: Optional oracle manager for interpretation context
    """
    logger.debug(
        f"Displaying game status for {game.id} with {len(recent_events)} events and "
        f"active scene: {active_scene.id if active_scene else 'None'}"
    )

    # Calculate display dimensions
    truncation_length = _calculate_truncation_length(console)

    # Display game header
    console.print(_create_game_header_panel(game))

    # Create and display the main grid with scene and events info
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column("Left", ratio=1)
    grid.add_column("Right", ratio=1)

    # Add scene panels and events panel to main grid
    left_grid = _create_scene_panels_grid(game, active_scene, scene_manager)
    events_panel = _create_events_panel(recent_events, truncation_length)
    grid.add_row(left_grid, events_panel)
    console.print(grid)

    # Display oracle panel if applicable
    oracle_panel = _create_oracle_panel(
        game,
        active_scene,
        oracle_manager,
        truncation_length,
    )
    if oracle_panel:
        console.print(oracle_panel)


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


def _create_game_header_panel(game: Game) -> Panel:
    """Create the game info header panel."""
    logger.debug(f"Creating game header panel for game {game.id}")

    # Access scenes relationship directly
    scene_count = len(game.scenes)

    # Create metadata with consistent formatting
    metadata = {"Created": game.created_at.strftime("%Y-%m-%d"), "Scenes": scene_count}
    formatted_metadata = format_metadata(metadata)

    # Create a title with consistent styling
    panel_title = (
        f"[{TEXT_STYLES['title']} bright_blue]{game.name}[/{TEXT_STYLES['title']} bright_blue] "
        f"([{TEXT_STYLES['title']} {TEXT_STYLES['timestamp']}]{game.slug}[/{TEXT_STYLES['title']} {TEXT_STYLES['timestamp']}]) "
        f"[{TEXT_STYLES['timestamp']}]{game.id}[/{TEXT_STYLES['timestamp']}]"
    )

    # Create content with consistent styling
    game_info = (
        f"[{TEXT_STYLES['subtitle']}]{game.description}[/{TEXT_STYLES['subtitle']}]\n"
        f"{formatted_metadata}"
    )

    logger.debug("Game header panel created")
    return Panel(
        game_info,
        title=panel_title,
        expand=True,
        border_style=BORDER_STYLES["game_info"],
    )


def _create_scene_panels_grid(
    game: Game, active_scene: Optional[Scene], scene_manager: Optional[SceneManager]
) -> Table:
    """Create a grid containing current and previous scene panels."""
    logger.debug(f"Creating scene panels grid for game {game.id}")

    # Create current scene panel with consistent styling
    scenes_content = ""
    if active_scene:
        logger.debug(f"Including active scene {active_scene.id} in panel")
        scenes_content = (
            f"[{TEXT_STYLES['title']}]{active_scene.title}[/{TEXT_STYLES['title']}]\n"
            f"[{TEXT_STYLES['subtitle']}]{active_scene.description}[/{TEXT_STYLES['subtitle']}]"
        )
    else:
        logger.debug("No active scene to display")
        scenes_content = (
            f"[{TEXT_STYLES['subtitle']}]No active scene[/{TEXT_STYLES['subtitle']}]"
        )

    scenes_panel = Panel(
        scenes_content,
        title=f"[{TEXT_STYLES['title']}]Current Scene[/{TEXT_STYLES['title']}]",
        border_style=BORDER_STYLES["current"],
    )

    # Create previous scene panel with consistent styling
    prev_scene = None
    if active_scene and scene_manager:
        logger.debug(
            f"Attempting to get previous scene for active scene {active_scene.id}"
        )
        prev_scene = scene_manager.get_previous_scene(game.id, active_scene)

    prev_scene_content = ""
    if prev_scene:
        logger.debug(f"Including previous scene {prev_scene.id} in panel")
        prev_scene_content = (
            f"[{TEXT_STYLES['title']}]{prev_scene.title}[/{TEXT_STYLES['title']}]\n"
            f"[{TEXT_STYLES['subtitle']}]{prev_scene.description}[/{TEXT_STYLES['subtitle']}]"
        )
    else:
        logger.debug("No previous scene to display")
        prev_scene_content = (
            f"[{TEXT_STYLES['subtitle']}]No previous scene[/{TEXT_STYLES['subtitle']}]"
        )

    prev_scene_panel = Panel(
        prev_scene_content,
        title=f"[{TEXT_STYLES['title']}]Previous Scene[/{TEXT_STYLES['title']}]",
        border_style=BORDER_STYLES["game_info"],
    )

    # Create a nested grid for the left column to stack the scene panels
    left_grid = Table.grid(padding=(0, 1))
    left_grid.add_column()
    left_grid.add_row(scenes_panel)
    left_grid.add_row(prev_scene_panel)

    return left_grid


def _create_events_panel(recent_events: List[Event], truncation_length: int) -> Panel:
    """Create the recent events panel."""
    logger.debug(f"Creating events panel with {len(recent_events)} events")
    events_content = ""

    if recent_events:
        # Calculate how many events we can reasonably show
        # Each event takes at least 3 lines (timestamp+source, description, blank)
        max_events_to_show = min(3, len(recent_events))  # Show at most 3 events
        logger.debug(f"Showing {max_events_to_show} of {len(recent_events)} events")

        events_shown = recent_events[:max_events_to_show]
        for event in events_shown:
            logger.debug(f"Adding event {event.id} to panel (source: {event.source})")
            # Truncate long descriptions based on calculated width
            truncated_description = truncate_text(
                event.description, max_length=truncation_length
            )
            events_content += (
                f"[{TEXT_STYLES['timestamp']}]{event.created_at.strftime('%Y-%m-%d %H:%M')}[/{TEXT_STYLES['timestamp']}] "
                f"[{TEXT_STYLES['category']}]({event.source})[/{TEXT_STYLES['category']}]\n"
                f"{truncated_description}\n\n"
            )
    else:
        logger.debug("No events to display in panel")
        events_content = (
            f"[{TEXT_STYLES['subtitle']}]No recent events[/{TEXT_STYLES['subtitle']}]"
        )

    # Use success border style for events as they represent completed actions
    return Panel(
        events_content.rstrip(),
        title=f"[{TEXT_STYLES['title']}]Recent Events[/{TEXT_STYLES['title']}] ({len(recent_events)} shown)",
        border_style=BORDER_STYLES["success"],
    )


def _create_oracle_panel(
    game: Game,
    active_scene: Optional[Scene],
    oracle_manager: Optional["OracleManager"],
    truncation_length: int,
) -> Optional[Panel]:
    """Create the oracle panel if applicable."""
    logger.debug(f"Creating oracle panel for game {game.id}")

    if not oracle_manager or not active_scene:
        logger.debug("No oracle manager or active scene, skipping oracle panel")
        return None

    # Check for current interpretation set
    current_interp_set = oracle_manager.get_current_interpretation_set(active_scene.id)

    if current_interp_set:
        # Check if any interpretation is selected
        has_selection = any(
            interp.is_selected for interp in current_interp_set.interpretations
        )

        if not has_selection:
            logger.debug("Creating pending oracle panel")
            return _create_pending_oracle_panel(current_interp_set, truncation_length)

    # Try to get most recent interpretation
    recent_interp = oracle_manager.get_most_recent_interpretation(active_scene.id)

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

    # Show truncated versions of the options
    options_text = ""

    for i, interp in enumerate(interp_set.interpretations, 1):
        logger.debug(f"Adding interpretation option {i}: {interp.id}")
        truncated_title = truncate_text(interp.title, truncation_length // 2)
        options_text += f"[{TEXT_STYLES['subtitle']}]{i}.[/{TEXT_STYLES['subtitle']}] {truncated_title}\n"

    # Create panel with consistent styling for pending actions
    panel_content = (
        f"[{TEXT_STYLES['warning']}]Open Oracle Interpretation:[/{TEXT_STYLES['warning']}]\n"
        f"[{TEXT_STYLES['subtitle']}]Context:[/{TEXT_STYLES['subtitle']}] {interp_set.context}\n\n"
        f"{options_text}\n"
        f"[{TEXT_STYLES['subtitle']}]Use 'sologm oracle select' to choose an interpretation[/{TEXT_STYLES['subtitle']}]"
    )

    return Panel(
        panel_content,
        title=f"[{TEXT_STYLES['title']}]Pending Oracle Decision[/{TEXT_STYLES['title']}]",
        border_style=BORDER_STYLES["pending"],
        expand=True,
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

    # Build the panel content with consistent styling
    panel_content = (
        f"[{TEXT_STYLES['success']}]Last Oracle Interpretation:[/{TEXT_STYLES['success']}]\n"
        f"[{TEXT_STYLES['title']}]Oracle Results:[/{TEXT_STYLES['title']}] {interp_set.oracle_results}\n"
        f"[{TEXT_STYLES['title']}]Context:[/{TEXT_STYLES['title']}] {interp_set.context}\n"
        f"[{TEXT_STYLES['title']}]Selected:[/{TEXT_STYLES['title']}] {selected_interp.title}\n"
        f"[{TEXT_STYLES['subtitle']}]{selected_interp.description}[/{TEXT_STYLES['subtitle']}]"
    )

    return Panel(
        panel_content,
        title=f"[{TEXT_STYLES['title']}]Previous Oracle Decision[/{TEXT_STYLES['title']}]",
        border_style=BORDER_STYLES["success"],
        expand=True,
    )


def format_metadata(items: Dict[str, Any]) -> str:
    """Format metadata items consistently.

    Args:
        items: Dictionary of metadata key-value pairs

    Returns:
        Formatted metadata string with consistent separators
    """
    formatted_items = []

    for key, value in items.items():
        if value is not None:
            formatted_items.append(METADATA_FORMAT.format(key=key, value=value))

    return METADATA_SEPARATOR.join(formatted_items)
