"""Event tracking commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING, Optional

import typer

# Console import removed
# display_events_table import removed
from sologm.core.event import EventManager
from sologm.utils.errors import EventError

if TYPE_CHECKING:
    from rich.console import Console

    from sologm.cli.rendering.base import Renderer


logger = logging.getLogger(__name__)
# console instance removed
event_app = typer.Typer(help="Event tracking commands")


@event_app.command("add")
def add_event(
    ctx: typer.Context,
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Description of the event (opens editor if not provided)",
    ),
    source: str = typer.Option(
        "manual",
        "--source",
        "-s",
        help=(
            "Source of the event (use 'sologm event sources' to see available options)"
        ),
    ),
) -> None:
    """Add a new event to the current scene.

    If no description is provided, opens an editor to create the event.
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        event_manager = EventManager(session=session)
        try:
            # Validate active context - no need to pass other managers
            game_id, scene_id = event_manager.validate_active_context()

            # Get the current scene, act, and game for context through manager chain
            game = event_manager.scene_manager.game_manager.get_game(game_id)
            active_act = event_manager.scene_manager.act_manager.get_active_act(game_id)
            scene = event_manager.scene_manager.get_scene(scene_id)

            # If no description is provided, open an editor
            if description is None:
                # Get recent events for context
                recent_events = event_manager.list_events(scene_id=scene_id, limit=3)
                # Import the structured editor
                from sologm.cli.utils.structured_editor import (
                    EditorConfig,
                    FieldConfig,
                    StructuredEditorConfig,
                    edit_structured_data,
                    get_event_context_header,
                )

                # Format act info for context header
                act_info = None
                if active_act:
                    act_title = (
                        active_act.title or f"Act {active_act.sequence} (Untitled)"
                    )
                    act_info = f"Act: {act_title}"

                context_info = get_event_context_header(
                    game_name=game.name,
                    scene_title=scene.title,
                    scene_description=scene.description,
                    recent_events=recent_events,
                    act_info=act_info,
                )

                # Create editor configurations
                editor_config = EditorConfig(
                    edit_message="Creating new event:",
                    success_message="Event created successfully.",
                    cancel_message="Event creation canceled.",
                    error_message="Could not open editor",
                )

                # Get available sources
                available_sources = [
                    source.name for source in event_manager.get_event_sources()
                ]

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
                            help_text="Source of the event",
                            required=False,
                            multiline=False,
                            enum_values=available_sources,
                        ),
                    ]
                )

                # Use the structured editor with initial data
                initial_data = {
                    "source": source if isinstance(source, str) else source.name
                }
                edited_data, was_modified = edit_structured_data(
                    data=initial_data,
                    console=console,
                    config=structured_config,
                    context_info=context_info,
                    editor_config=editor_config,
                    is_new=True,  # This is a new event
                )

                # If the user canceled or didn't modify anything, exit
                if not was_modified or not edited_data.get("description"):
                    return  # Just return without printing a duplicate message

                # Use the edited description and source
                description = edited_data["description"]
                if "source" in edited_data and edited_data["source"]:
                    source = edited_data["source"]

            # Add the event with the provided or edited description
            event = event_manager.add_event(
                scene_id=scene_id, description=description, source=source
            )

            logger.debug(f"Added event {event.id}")
            renderer.display_success("Event added successfully!")

            # Display the event using the renderer
            events = [event]  # Create a list with just this event
            renderer.display_events_table(events, scene)

        except EventError as e:
            renderer.display_error(f"Error: {str(e)}")
            raise typer.Exit(1) from e


