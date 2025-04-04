"""Display helpers for CLI output."""

from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.core.dice import DiceRoll
from sologm.core.event import Event
from sologm.core.game import Game
from sologm.core.oracle import Interpretation, InterpretationSet
from sologm.core.scene import Scene


def display_dice_roll(console: Console, roll: DiceRoll) -> None:
    """Display a dice roll result.

    Args:
        console: Rich console instance
        roll: DiceRoll to display
    """
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
            event.description,
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
    current_interpretation: Optional[dict] = None,
) -> None:
    """Display comprehensive game status in a compact layout.

    Args:
        console: Rich console instance
        game: Current game
        active_scene: Active scene if any
        recent_events: Recent events (limited list)
        current_interpretation: Current interpretation data if any
    """
    # Create a grid layout with two columns
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column("Left", ratio=1)
    grid.add_column("Right", ratio=1)

    # Left column: Game & Scene info
    game_panel = Panel(
        f"[bold]{game.name}[/bold]\n[dim]{game.description}[/dim]",
        title="Game",
        border_style="blue",
    )

    scene_content = (
        f"[bold]{active_scene.title}[/bold]\n"
        f"[dim]{active_scene.description}[/dim]\n\n"
        f"Status: [italic]{active_scene.status.value}[/italic]"
        if active_scene
        else "[dim]No active scene[/dim]"
    )
    scene_panel = Panel(scene_content, title="Current Scene", border_style="cyan")

    # Right column: Recent Events
    events_content = ""
    if recent_events:
        for event in recent_events:
            events_content += (
                f"[cyan]{event.created_at.strftime('%H:%M')}[/cyan] "
                f"({event.source})\n{event.description}\n\n"
            )
    else:
        events_content = "[dim]No recent events[/dim]"

    events_panel = Panel(
        events_content.rstrip(),
        title="Recent Events",
        border_style="green"
    )

    # Add game and scene info to left column, events to right
    grid.add_row(game_panel, events_panel)
    grid.add_row(scene_panel)

    # If there's an open interpretation, show it in a panel below
    if current_interpretation and current_interpretation.get("selected_interpretation") is None:
        interp_panel = Panel(
            f"[yellow]Open Oracle Interpretation:[/yellow]\n"
            f"Context: {current_interpretation['context']}\n"
            f"[dim]Use 'sologm oracle select' to choose an interpretation[/dim]",
            title="Pending Decision",
            border_style="yellow"
        )
        grid.add_row(Panel(interp_panel, expand=True))

    console.print(grid)
