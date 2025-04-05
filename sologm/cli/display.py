"""Display helpers for CLI output."""

import logging
from typing import TYPE_CHECKING, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.core.dice import DiceRoll
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene, SceneManager

if TYPE_CHECKING:
    from sologm.core.oracle import OracleManager

logger = logging.getLogger(__name__)


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to max_length and add ellipsis if needed.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation
    Returns:
        Truncated text with ellipsis if needed
    """
    logger.debug(f"Truncating text of length {len(text)} to max_length {max_length}")
    if max_length <= 3:
        logger.debug("Max length too small, returning ellipsis only")
        return "..."
    if len(text) <= max_length:
        logger.debug("Text already within max length, returning unchanged")
        return text
    # Ensure we keep exactly max_length characters including the ellipsis
    logger.debug(f"Truncating text to {max_length-3} chars plus ellipsis")
    return text[:max_length-3] + "..."


def display_dice_roll(console: Console, roll: DiceRoll) -> None:
    """Display a dice roll result.

    Args:
        console: Rich console instance
        roll: DiceRoll to display
    """
    logger.debug(f"Displaying dice roll: {roll.notation} (total: {roll.total})")
    logger.debug(
        f"Individual results: {roll.individual_results}, modifier: {roll.modifier}"
    )
    title = Text()
    if roll.reason:
        title.append(f"{roll.reason}: ", style="bold blue")
    title.append(roll.notation, style="bold")

    details = Text()
    if len(roll.individual_results) > 1:
        details.append("Rolls: ", style="dim")
        details.append(str(roll.individual_results), style="cyan")
        details.append("\n")

    if roll.modifier != 0:
        details.append("Modifier: ", style="dim")
        details.append(f"{roll.modifier:+d}", style="yellow")
        details.append("\n")

    details.append("Result: ", style="dim")
    details.append(str(roll.total), style="bold green")
    
    # Add timestamp if available
    if roll.created_at:
        details.append("\nTime: ", style="dim")
        details.append(roll.created_at, style="dim")

    panel = Panel(details, title=title, border_style="bright_black", expand=False)
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
    logger.debug(f"Displaying interpretation {interp.id} (selected: {selected})")
    logger.debug(
        f"Interpretation title: '{interp.title}', created: {interp.created_at}"
    )
    # Extract the numeric part of the ID (e.g., "1" from "interp-1")
    id_number = interp.id.split('-')[1]
    title_line = f"[bold]{interp.title}[/bold]"
    if selected:
        title_line += " [green](Selected)[/green]"

    panel = Panel(
        Text.from_markup(
            f"{title_line}\n{interp.description}"
        ),
        title=Text.from_markup(f"[cyan]Interpretation {interp.id} "
                               f"({id_number})[/cyan]"),
        border_style="blue",
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

    table = Table(title=f"Events in scene '{scene_title}'")
    table.add_column("Time", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Description")

    for event in events:
        table.add_row(
            event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            event.source,
            truncate_text(event.description, max_length=80),
        )

    console.print(table)


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

    table = Table(title="Games")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description")
    table.add_column("Scenes", justify="right")
    table.add_column("Current", style="yellow", justify="center")

    for game in games:
        table.add_row(
            game.id,
            game.name,
            game.description,
            str(len(game.scenes)),
            "✓" if active_game and game.id == active_game.id else "",
        )

    console.print(table)


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
    logger.debug(f"Game details: name='{game.name}', scenes={len(game.scenes)}")
    console.print("[bold]Active Game:[/]")
    console.print(f"  Name: {game.name} ({game.id})")
    console.print(f"  Description: {game.description}")
    console.print(f"  Created: {game.created_at}")
    console.print(f"  Modified: {game.modified_at}")
    console.print(f"  Scenes: {len(game.scenes)}")
    if active_scene:
        console.print(f"  Active Scene: {active_scene.title}")


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
    logger.debug(
        f"Displaying interpretation set {interp_set.id} with "
        f"{len(interp_set.interpretations)} interpretations"
    )
    logger.debug(
        f"Show context: {show_context}, "
        f"selected interpretation index: {interp_set.selected_interpretation}"
    )
    if show_context:
        console.print("\n[bold]Oracle Interpretations[/bold]")
        console.print(f"Context: {interp_set.context}")
        console.print(f"Results: {interp_set.oracle_results}\n")

    for i, interp in enumerate(interp_set.interpretations, 1):
        selected = interp_set.selected_interpretation == i - 1
        display_interpretation(console, interp, selected)

    console.print(
        f"\nInterpretation set ID: [bold]{interp_set.id}[/bold] "
        "(use this ID to select an interpretation)"
    )


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
    console.print("[bold]Active Scene:[/]")
    console.print(f"  ID: {scene.id}")
    console.print(f"  Title: {scene.title}")
    console.print(f"  Description: {scene.description}")
    console.print(f"  Status: {scene.status.value}")
    console.print(f"  Sequence: {scene.sequence}")
    console.print(f"  Created: {scene.created_at}")
    console.print(f"  Modified: {scene.modified_at}")


def display_game_status(
    console: Console,
    game: Game,
    active_scene: Optional[Scene],
    recent_events: List[Event],
    current_interpretation_reference: Optional[dict] = None,
    scene_manager: Optional[SceneManager] = None,
    oracle_manager: Optional["OracleManager"] = None,
) -> None:
    """Display comprehensive game status in a compact layout.

    Args:
        console: Rich console instance
        game: Current game
        active_scene: Active scene if any
        recent_events: Recent events (limited list)
        current_interpretation_reference: Current interpretation data if any
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
        current_interpretation_reference,
        oracle_manager,
        truncation_length
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
    game_info = (
        f"[bold]{game.name}[/bold] ({game.id})\n"
        f"[dim]{game.description}[/dim]\n"
        f"Created: {game.created_at.strftime('%Y-%m-%d')} • "
        f"Scenes: {len(game.scenes)}"
    )
    logger.debug("Game header panel created")
    return Panel(game_info, expand=True, border_style="blue")


