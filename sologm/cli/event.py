"""Event tracking commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console
from rich.table import Table

from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)
console = Console()
event_app = typer.Typer(help="Event tracking commands")


@event_app.command("add")
def add_event(
    text: str = typer.Option(..., "--text", "-t", help="Text of the event"),
    source: str = typer.Option("manual", "--source", "-s",
                               help="Source of the event (manual, oracle, "
                                    "dice)")
) -> None:
    """Add a new event to the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    # Get active game
    game = game_manager.get_active_game()
    if not game:
        console.print("[red]Error:[/] No active game. Use 'sologm game "
                      "activate' to set one.")
        raise typer.Exit(1)

    # Get current scene
    scene = scene_manager.get_active_scene(game.id)
    if not scene:
        console.print("[red]Error:[/] No current scene. Create one with "
                      "'sologm scene create'.")
        raise typer.Exit(1)

    logger.debug(f"Adding event to game {game.id}, scene {scene.id}")
    try:
        event = event_manager.add_event(
            game_id=game.id,
            scene_id=scene.id,
            description=text,
            source=source
        )
        logger.debug(f"Added event {event.id}")
        console.print(f"\nAdded event to scene '{scene.title}':")
        console.print(f"[green]{event.description}[/]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)


@event_app.command("list")
def list_events(
    limit: int = typer.Option(5, "--limit", "-l",
                              help="Number of events to show"),
) -> None:
    """List events in the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    # Get active game
    game = game_manager.get_active_game()
    if not game:
        console.print("[red]Error:[/] No active game. Use 'sologm game "
                      "activate' to set one.")
        raise typer.Exit(1)

    # Get current scene
    scene = scene_manager.get_active_scene(game.id)
    if not scene:
        console.print("[red]Error:[/] No current scene. Create one with "
                      "'sologm scene create'.")
        raise typer.Exit(1)

    logger.debug(f"Listing events for game {game.id}, scene {scene.id} with limit {limit}")
    try:
        events = event_manager.list_events(
            game_id=game.id,
            scene_id=scene.id,
            limit=limit
        )
        logger.debug(f"Found {len(events)} events")

        if not events:
            console.print(f"\nNo events in scene '{scene.title}'")
            return

        # Create table
        table = Table(title=f"Events in scene '{scene.title}'")
        table.add_column("Time", style="cyan")
        table.add_column("Source", style="magenta")
        table.add_column("Description")

        for event in events:
            table.add_row(
                event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                event.source,
                event.description
            )

        console.print(table)

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)