@event_app.command("edit")
def edit_event(
    ctx: typer.Context,
    event_id: Optional[str] = typer.Option(
        None, "--id", help="ID of the event to edit (defaults to most recent event)"
    ),
) -> None:
    """Edit an existing event.

    If no event ID is provided, edits the most recent event in the current scene.
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        event_manager = EventManager(session=session)

        try:
            # Validate active context
            game_id, scene_id = event_manager.validate_active_context()

            # Get the game, act, and scene objects through manager chain
            game = event_manager.scene_manager.game_manager.get_game(game_id)
            active_act = event_manager.scene_manager.act_manager.get_active_act(game_id)
            scene = event_manager.scene_manager.get_scene(scene_id)

            # If no event_id provided, get the most recent event
            if event_id is None:
                # Get the most recent event (limit=1)
                recent_events = event_manager.list_events(scene_id=scene_id, limit=1)

                if not recent_events:
                    renderer.display_error(
                        "No events found in the current scene. Please provide an "
                        "event ID with --id."
                    )
                    raise typer.Exit(1)

                event = recent_events[0]
                event_id = event.id
                renderer.display_message(f"Editing most recent event (ID: {event_id})")
            else:
                # Get the specified event
                event = event_manager.get_event(event_id)
                if not event:
                    renderer.display_error(f"Event with ID '{event_id}' not found")
                    raise typer.Exit(1)

            # Check if event belongs to current scene
            if event.scene_id != scene_id:
                renderer.display_error(
                    f"Event '{event_id}' does not belong to the current scene"
                )
                raise typer.Exit(1)

            # Get recent events for context, excluding the event being edited
            # First get more events than we need, then filter
            all_recent_events = event_manager.list_events(scene_id=scene_id, limit=5)

            # Filter out the event being edited
            recent_events = [e for e in all_recent_events if e.id != event_id]

            # Limit to 3 events for display
            recent_events = recent_events[:3]

            # Import the structured editor
            from sologm.cli.utils.structured_editor import (
                EditorConfig,
                FieldConfig,
                StructuredEditorConfig,
                edit_structured_data,
                get_event_context_header,
            )

            # Format act info for context header
            act_info = None
            if active_act:
                act_title = active_act.title or f"Act {active_act.sequence} (Untitled)"
                act_info = f"Act: {act_title}"

            context_info = get_event_context_header(
                game_name=game.name,
                scene_title=scene.title,
                scene_description=scene.description,
                recent_events=recent_events,
                act_info=act_info,
            )

            # Create editor configurations
            editor_config = EditorConfig(
                edit_message=f"Editing event {event_id}:",
                success_message="Event updated successfully.",
                cancel_message="Event unchanged.",
                error_message="Could not open editor",
            )

            # Get available sources
            available_sources = [
                source.name for source in event_manager.get_event_sources()
            ]

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
                        help_text="Source of the event",
                        required=False,
                        multiline=False,
                        enum_values=available_sources,  # Pass the available sources
                    ),
                ]
            )

            # Use the structured editor with existing data
            initial_data = {
                "description": event.description,
                "source": event.source.name,
            }
            edited_data, was_modified = edit_structured_data(
                data=initial_data,
                console=console,
                config=structured_config,
                context_info=context_info,
                editor_config=editor_config,
                is_new=False,
            )

            # Update the event if it was modified
            if was_modified:
                # Check if source was changed
                source = edited_data.get("source", event.source)
                updated_event = event_manager.update_event(
                    event_id, edited_data["description"], source
                )
                renderer.display_success("Event updated successfully!")

                # Display the updated event using the renderer
                events = [updated_event]
                renderer.display_events_table(events, scene)

        except EventError as e:
            renderer.display_error(f"Error: {str(e)}")
            raise typer.Exit(1) from e


@event_app.command("sources")
def list_event_sources(ctx: typer.Context) -> None:
    """List all available event sources."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        event_manager = EventManager(session=session)

    try:
        sources = event_manager.get_event_sources()

        renderer.display_message("\nAvailable Event Sources:", style="bold")
        for source in sources:
            renderer.display_message(f"- {source.name}")

    except EventError as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@event_app.command("list")
def list_events(
    ctx: typer.Context,
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
    scene_id: Optional[str] = typer.Option(
        None,
        "--scene-id",
        "-s",
        help="ID of the scene to list events from (defaults to current scene)",
    ),
) -> None:
    """List events in the current scene or a specified scene."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        event_manager = EventManager(session=session)

    try:
        game_id, current_scene_id = event_manager.validate_active_context()

        # Use the specified scene_id if provided, otherwise use the current scene
        target_scene_id = scene_id if scene_id else current_scene_id

        # Get the scene to display its title
        scene = event_manager.scene_manager.get_scene(target_scene_id)
        if not scene:
            renderer.display_error(f"Scene with ID '{target_scene_id}' not found")
            raise typer.Exit(1)

        events = event_manager.list_events(scene_id=target_scene_id, limit=limit)

        logger.debug(f"Found {len(events)} events")
        renderer.display_events_table(events, scene)

    except EventError as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