def _create_scene_panels_grid(
    game: Game,
    active_scene: Optional[Scene],
    scene_manager: Optional[SceneManager]
) -> Table:
    """Create a grid containing current and previous scene panels."""
    logger.debug(f"Creating scene panels grid for game {game.id}")
    # Create current scene panel
    scenes_content = ""
    if active_scene:
        logger.debug(f"Including active scene {active_scene.id} in panel")
        scenes_content = (
            f"[bold]{active_scene.title}[/bold]\n"
            f"[dim]{active_scene.description}[/dim]"
        )
    else:
        logger.debug("No active scene to display")
        scenes_content = "[dim]No active scene[/dim]"

    scenes_panel = Panel(
        scenes_content,
        title="Current Scene",
        border_style="cyan"
    )

    # Create previous scene panel
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
            f"[bold]{prev_scene.title}[/bold]\n"
            f"[dim]{prev_scene.description}[/dim]"
        )
    else:
        logger.debug("No previous scene to display")
        prev_scene_content = "[dim]No previous scene[/dim]"

    prev_scene_panel = Panel(
        prev_scene_content,
        title="Previous Scene",
        border_style="blue"
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
                f"[cyan]{event.created_at.strftime('%Y-%m-%d %H:%M')}[/cyan] "
                f"[magenta]({event.source})[/magenta]\n"
                f"{truncated_description}\n\n"
            )
    else:
        logger.debug("No events to display in panel")
        events_content = "[dim]No recent events[/dim]"

    return Panel(
        events_content.rstrip(),
        title=f"Recent Events ({len(recent_events)} shown)",
        border_style="green",
    )


