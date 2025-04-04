"""Display helpers for CLI output."""

import logging
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.core.dice import DiceRoll
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene, SceneManager

logger = logging.getLogger(__name__)


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to max_length and add ellipsis if needed.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation
    Returns:
        Truncated text with ellipsis if needed
    """
    if max_length <= 3:
        return "..."
    if len(text) <= max_length:
        return text
    # Ensure we keep exactly max_length characters including the ellipsis
    return text[:max_length-3] + "..."


def display_dice_roll(console: Console, roll: DiceRoll) -> None:
    """Display a dice roll result.

    Args:
        console: Rich console instance
        roll: DiceRoll to display
    """
    logger.debug(f"Displaying dice roll: {roll.notation} (total: {roll.total})")
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
        console.print(f"\nNo events in scene '{scene_title}'")
        return

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
    if not games:
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
) -> None:
    """Display comprehensive game status in a compact layout.

    Args:
        console: Rich console instance
        game: Current game
        active_scene: Active scene if any
        recent_events: Recent events (limited list)
        current_interpretation: Current interpretation data if any
        scene_manager: Optional scene manager for additional context
    """
    logger.debug(
        f"Displaying game status for {game.id} with {len(recent_events)} events and "
        f"active scene: {active_scene.id if active_scene else 'None'}"
    )

    # Get console width for responsive layout
    try:
        console_width = console.width
        logger.debug(f"Console width detected: {console_width} characters")
        # Calculate appropriate truncation length based on console width
        # Since we're using a two-column layout, each column gets roughly half the width
        # Subtract some space for borders, padding, and formatting
        truncation_length = max(40, int(console_width) - 10)
    except (TypeError, ValueError):
        # Default to a reasonable truncation length if console width is not available
        logger.debug("Could not determine console width, using default value")
        truncation_length = 40
    logger.debug(
        f"Using truncation length of {truncation_length} "
        f"characters for event descriptions"
    )

    # Top bar with game info
    game_info = (
        f"[bold]{game.name}[/bold] ({game.id})\n"
        f"[dim]{game.description}[/dim]\n"
        f"Created: {game.created_at.strftime('%Y-%m-%d')} • "
        f"Scenes: {len(game.scenes)}"
    )
    console.print(Panel(game_info, expand=True, border_style="blue"))

    # Create a grid layout with two columns for scene and events
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column("Left", ratio=1)
    grid.add_column("Right", ratio=1)

    # Left column: Scene info
    scenes_content = ""
    if active_scene:
        scenes_content = (
            f"[bold]{active_scene.title}[/bold]\n"
            f"[dim]{active_scene.description}[/dim]"
        )
    else:
        scenes_content = "[dim]No active scene[/dim]"

    scenes_panel = Panel(
        scenes_content,
        title="Current Scene",
        border_style="cyan"
    )

    # Previous scene panel
    prev_scene = None
    if active_scene and scene_manager:
        prev_scene = scene_manager.get_previous_scene(game.id, active_scene)
    prev_scene_content = ""
    if prev_scene:
        prev_scene_content = (
            f"[bold]{prev_scene.title}[/bold]\n"
            f"[dim]{prev_scene.description}[/dim]"
        )
    else:
        prev_scene_content = "[dim]No previous scene[/dim]"

    prev_scene_panel = Panel(
        prev_scene_content,
        title="Previous Scene",
        border_style="blue"
    )

    # Right column: Recent Events (up to 5)
    events_content = ""
    if recent_events:
        # Calculate how many events we can reasonably show
        # Each event takes at least 3 lines (timestamp+source, description, blank)
        # For longer descriptions, estimate additional lines
        max_events_to_show = min(3, len(recent_events))  # Show at most 3 events

        events_shown = recent_events[:max_events_to_show]
        for event in events_shown:
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
        events_content = "[dim]No recent events[/dim]"

    events_panel = Panel(
        events_content.rstrip(),
        title=f"Recent Events ({len(recent_events)} shown)",
        border_style="green",
    )

    # Create a nested grid for the left column to stack the scene panels
    left_grid = Table.grid(padding=(0, 1))
    left_grid.add_column()
    left_grid.add_row(scenes_panel)
    left_grid.add_row(prev_scene_panel)

    # Add scene panels and events panel to main grid
    grid.add_row(left_grid, events_panel)
    console.print(grid)

    # If there's an open interpretation, show it in a panel below
    has_open_interpretation = (
        current_interpretation_reference
        and not current_interpretation_reference.get("resolved", False)
    )
    if has_open_interpretation:
        # Try to load the actual interpretation set for more context
        from sologm.core.oracle import OracleManager
        oracle_manager = OracleManager()
        try:
            interp_set = oracle_manager.get_interpretation_set(
                game.id,
                current_interpretation_reference["scene_id"],
                current_interpretation_reference["id"]
            )
            context = interp_set.context
        except Exception:
            # If we can't load the interpretation set, just show a generic message
            context = "Use 'sologm oracle status' to see details"

        interp_panel = Panel(
            f"[yellow]Open Oracle Interpretation:[/yellow]\n"
            f"Context: {context}\n"
            f"[dim]Use 'sologm oracle select' to choose an interpretation[/dim]",
            title="Pending Decision",
            border_style="yellow",
            expand=True
        )
        console.print(interp_panel)
