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

    st = StyledText

    # Create title with consistent styling
    title_parts = []
    if roll.reason:
        title_parts.extend([st.title(f"{roll.reason}:"), " ", st.title(roll.notation)])
    else:
        title_parts.append(st.title(roll.notation))

    panel_title = st.combine(*title_parts)

    # Build details with consistent styling
    details = []

    if len(roll.individual_results) > 1:
        details.append(
            st.combine(
                st.subtitle("Rolls:"), " ", st.timestamp(str(roll.individual_results))
            )
        )

    if roll.modifier != 0:
        details.append(
            st.combine(st.subtitle("Modifier:"), " ", st.warning(f"{roll.modifier:+d}"))
        )

    details.append(
        st.combine(st.subtitle("Result:"), " ", st.title_success(str(roll.total)))
    )

    # Add timestamp metadata if available
    metadata = {}
    if roll.created_at:
        metadata["Time"] = roll.created_at.isoformat()

    # Create panel content
    panel_content = Text()

    # Add all details
    for i, detail in enumerate(details):
        if i > 0:
            panel_content.append("\n")
        panel_content.append(detail)

    # Add metadata if available
    if metadata:
        panel_content.append("\n")
        panel_content.append(st.format_metadata(metadata))

    # Use consistent border style for dice rolls (neutral information)
    panel = Panel(
        panel_content,
        title=panel_title,
        border_style=BORDER_STYLES["neutral"],
        expand=True,
        title_align="left",
    )
    console.print(panel)


def display_interpretation(
    console: Console,
    interp: Interpretation,
    selected: bool = False,
    sequence: Optional[int] = None,
) -> None:
    """Display a single interpretation.

    Args:
        console: Rich console instance
        interp: Interpretation to display
        selected: Whether this interpretation is selected
        sequence: Optional sequence number of the interpretation
    """
    logger.debug(
        f"Displaying interpretation {interp.id} (selected: {interp.is_selected})"
    )
    logger.debug(
        f"Interpretation title: '{interp.title}', created: {interp.created_at}"
    )

    st = StyledText

    # Create panel title with sequence number, title, selection indicator, and ID
    sequence_text = f"(#{sequence}) " if sequence is not None else ""

    # Build the title components
    title_parts = [st.title(f"{sequence_text}{interp.title}")]

    # Add selection indicator if selected
    if interp.is_selected or selected:
        title_parts.extend([" ", st.success("(Selected)")])

    # Add ID and slug
    title_parts.extend([" ", st.timestamp(f"({interp.slug} / {interp.id})")])

    # Combine into a single Text object
    panel_title = st.combine(*title_parts)

    # Determine border style based on selection status
    border_style = (
        BORDER_STYLES["success"]
        if (interp.is_selected or selected)
        else BORDER_STYLES["game_info"]
    )

    # Panel content is just the description
    panel = Panel(
        interp.description,
        title=panel_title,
        border_style=border_style,
        title_align="left",
    )
    console.print(panel)
    console.print()