def _create_oracle_panel(
    game: Game,
    active_scene: Optional[Scene],
    current_interpretation_reference: Optional[dict],
    oracle_manager: Optional["OracleManager"],
    truncation_length: int
) -> Optional[Panel]:
    """Create the oracle panel if applicable."""
    logger.debug(f"Creating oracle panel for game {game.id}")

    has_open_interpretation = (
        current_interpretation_reference
        and not current_interpretation_reference.get("resolved", False)
    )

    logger.debug(f"Has open interpretation: {has_open_interpretation}")
    logger.debug(f"Has active scene: {active_scene}, "
                 f"oracle_manager: {oracle_manager}")

    if has_open_interpretation:
        logger.debug("Creating pending oracle panel")
        return _create_pending_oracle_panel(
            game,
            current_interpretation_reference,
            oracle_manager,
            truncation_length
        )
    elif active_scene and oracle_manager:
        logger.debug(f"Creating recent oracle panel for scene {active_scene.id}")
        return _create_recent_oracle_panel(
            game,
            active_scene,
            oracle_manager,
            truncation_length
        )
    logger.debug("No oracle panel needed")
    return None


def _create_pending_oracle_panel(
    game: Game,
    current_interpretation_reference: dict,
    oracle_manager: Optional["OracleManager"],
    truncation_length: int
) -> Panel:
    """Create a panel for pending oracle interpretation."""
    logger.debug(f"Creating pending oracle panel for game {game.id}")
    # Try to load the actual interpretation set for more context
    from sologm.core.oracle import OracleManager
    oracle_mgr = oracle_manager or OracleManager()
    try:
        logger.debug(
            f"Attempting to load interpretation set "
            f"{current_interpretation_reference['id']}"
        )
        interp_set = oracle_mgr.get_interpretation_set(
            game.id,
            current_interpretation_reference["scene_id"],
            current_interpretation_reference["id"]
        )
        context = interp_set.context
        logger.debug(
            f"Successfully loaded interpretation set with "
            f"{len(interp_set.interpretations)} interpretations"
        )

        # Show truncated versions of the options
        options_text = ""
        for i, interp in enumerate(interp_set.interpretations, 1):
            logger.debug(f"Adding interpretation option {i}: {interp.id}")
            truncated_title = truncate_text(interp.title, truncation_length // 2)
            options_text += f"[dim]{i}.[/dim] {truncated_title}\n"
        return Panel(
            f"[yellow]Open Oracle Interpretation:[/yellow]\n"
            f"Context: {context}\n\n"
            f"{options_text}\n"
            f"[dim]Use 'sologm oracle select' to choose an interpretation[/dim]",
            title="Pending Oracle Decision",
            border_style="yellow",
            expand=True
        )
    except Exception as e:
        logger.debug(f"Failed to load interpretation set: {e}, using fallback panel")
        # Fallback if we can't load the interpretation set
        return Panel(
            "[yellow]Open Oracle Interpretation[/yellow]\n"
            "[dim]Use 'sologm oracle status' to see details[/dim]",
            title="Pending Oracle Decision",
            border_style="yellow",
            expand=True
        )


def _create_recent_oracle_panel(
    game: Game,
    active_scene: Scene,
    oracle_manager: "OracleManager",
    truncation_length: int
) -> Optional[Panel]:
    """Create a panel showing the most recent oracle interpretation."""
    logger.debug(
        f"Creating recent oracle panel for game {game.id}, scene {active_scene.id}"
    )
    try:
        logger.debug("Attempting to get most recent interpretation")
        recent_interp = oracle_manager.get_most_recent_interpretation(
            game.id, active_scene.id
        )
        if recent_interp:
            interp_set, selected_interp = recent_interp
            logger.debug(
                f"Found recent interpretation: set {interp_set.id}, "
                f"interpretation {selected_interp.id}"
            )

            # Build the panel content with the prepared components
            return Panel(
                f"[green]Last Oracle Interpretation:[/green]\n"
                f"[bold]Oracle Results:[/bold] {interp_set.oracle_results}\n"
                f"[bold]Context:[/bold] {interp_set.context}\n"
                f"[bold]Selected:[/bold] {selected_interp.title}\n"
                f"[dim]{selected_interp.description}[/dim]",
                title="Previous Oracle Decision",
                border_style="green",
                expand=True
            )
        else:
            logger.debug("No recent interpretation found")
    except Exception as e:
        logger.debug(f"Error getting recent interpretation: {e}")
    return None
