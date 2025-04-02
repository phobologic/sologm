"""Event tracking commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app

# Create event subcommand
event_app = typer.Typer(help="Event tracking commands")
app.add_typer(event_app, name="event")

# Create console for rich output
console = Console()


@event_app.command("add")
def add_event(
    text: str = typer.Option(..., "--text", "-t", help="Text of the event"),
) -> None:
    """Add an event to the active scene."""
    console.print("[bold green]Event added successfully![/]")
    console.print(f"Event: {text}")


@event_app.command("list")
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
) -> None:
    """List events in the active scene."""
    console.print("[bold]Events:[/]")
    console.print(f"Showing last {limit} events:")
    console.print("No events found. Add one with 'sologm event add'.")
"""Event CLI commands."""

import logging
from typing import Optional

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
    source: str = typer.Option("manual", "--source", "-s", help="Source of the event (manual, oracle, dice)")
) -> None:
    """Add a new event to the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()
    
    # Get active game
    game = game_manager.get_active_game()
    if not game:
        console.print("[red]Error:[/] No active game. Use 'sologm game activate' to set one.")
        raise typer.Exit(1)
        
    # Get current scene
    scene = scene_manager.get_active_scene(game.id)
    if not scene:
        console.print("[red]Error:[/] No current scene. Create one with 'sologm scene create'.")
        raise typer.Exit(1)
        
    try:
        event = event_manager.add_event(
            game_id=game.id,
            scene_id=scene.id,
            description=text,
            source=source
        )
        console.print(f"\nAdded event to scene '{scene.title}':")
        console.print(f"[green]{event.description}[/]")
        
    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)

@event_app.command("list")
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
) -> None:
    """List events in the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()
    
    # Get active game
    game = game_manager.get_active_game()
    if not game:
        console.print("[red]Error:[/] No active game. Use 'sologm game activate' to set one.")
        raise typer.Exit(1)
        
    # Get current scene
    scene = scene_manager.get_active_scene(game.id)
    if not scene:
        console.print("[red]Error:[/] No current scene. Create one with 'sologm scene create'.")
        raise typer.Exit(1)
        
    try:
        events = event_manager.list_events(
            game_id=game.id,
            scene_id=scene.id,
            limit=limit
        )
        
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
