"""Event tracking commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console
from sqlalchemy.orm import Session

from sologm.cli.display import display_events_table
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.database.session import with_db_session
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)
console = Console()
event_app = typer.Typer(help="Event tracking commands")


@event_app.command("add")
@with_db_session
def add_event(
    text: str = typer.Option(..., "--text", "-t", help="Text of the event"),
    source: str = typer.Option(
        "manual", "--source", "-s", help="Source of the event (manual, oracle, dice)"
    ),
    session: Session = None,
) -> None:
    """Add a new event to the current scene."""
    game_manager = GameManager(session=session)
    scene_manager = SceneManager(session=session)
    event_manager = EventManager(session=session)

    try:
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )
        event = event_manager.add_event(
            game_id=game_id, scene_id=scene_id, description=text, source=source
        )
        scene = scene_manager.get_scene(game_id, scene_id)
        logger.debug(f"Added event {event.id}")
        console.print(f"\nAdded event to scene '{scene.title}':")
        console.print(f"[green]{event.description}[/]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("list")
@with_db_session
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
    session: Session = None,
) -> None:
    """List events in the current scene."""
    game_manager = GameManager(session=session)
    scene_manager = SceneManager(session=session)
    event_manager = EventManager(session=session)

    try:
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )
        events = event_manager.list_events(
            game_id=game_id, scene_id=scene_id, limit=limit
        )
        scene = scene_manager.get_scene(game_id, scene_id)
        logger.debug(f"Found {len(events)} events")
        display_events_table(console, events, scene.title)

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
