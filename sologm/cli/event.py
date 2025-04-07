"""Event tracking commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

from sologm.cli.utils.display import display_events_table
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)
console = Console()
event_app = typer.Typer(help="Event tracking commands")


@event_app.command("add")
def add_event(
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the event"
    ),
    source: str = typer.Option(
        "manual", "--source", "-s", help="Source of the event (manual, oracle, dice)"
    ),
) -> None:
    """Add a new event to the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )
        event = event_manager.add_event(
            game_id=game_id, scene_id=scene_id, description=description, source=source
        )
        scene = scene_manager.get_scene(game_id, scene_id)
        logger.debug(f"Added event {event.id}")
        console.print(f"\nAdded event to scene '{scene.title}':")
        console.print(f"[green]{event.description}[/]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("edit")
def edit_event(
    event_id: str = typer.Option(..., "--id", help="ID of the event to edit"),
) -> None:
    """Edit an existing event."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        # Validate active context
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )

        # Get the event
        event = event_manager.get_event(event_id)
        if not event:
            console.print(f"[red]Error:[/] Event with ID '{event_id}' not found")
            raise typer.Exit(1)

        # Check if event belongs to current scene
        if event.scene_id != scene_id:
            console.print(
                f"[red]Error:[/] Event '{event_id}' does not belong to the current scene"
            )
            raise typer.Exit(1)

        # Use the editor utility to edit the event description
        from sologm.cli.utils.editor import edit_text

        edited_text, was_modified = edit_text(
            event.description,
            console=console,
            message=f"Editing event {event_id}:",
            success_message="Event updated successfully.",
            cancel_message="Event unchanged.",
            error_message="Could not open editor",
        )

        # Update the event if it was modified
        if was_modified:
            updated_event = event_manager.update_event(event_id, edited_text)
            console.print(
                f"\nUpdated event in scene '{scene_manager.get_scene(game_id, scene_id).title}':"
            )
            console.print(f"[green]{updated_event.description}[/]")
        else:
            console.print("[yellow]No changes made to the event.[/yellow]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("list")
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
) -> None:
    """List events in the current scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )
        events = event_manager.list_events(
            game_id=game_id, scene_id=scene_id, limit=limit
        )
        scene = scene_manager.get_scene(game_id, scene_id)
        logger.debug(f"Found {len(events)} events")
        display_events_table(console, events, scene)

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
