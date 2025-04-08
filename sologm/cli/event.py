"""Event tracking commands for Solo RPG Helper."""

import logging
from typing import Optional, List

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
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Description of the event (opens editor if not provided)",
    ),
    source: str = typer.Option(
        "manual", "--source", "-s", help="Source of the event (manual, oracle, dice)"
    ),
) -> None:
    """Add a new event to the current scene.

    If no description is provided, opens an editor to create the event.
    """
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )

        # Get the current scene and game for context
        scene = scene_manager.get_scene(game_id, scene_id)
        game = game_manager.get_game(game_id)

        # If no description is provided, open an editor
        if description is None:
            # Get recent events for context
            recent_events = event_manager.list_events(
                game_id=game_id, scene_id=scene_id, limit=3
            )

            # Import the structured editor
            from sologm.cli.utils.structured_editor import (
                edit_structured_data,
                EditorConfig,
                FieldConfig,
                StructuredEditorConfig,
                get_event_context_header,
            )

            context_info = get_event_context_header(
                game_name=game.name,
                scene_title=scene.title,
                scene_description=scene.description,
                recent_events=recent_events,
            )

            # Create editor configurations
            editor_config = EditorConfig(
                edit_message="Creating new event:",
                success_message="Event created successfully.",
                cancel_message="Event creation canceled.",
                error_message="Could not open editor",
            )

            # Configure the structured editor fields
            structured_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="description",
                        display_name="Event Description",
                        help_text="The detailed description of the event",
                        required=True,
                        multiline=True,
                    ),
                    FieldConfig(
                        name="source",
                        display_name="Source",
                        help_text="Source of the event (manual, oracle, dice)",
                        required=False,
                        multiline=False,
                    ),
                ]
            )

            # Use the structured editor with initial data
            initial_data = {"source": source}
            edited_data, was_modified = edit_structured_data(
                data=initial_data,
                console=console,
                config=structured_config,
                context_info=context_info,
                editor_config=editor_config,
            )

            # If the user canceled or didn't modify anything, exit
            if not was_modified or not edited_data.get("description"):
                console.print("[yellow]Event creation canceled.[/yellow]")
                return

            # Use the edited description and source
            description = edited_data["description"]
            if "source" in edited_data and edited_data["source"]:
                source = edited_data["source"]

        # Add the event with the provided or edited description
        event = event_manager.add_event(
            game_id=game_id, scene_id=scene_id, description=description, source=source
        )

        logger.debug(f"Added event {event.id}")
        console.print(f"\nAdded event to scene '{scene.title}':")
        console.print(f"[green]{event.description}[/]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("edit")
def edit_event(
    event_id: Optional[str] = typer.Option(
        None, "--id", help="ID of the event to edit (defaults to most recent event)"
    ),
) -> None:
    """Edit an existing event.

    If no event ID is provided, edits the most recent event in the current scene.
    """
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        # Validate active context
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )

        # Get the game and scene objects
        game = game_manager.get_game(game_id)
        scene = scene_manager.get_scene(game_id, scene_id)

        # If no event_id provided, get the most recent event
        if event_id is None:
            # Get the most recent event (limit=1)
            recent_events = event_manager.list_events(
                game_id=game_id, scene_id=scene_id, limit=1
            )

            if not recent_events:
                console.print(
                    "[red]Error:[/] No events found in the current scene. "
                    "Please provide an event ID with --id."
                )
                raise typer.Exit(1)

            event = recent_events[0]
            event_id = event.id
            console.print(f"Editing most recent event (ID: {event_id})")
        else:
            # Get the specified event
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

        # Get recent events for context, excluding the event being edited
        # First get more events than we need, then filter
        all_recent_events = event_manager.list_events(
            game_id=game_id, scene_id=scene_id, limit=5
        )

        # Filter out the event being edited
        recent_events = [e for e in all_recent_events if e.id != event_id]

        # Limit to 3 events for display
        recent_events = recent_events[:3]

        # Import the structured editor
        from sologm.cli.utils.structured_editor import (
            edit_structured_data,
            EditorConfig,
            FieldConfig,
            StructuredEditorConfig,
            get_event_context_header,
        )

        context_info = get_event_context_header(
            game_name=game.name,
            scene_title=scene.title,
            scene_description=scene.description,
            recent_events=recent_events,
        )

        # Create editor configurations
        editor_config = EditorConfig(
            edit_message=f"Editing event {event_id}:",
            success_message="Event updated successfully.",
            cancel_message="Event unchanged.",
            error_message="Could not open editor",
        )

        # Configure the structured editor fields
        structured_config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="description",
                    display_name="Event Description",
                    help_text="The detailed description of the event",
                    required=True,
                    multiline=True,
                ),
                FieldConfig(
                    name="source",
                    display_name="Source",
                    help_text="Source of the event (manual, oracle, dice)",
                    required=False,
                    multiline=False,
                ),
            ]
        )

        # Use the structured editor with existing data
        initial_data = {
            "description": event.description,
            "source": event.source
        }
        edited_data, was_modified = edit_structured_data(
            data=initial_data,
            console=console,
            config=structured_config,
            context_info=context_info,
            editor_config=editor_config,
        )

        # Update the event if it was modified
        if was_modified:
            # Check if source was changed
            source = edited_data.get("source", event.source)
            updated_event = event_manager.update_event(
                event_id, edited_data["description"], source
            )
            console.print(f"\nUpdated event in scene '{scene.title}':")
            console.print(f"[green]{updated_event.description}[/]")
        else:
            console.print("[yellow]No changes made to the event.[/yellow]")

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("list")
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
    scene_id: Optional[str] = typer.Option(
        None,
        "--scene-id",
        "-s",
        help="ID of the scene to list events from (defaults to current scene)",
    ),
) -> None:
    """List events in the current scene or a specified scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()
    event_manager = EventManager()

    try:
        game_id, current_scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )

        # Use the specified scene_id if provided, otherwise use the current scene
        target_scene_id = scene_id if scene_id else current_scene_id

        # Get the scene to display its title
        scene = scene_manager.get_scene(game_id, target_scene_id)
        if not scene:
            console.print(f"[red]Error:[/] Scene with ID '{target_scene_id}' not found")
            raise typer.Exit(1)

        events = event_manager.list_events(
            game_id=game_id, scene_id=target_scene_id, limit=limit
        )

        logger.debug(f"Found {len(events)} events")
        display_events_table(console, events, scene)

    except EventError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
