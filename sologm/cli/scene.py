"""Scene management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer
# Console import removed
# display_scene_info import removed
from sologm.core.scene import SceneManager
from sologm.database.session import get_db_context
from sologm.utils.errors import ActError, GameError, SceneError

if TYPE_CHECKING:
    from typer import Typer
    from rich.console import Console
    from sologm.cli.rendering.base import Renderer

    app: Typer


# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")

# console instance removed
logger = logging.getLogger(__name__)


@scene_app.command("add")
def add_scene(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="Title of the scene"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the scene"
    ),
) -> None:
    """Add a new scene to the active act."""
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            # Initialize scene_manager with the session
            scene_manager = SceneManager(session=session)

            # Get active game and act context through scene_manager
            try:
                act_id, _ = scene_manager.validate_active_context()
            except SceneError:
                # If there's no active scene, we still need the active act
                active_game = scene_manager.game_manager.get_active_game()
                if not active_game:
                    raise GameError(
                        "No active game. Use 'sologm game activate' to set one."
                    )

                active_act = scene_manager.act_manager.get_active_act(active_game.id)
                if not active_act:
                    raise ActError(
                        "No active act. Create one with 'sologm act create'."
                    )

                act_id = active_act.id

            # Create the scene
            scene = scene_manager.create_scene(
                act_id=act_id,
                title=title,
                description=description,
            )

            renderer.display_success("Scene added successfully!")
            renderer.display_scene_info(scene)
    except (GameError, SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("list")
def list_scenes(ctx: typer.Context) -> None:
    """List all scenes in the active act."""
    # display_scenes_table import removed
    renderer: "Renderer" = ctx.obj["renderer"]
    with get_db_context() as session:
        scene_manager = SceneManager(session=session)

        try:
            # Get active game and act context through scene_manager
            act_id, active_scene = scene_manager.validate_active_context()
            active_scene_id = active_scene.id if active_scene else None
        except SceneError:
            # If there's no active scene, we still need the active act
            active_game = scene_manager.game_manager.get_active_game()
            if not active_game:
                raise GameError(
                    "No active game. Use 'sologm game activate' to set one."
                )

            active_act = scene_manager.act_manager.get_active_act(active_game.id)
            if not active_act:
                raise ActError("No active act. Create one with 'sologm act create'.")

            act_id = active_act.id
            active_scene_id = None

        # Get scenes
        scenes = scene_manager.list_scenes(act_id)

        # Use the renderer - session still open for lazy loading
        renderer.display_scenes_table(scenes, active_scene_id)


@scene_app.command("info")
def scene_info(
    ctx: typer.Context,
    show_events: bool = typer.Option(
        True, "--events/--no-events", help="Show events associated with this scene"
    ),
) -> None:
    """Show information about the active scene and its events."""
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            _, active_scene = scene_manager.validate_active_context()

            # Display scene information using renderer
            renderer.display_scene_info(active_scene)

            # If show_events is True, fetch and display events
            if show_events:
                # display_events_table import removed

                # Access event_manager through scene_manager instead of creating a new instance
                event_manager = scene_manager.event_manager
                events = event_manager.list_events(scene_id=active_scene.id)

                # Display events table using renderer
                truncate_descriptions = (
                    len(events) > 3
                )  # Truncate if more than 3 events
                renderer.display_message("") # Add a blank line for separation
                renderer.display_events_table(
                    events,
                    active_scene,
                    truncate_descriptions=truncate_descriptions,
                )

    except (SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")


@scene_app.command("complete")
def complete_scene(ctx: typer.Context) -> None:
    """Complete the active scene."""
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            _, active_scene = scene_manager.validate_active_context()
            completed_scene = scene_manager.complete_scene(active_scene.id)
            renderer.display_success("Scene completed successfully!")
            renderer.display_scene_info(completed_scene)
    except (SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("edit")
def edit_scene(
    ctx: typer.Context,
    scene_id: str = typer.Option(
        None, "--id", help="ID of the scene to edit (defaults to active scene)"
    ),
) -> None:
    """Edit the title and description of a scene."""
    from sologm.cli.utils.structured_editor import (
        EditorConfig,
        FieldConfig,
        StructuredEditorConfig,
        edit_structured_data,
    )
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"] # Needed for editor
    try:
        with get_db_context() as session:
            # Initialize the scene_manager with the session
            scene_manager = SceneManager(session=session)

            # Get active game and act context through scene_manager
            act_id, active_scene = scene_manager.validate_active_context()

            # If no scene_id provided, use the active scene
            if not scene_id:
                scene_id = active_scene.id

            # Get the scene to edit
            scene = scene_manager.get_scene(scene_id)
            if not scene:
                renderer.display_error(f"Scene '{scene_id}' not found.")
                raise typer.Exit(1)

            # Prepare the data for editing
            scene_data = {"title": scene.title, "description": scene.description}

            # Create editor configurations
            editor_config = EditorConfig(
                edit_message=f"Editing scene {scene_id}:",
                success_message="Scene updated successfully.",
                cancel_message="Scene unchanged.",
                error_message="Could not open editor",
            )

            # Configure the structured editor fields
            structured_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="title",
                        display_name="Scene Title",
                        help_text="The title of the scene",
                        required=True,
                        multiline=False,
                    ),
                    FieldConfig(
                        name="description",
                        display_name="Scene Description",
                        help_text="The detailed description of the scene",
                        required=False,
                        multiline=True,
                    ),
                ]
            )

            # Use the structured editor
            edited_data, was_modified = edit_structured_data(
                data=scene_data,
                console=console,
                config=structured_config,
                context_info=f"Editing scene: {scene.title} ({scene.id})\n",
                editor_config=editor_config,
                is_new=False,  # This is an existing scene
            )

            if was_modified:
                # Update the scene
                updated_scene = scene_manager.update_scene(
                    scene_id=scene_id,
                    title=edited_data["title"],
                    description=edited_data["description"],
                )

                renderer.display_success("Scene updated successfully!")
                renderer.display_scene_info(updated_scene)
            else:
                # User cancelled the editor
                renderer.display_warning("Scene edit cancelled.")


    except (SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("set-current")
def set_current_scene(
    ctx: typer.Context,
    scene_id: str = typer.Option(..., "--id", help="ID of the scene to make current"),
) -> None:
    """Set which scene is currently being played."""
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            try:
                act_id, _ = scene_manager.validate_active_context()
            except SceneError:
                # If there's no active scene, we still need the active act
                active_game = scene_manager.game_manager.get_active_game()
                if not active_game:
                    raise GameError(
                        "No active game. Use 'sologm game activate' to set one."
                    )

                active_act = scene_manager.act_manager.get_active_act(active_game.id)
                if not active_act:
                    raise ActError(
                        "No active act. Create one with 'sologm act create'."
                    )

                act_id = active_act.id

            # Get list of valid scenes first
            scenes = scene_manager.list_scenes(act_id)
            scene_ids = [s.id for s in scenes]

            # Check if scene_id exists before trying to set it
            if scene_id not in scene_ids:
                renderer.display_error(f"Scene '{scene_id}' not found.")
                renderer.display_message("\nValid scene IDs:")
                for sid in scene_ids:
                    renderer.display_message(f"  {sid}")
                raise typer.Exit(1) # Exit after showing valid IDs

            # Set the current scene
            new_current = scene_manager.set_current_scene(scene_id)
            renderer.display_success("Current scene updated successfully!")
            renderer.display_scene_info(new_current)
    except (GameError, SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
