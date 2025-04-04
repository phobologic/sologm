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