def display_events_table(console: Console, events: List[Event], scene: Scene) -> None:
    """Display events in a formatted table.

    Args:
        console: Rich console instance
        events: List of events to display
        scene: The Scene to display events from.
    """
    logger.debug(
        f"Displaying events table for scene '{scene.title}' with {len(events)} events"
    )
    if not events:
        logger.debug(f"No events to display for scene '{scene.title}'")
        console.print(f"\nNo events in scene '{scene.title}'")
        return

    logger.debug(f"Creating table with {len(events)} events")

    st = StyledText

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=st.STYLES["timestamp"])
    table.add_column("Time", style=st.STYLES["timestamp"])
    table.add_column("Source", style=st.STYLES["category"])
    table.add_column("Description")

    # Add rows with consistent formatting
    for event in events:
        # Get the source name instead of the source object
        source_name = (
            event.source.name if hasattr(event.source, "name") else str(event.source)
        )

        table.add_row(
            event.id,
            event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            source_name,
            event.description,  # Show full description without truncation
        )

    # Create panel title
    panel_title = st.title(
        f"Events in game '{scene.act.game.name}', scene '{scene.title}'"
    )

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=panel_title,
        title_align="left",
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

    st = StyledText

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=st.STYLES["timestamp"])
    table.add_column("Name", style=st.STYLES["category"])
    table.add_column("Description")
    table.add_column("Acts", justify="right")
    table.add_column("Scenes", justify="right")
    table.add_column("Current", style=st.STYLES["success"], justify="center")

    # Add rows with consistent formatting
    for game in games:
        # Get acts and scenes count
        act_count = len(game.acts) if hasattr(game, "acts") else 0
        scene_count = (
            sum(len(act.scenes) for act in game.acts)
            if hasattr(game, "acts")
            else len(game.scenes)
        )

        is_active = active_game and game.id == active_game.id
        active_marker = "✓" if is_active else ""

        # Create game name with appropriate styling
        game_name = st.title(game.name).plain if is_active else game.name

        table.add_row(
            game.id,
            game_name,
            game.description,
            str(act_count),
            str(scene_count),
            active_marker,
        )

    # Create panel title
    panel_title = st.title("Games")

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=panel_title,
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

    st = StyledText

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=st.STYLES["timestamp"])
    table.add_column("Title", style=st.STYLES["category"])
    table.add_column("Description")
    table.add_column("Status", style=st.STYLES["success"])
    table.add_column("Current", style=st.STYLES["success"], justify="center")
    table.add_column("Sequence", justify="right")

    # Add rows with consistent formatting
    for scene in scenes:
        is_active = active_scene_id and scene.id == active_scene_id
        active_marker = "✓" if is_active else ""

        # Create scene title with appropriate styling
        scene_title = st.title(scene.title).plain if is_active else scene.title

        table.add_row(
            scene.id,
            scene_title,
            scene.description,
            scene.status.value,
            active_marker,
            str(scene.sequence),
        )

    # Create panel title
    panel_title = st.title("Scenes")

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=panel_title,
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

    st = StyledText

    # Get active act if available
    active_act = (
        next((act for act in game.acts if act.is_active), None)
        if hasattr(game, "acts")
        else None
    )

    # Count scenes across all acts
    scene_count = (
        sum(len(act.scenes) for act in game.acts)
        if hasattr(game, "acts")
        else len(game.scenes)
    )
    act_count = len(game.acts) if hasattr(game, "acts") else 0

    logger.debug(
        f"Game details: name='{game.name}', acts={act_count}, scenes={scene_count}"
    )

    # Create metadata with consistent formatting
    metadata = {
        "Created": game.created_at.strftime("%Y-%m-%d"),
        "Modified": game.modified_at.strftime("%Y-%m-%d"),
        "Acts": act_count,
        "Scenes": scene_count,
    }

    # Create panel content
    content = Text()
    content.append(st.subtitle(game.description))
    content.append("\n")
    content.append(st.format_metadata(metadata))

    if active_act:
        act_title = active_act.title or "Untitled Act"
        content.append("\nActive Act: ")
        content.append(st.title(f"Act {active_act.sequence}: {act_title}"))

    if active_scene:
        content.append("\nActive Scene: ")
        content.append(st.title(active_scene.title))

    # Create panel title
    panel_title = st.combine(
        st.title_blue(game.name),
        " (",
        st.title_timestamp(game.slug),
        ") ",
        st.timestamp(game.id),
    )

    panel = Panel(
        content,
        title=panel_title,
        border_style=BORDER_STYLES["game_info"],
        title_align="left",
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
    st = StyledText

    # Access interpretations relationship directly
    interpretation_count = len(interp_set.interpretations)

    logger.debug(
        f"Displaying interpretation set {interp_set.id} with "
        f"{interpretation_count} interpretations"
    )

    # Show context panel if requested
    if show_context:
        # Create context content
        context_content = st.combine(
            st.subtitle("Context:"),
            " ",
            interp_set.context,
            "\n",
            st.subtitle("Results:"),
            " ",
            interp_set.oracle_results,
        )

        # Create panel title
        panel_title = st.title("Oracle Interpretations")

        context_panel = Panel(
            context_content,
            title=panel_title,
            border_style=BORDER_STYLES["game_info"],
            title_align="left",
        )
        console.print(context_panel)
        console.print()

    # Display each interpretation with its sequence number
    for i, interp in enumerate(interp_set.interpretations, 1):
        display_interpretation(console, interp, sequence=i)

    # Show set ID with instruction
    instruction_panel = Panel(
        "Use this ID to select an interpretation with 'sologm oracle select'",
        title=st.timestamp(f"Interpretation Set: {interp_set.id}"),
        border_style=BORDER_STYLES["pending"],
        expand=False,
        title_align="left",
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
        f"act_id={scene.act_id if hasattr(scene, 'act_id') else 'unknown'}"
    )

    st = StyledText

    # Get act information
    act_info = ""
    if hasattr(scene, "act") and scene.act:
        act_title = scene.act.title or "Untitled Act"
        act_info = f"Act {scene.act.sequence}: {act_title}"

    # Create metadata with consistent formatting
    metadata = {
        "Status": scene.status.value,
        "Sequence": scene.sequence,
        "Act": act_info,
        "Created": scene.created_at.strftime("%Y-%m-%d"),
        "Modified": scene.modified_at.strftime("%Y-%m-%d"),
    }

    # Determine border style based on scene status
    border_style = BORDER_STYLES["current"]
    if scene.status.value == "COMPLETED":
        border_style = BORDER_STYLES["success"]

    # Create panel content
    panel_content = st.combine(
        st.subtitle(scene.description), "\n", st.format_metadata(metadata)
    )

    # Create panel title
    panel_title = st.combine(
        st.title_blue(scene.title), " ", st.timestamp(f"({scene.id})")
    )

    panel = Panel(
        panel_content, title=panel_title, border_style=border_style, title_align="left"
    )

    console.print(panel)


def display_game_status(
    console: Console,
    game: Game,
    active_scene: Optional[Scene],
    recent_events: List[Event],
    scene_manager: Optional[SceneManager] = None,
    oracle_manager: Optional["OracleManager"] = None,
    recent_rolls: Optional[List[DiceRoll]] = None,
) -> None:
    """Display comprehensive game status in a compact layout.

    Args:
        console: Rich console instance
        game: Current game
        active_scene: Active scene if any
        recent_events: Recent events (limited list)
        scene_manager: Optional scene manager for additional context
        oracle_manager: Optional oracle manager for interpretation context
        recent_rolls: Optional list of recent dice rolls
    """
    logger.debug(
        f"Displaying game status for {game.id} with {len(recent_events)} events and "
        f"active scene: {active_scene.id if active_scene else 'None'}"
    )

    # Calculate display dimensions
    truncation_length = _calculate_truncation_length(console)

    # Display game header
    console.print(_create_game_header_panel(game, console))

    # Get active act
    active_act = (
        next((act for act in game.acts if act.is_active), None)
        if hasattr(game, "acts")
        else None
    )

    # Display act panel
    console.print(_create_act_panel(game, active_act))

    # Create and display the main grid with scene and events info
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column("Left", ratio=1)
    grid.add_column("Right", ratio=1)

    # Add scene panels and events panel to main grid
    left_grid = _create_scene_panels_grid(game, active_scene, scene_manager, console)
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
            active_scene,
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


def _create_act_panel(game: Game, active_act: Optional[Act] = None) -> Panel:
    """Create a panel showing act information.

    Args:
        game: The current game
        active_act: The currently active act, if any

    Returns:
        Panel containing formatted act information
    """
    st = StyledText

    if not active_act:
        # No active act
        panel_content = st.subtitle(
            "No active act. Create one with 'sologm act create'."
        )
        return Panel(
            panel_content,
            title=st.title("Current Act"),
            border_style=BORDER_STYLES["neutral"],
            expand=True,
            title_align="left",
        )

    # Create panel content with act information
    panel_content = Text()

    # Add act title and sequence
    act_title = active_act.title or "[italic]Untitled Act[/italic]"
    panel_content.append(st.title(f"Act {active_act.sequence}: {act_title}"))

    # Add act description if available
    if active_act.description:
        panel_content.append("\n")
        panel_content.append(active_act.description)

    # Add metadata
    metadata = {
        "Status": active_act.status.value,
        "Scenes": len(active_act.scenes) if hasattr(active_act, "scenes") else 0,
        "Created": active_act.created_at.strftime("%Y-%m-%d"),
    }
    panel_content.append("\n")
    panel_content.append(st.format_metadata(metadata))

    return Panel(
        panel_content,
        title=st.title("Current Act"),
        border_style=BORDER_STYLES["current"],
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
    active_scene: Optional[Scene],
    scene_manager: Optional[SceneManager],
    console: Optional[Console] = None,
) -> Table:
    """Create a grid containing current and previous scene panels.

    Args:
        game: The game to display information for
        active_scene: The currently active scene, if any
        scene_manager: Optional scene manager for retrieving previous scene
        console: Optional console instance to determine width for text truncation

    Returns:
        A Table grid containing the scene panels
    """
    logger.debug(f"Creating scene panels grid for game {game.id}")

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

    # Create current scene panel with consistent styling
    scenes_content = Text()
    if active_scene:
        logger.debug(f"Including active scene {active_scene.id} in panel")
        truncated_description = truncate_text(
            active_scene.description, max_length=max_desc_length
        )
        logger.debug(
            f"Truncated active scene description from {len(active_scene.description)} to {len(truncated_description)} chars"
        )

        # Get act information for the scene
        act_info = ""
        if hasattr(active_scene, "act") and active_scene.act:
            act_title = active_scene.act.title or "Untitled Act"
            act_info = f"Act {active_scene.act.sequence}: {act_title}\n"

        scenes_content = st.combine(
            st.subtitle(act_info) if act_info else Text(),
            st.title(active_scene.title),
            "\n",
            truncated_description,
        )
    else:
        logger.debug("No active scene to display")
        scenes_content = st.subtitle("No active scene")

    scenes_panel = Panel(
        scenes_content,
        title=st.title("Current Scene"),
        border_style=BORDER_STYLES["current"],
        title_align="left",
        expand=True,  # Ensure panel expands to fill available width
    )

    # Create previous scene panel with consistent styling
    prev_scene = None
    if active_scene and scene_manager:
        logger.debug(
            f"Attempting to get previous scene for active scene {active_scene.id}"
        )
        prev_scene = scene_manager.get_previous_scene(active_scene.id)

    prev_scene_content = Text()
    if prev_scene:
        logger.debug(f"Including previous scene {prev_scene.id} in panel")
        truncated_description = truncate_text(
            prev_scene.description, max_length=max_desc_length
        )
        logger.debug(
            f"Truncated previous scene description from {len(prev_scene.description)} to {len(truncated_description)} chars"
        )

        # Get act information for the previous scene
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


def display_acts_table(
    console: Console, acts: List[Act], active_act_id: Optional[str] = None
) -> None:
    """Display acts in a formatted table.

    Args:
        console: Rich console instance
        acts: List of acts to display
        active_act_id: ID of the currently active act, if any
    """
    logger.debug(f"Displaying acts table with {len(acts)} acts")
    logger.debug(f"Active act ID: {active_act_id if active_act_id else 'None'}")
    if not acts:
        logger.debug("No acts found to display")
        console.print("No acts found. Create one with 'sologm act create'.")
        return

    st = StyledText

    # Create table without a title
    table = Table(
        border_style=BORDER_STYLES["game_info"],
    )

    # Add columns with consistent styling
    table.add_column("ID", style=st.STYLES["timestamp"])
    table.add_column("Sequence", justify="right")
    table.add_column("Title", style=st.STYLES["category"])
    table.add_column("Description")
    table.add_column("Status", style=st.STYLES["success"])
    table.add_column("Current", style=st.STYLES["success"], justify="center")

    # Add rows with consistent formatting
    for act in acts:
        is_active = active_act_id and act.id == active_act_id
        active_marker = "✓" if is_active else ""

        # Create act title with appropriate styling
        act_title = act.title if act.title else "[italic]Untitled Act[/italic]"
        act_title_styled = st.title(act_title).plain if is_active else act_title

        table.add_row(
            act.id,
            str(act.sequence),
            act_title_styled,
            act.description or "",
            act.status.value,
            active_marker,
        )

    # Create panel title
    panel_title = st.title("Acts")

    # Wrap the table in a panel with a title
    panel = Panel(
        table,
        title=panel_title,
        title_align="left",
        border_style=BORDER_STYLES["game_info"],
    )
    console.print(panel)


def display_act_info(console: Console, act: Act, game_name: str) -> None:
    """Display detailed information about an act.

    Args:
        console: Rich console instance
        act: Act to display
        game_name: Name of the game this act belongs to
    """
    logger.debug(f"Displaying act info for {act.id} (status: {act.status.value})")
    logger.debug(
        f"Act details: title='{act.title}', sequence={act.sequence}, "
        f"game_id={act.game_id}"
    )

    st = StyledText

    # Create metadata with consistent formatting
    metadata = {
        "Game": game_name,
        "Status": act.status.value,
        "Sequence": f"Act {act.sequence}",
        "Created": act.created_at.strftime("%Y-%m-%d"),
        "Modified": act.modified_at.strftime("%Y-%m-%d"),
    }

    # Determine border style based on act status
    border_style = (
        BORDER_STYLES["current"] if act.is_active else BORDER_STYLES["game_info"]
    )
    if act.status.value == "COMPLETED":
        border_style = BORDER_STYLES["success"]

    # Create panel content
    panel_content = Text()

    # Add description if available
    if act.description:
        panel_content.append(st.subtitle(act.description))
        panel_content.append("\n\n")

    # Add metadata
    panel_content.append(st.format_metadata(metadata))

    # Create panel title
    title_display = act.title or "[italic]Untitled Act[/italic]"
    panel_title = st.combine(
        st.title_blue(f"Act {act.sequence}: {title_display}"),
        " ",
        st.timestamp(f"({act.id})"),
    )

    panel = Panel(
        panel_content, title=panel_title, border_style=border_style, title_align="left"
    )

    console.print(panel)

    # Display scenes in this act if any
    if hasattr(act, "scenes") and act.scenes:
        console.print("\nScenes in this act:")
        for scene in act.scenes:
            active_marker = "[bold green]✓[/bold green] " if scene.is_active else ""
            status_style = "green" if scene.status.value == "COMPLETED" else "yellow"
            console.print(
                f"{active_marker}Scene {scene.sequence}: [bold]{scene.title}[/bold] [bold {status_style}]({scene.status.value})[/bold {status_style}]"
            )
    else:
        console.print("\nNo scenes in this act yet.")


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
