"""Scene management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING, Optional

import typer

# Import structured editor components globally
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    EditorStatus,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)

# Console import removed
# display_scene_info import removed
from sologm.core.scene import SceneManager
from sologm.database.session import get_db_context
from sologm.utils.errors import ActError, GameError, SceneError

if TYPE_CHECKING:
    from rich.console import Console
    from typer import Typer

    from sologm.cli.rendering.base import Renderer
    from sologm.models.act import Act
    from sologm.models.scene import Scene

    app: Typer


# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")

# console instance removed
logger = logging.getLogger(__name__)


def _get_scene_editor_config() -> StructuredEditorConfig:
    """Returns the standard StructuredEditorConfig for scene editing."""
    return StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="title",
                display_name="Title",
                help_text="Title of the scene (required)",
                required=True,
                multiline=False,
            ),
            FieldConfig(
                name="description",
                display_name="Description",
                help_text="Description of the scene (optional)",
                multiline=True,
                required=False,
            ),
        ],
        wrap_width=70,
    )


def _build_scene_editor_context(
    verb: str,  # e.g., "Adding", "Editing"
    game_name: str,
    act_title: str,
    scene_title: Optional[str] = None,
    scene_id: Optional[str] = None,
) -> str:
    """Builds the context info string for the scene editor."""
    scene_display = f": {scene_title} ({scene_id})" if scene_title and scene_id else ""
    context_info = f"{verb} Scene{scene_display}\n"
    context_info += f"Act: {act_title}\n"
    context_info += f"Game: {game_name}\n\n"
    if verb == "Adding":
        context_info += (
            "Scenes represent specific locations, encounters, or challenges.\n"
            "Provide a concise title and an optional description."
        )
    else:  # Editing
        context_info += "Modify the title or description below."
    return context_info


@scene_app.command("add")
def add_scene(
    ctx: typer.Context,
    # Make title and description optional
    title: Optional[str] = typer.Option(
        None,  # Changed from ...
        "--title",
        "-t",
        help="Title of the scene (opens editor if not provided)",
    ),
    description: Optional[str] = typer.Option(
        None,  # Changed from ...
        "--description",
        "-d",
        help="Description of the scene (opens editor if not provided)",
    ),
) -> None:
    """[bold]Add a new scene to the active act.[/bold]

    If title and description are not provided via options, this command
    opens a structured editor for you to enter them.

    Scenes represent specific locations, encounters, or challenges within an Act.
    A title is required, but the description can be left empty.

    [yellow]Examples:[/yellow]
        [green]Add a scene providing title and description directly:[/green]
        $ sologm scene add -t "The Old Mill" -d "A dilapidated mill by the river."

        [green]Add a scene using the interactive editor:[/green]
        $ sologm scene add

        [green]Add a scene with only a title using the editor:[/green]
        $ sologm scene add -t "Market Square"
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    logger.debug("Attempting to add a new scene.")
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            # Initialize scene_manager with the session
            scene_manager = SceneManager(session=session)
            active_act: Optional["Act"] = (
                None  # Use forward reference if Act not imported
            )
            act_id: Optional[str] = None
            game_name: str = "Unknown Game"  # Default

            # Get active game and act context *before* potentially opening editor
            try:
                # Try getting the full context first (requires active scene)
                context = scene_manager.get_active_context()
                active_act = context["act"]
                act_id = active_act.id
                game_name = context["game"].name
                logger.debug(
                    f"Found active context: Game='{game_name}', "
                    f"Act='{active_act.title}' ({act_id})"
                )
            except SceneError as e:
                # If there's no active scene, we still need the active act
                logger.debug("No active scene found, attempting to find active act.")
                active_game = scene_manager.game_manager.get_active_game()
                if not active_game:
                    raise GameError(
                        "No active game. Use 'sologm game activate' to set one."
                    ) from e

                active_act = scene_manager.act_manager.get_active_act(active_game.id)
                if not active_act:
                    raise ActError(
                        "No active act. Create one with 'sologm act create'."
                    ) from e

                act_id = active_act.id
                game_name = active_game.name
                logger.debug(
                    f"Found active game='{game_name}' and "
                    f"act='{active_act.title}' ({act_id}), but no active scene."
                )

            # --- Editor Logic ---
            if title is None or description is None:
                logger.info("Title or description not provided, opening editor.")

                # Use helper functions to get config and context
                editor_config = _get_scene_editor_config()
                act_title_display = f"Act {active_act.sequence}"
                if active_act and active_act.title:
                    act_title_display = active_act.title
                context_info = _build_scene_editor_context(
                    verb="Adding",
                    game_name=game_name,
                    act_title=act_title_display,
                )

                # Create initial data (use provided values if any)
                initial_data = {
                    "title": title or "",
                    "description": description or "",
                }

                # Open editor
                result_data, status = edit_structured_data(
                    initial_data,
                    console,
                    editor_config,  # Use shared config
                    context_info=context_info,  # Use built context
                    is_new=True,  # Indicate this is for a new item
                    # No original_data_for_comments needed for add
                )

                # Check status: Proceed only if saved (modified or unchanged)
                if status not in (
                    EditorStatus.SAVED_MODIFIED,
                    EditorStatus.SAVED_UNCHANGED,
                ):
                    logger.info(
                        f"Scene creation cancelled via editor (status: {status.name})."
                    )
                    # Message already printed by edit_structured_data
                    raise typer.Exit(0)  # Exit gracefully

                # If saved, update title and description from editor results
                title = result_data.get(
                    "title"
                )  # Already validated as required by editor
                description = (
                    result_data.get("description") or None
                )  # Use None if empty
                logger.debug("Scene data collected from editor.")

            # --- End Editor Logic ---

            # Ensure we have an act_id (should be set from context fetching above)
            if not act_id:
                # This case should ideally not be reached if context fetching is correct
                logger.error("Failed to determine target Act ID for scene creation.")
                raise ActError(
                    "Could not determine the active act to add the scene to."
                )

            # Validate title is not empty after potentially using editor
            if not title or not title.strip():
                renderer.display_error("Scene title cannot be empty.")
                raise typer.Exit(1)

            # Create the scene using the (potentially editor-provided) title/description
            logger.debug(
                f"Calling scene_manager.create_scene for act {act_id} with "
                f"title='{title}'"
            )
            scene = scene_manager.create_scene(
                act_id=act_id,
                title=title.strip(),  # Ensure title is stripped
                description=description.strip()
                if description
                else None,  # Strip or use None
                make_active=True,  # Default behavior: new scene becomes active
            )

            renderer.display_success("Scene added successfully!")
            # Use the renderer's display_scene_info method
            renderer.display_scene_info(scene)  # Pass the created scene object
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
        except SceneError as e:
            # If there's no active scene, we still need the active act
            active_game = scene_manager.game_manager.get_active_game()
            if not active_game:
                raise GameError(
                    "No active game. Use 'sologm game activate' to set one."
                ) from e

            active_act = scene_manager.act_manager.get_active_act(active_game.id)
            if not active_act:
                raise ActError(
                    "No active act. Create one with 'sologm act create'."
                ) from e

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

                # Access event_manager through scene_manager instead of
                # creating a new instance
                event_manager = scene_manager.event_manager
                events = event_manager.list_events(scene_id=active_scene.id)

                # Display events table using renderer
                truncate_descriptions = (
                    len(events) > 3
                )  # Truncate if more than 3 events
                renderer.display_message("")  # Add a blank line for separation
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
    scene_id: Optional[str] = typer.Option(  # Make scene_id optional
        None,
        "--id",
        help="ID of the scene to edit (defaults to active scene)",
    ),
) -> None:
    """[bold]Edit the title and description of a scene.[/bold]

    Opens a structured editor to modify the title and description of a scene.
    If no [cyan]--id[/cyan] is provided, it edits the currently active scene.

    [yellow]Examples:[/yellow]
        [green]Edit the active scene:[/green]
        $ sologm scene edit

        [green]Edit a specific scene by ID:[/green]
        $ sologm scene edit --id <scene_id>
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    try:
        with get_db_context() as session:
            # Initialize the scene_manager with the session
            scene_manager = SceneManager(session=session)
            scene_to_edit: Optional["Scene"] = None  # Use forward reference

            # Determine which scene to edit
            if scene_id:
                logger.debug(f"Attempting to fetch specific scene with ID: {scene_id}")
                scene_to_edit = scene_manager.get_scene(scene_id)
                if not scene_to_edit:
                    renderer.display_error(f"Scene with ID '{scene_id}' not found.")
                    raise typer.Exit(1)
                # Optional: Verify scene_to_edit.act.game_id matches active game
                logger.debug(
                    f"Found specific scene: {scene_to_edit.id} "
                    f"('{scene_to_edit.title}')"
                )
            else:
                logger.debug("No scene ID provided, fetching active scene.")
                # Get active context (ensures active game/act/scene exist)
                context = scene_manager.get_active_context()
                scene_to_edit = context["scene"]
                scene_id = scene_to_edit.id  # Set scene_id for logging/messages
                logger.debug(
                    f"Found active scene: {scene_to_edit.id} ('{scene_to_edit.title}')"
                )

            # Prepare the data for editing
            scene_data = {
                "title": scene_to_edit.title
                or "",  # Use empty string if None initially
                "description": scene_to_edit.description or "",
            }

            # Use helper functions for config and context
            structured_config = _get_scene_editor_config()
            # Ensure act and game are loaded for context building
            try:
                game_name = scene_to_edit.act.game.name
                act_title = (
                    scene_to_edit.act.title or f"Act {scene_to_edit.act.sequence}"
                )
            except Exception as e:
                logger.warning(
                    f"Could not fully load context for editor: {e}", exc_info=True
                )
                # Provide defaults if loading fails
                game_name = "Unknown Game"
                act_title = "Unknown Act"

            context_info = _build_scene_editor_context(
                verb="Editing",
                game_name=game_name,
                act_title=act_title,
                scene_title=scene_to_edit.title,
                scene_id=scene_to_edit.id,
            )

            # Define specific editor messages for editing
            editor_config_obj = EditorConfig(
                edit_message=f"Editing Scene: {scene_to_edit.title} ({scene_id})",
                success_message="Scene updated successfully.",
                cancel_message="Edit cancelled. Scene unchanged.",
                error_message="Could not open editor.",
            )

            # Use the structured editor
            edited_data, status = edit_structured_data(
                data=scene_data,
                console=console,
                config=structured_config,
                context_info=context_info,
                editor_config=editor_config_obj,
                is_new=False,
                original_data_for_comments=scene_data,
            )

            # Process editor result based on status
            if status == EditorStatus.SAVED_MODIFIED:
                logger.info(f"Editor returned SAVED_MODIFIED for scene {scene_id}.")
                # Update the scene
                updated_scene = scene_manager.update_scene(
                    scene_id=scene_id,  # Use the determined scene_id
                    title=edited_data["title"],  # Already validated by editor
                    description=edited_data["description"] or None,  # Use None if empty
                )
                logger.info(f"Scene {scene_id} updated successfully.")
                # Success message printed by editor function now
                # renderer.display_success("Scene updated successfully!")
                renderer.display_scene_info(updated_scene)  # Display updated info

            elif status == EditorStatus.SAVED_UNCHANGED:
                logger.info(f"Editor returned SAVED_UNCHANGED for scene {scene_id}.")
                raise typer.Exit(0)  # Exit gracefully

            else:  # ABORTED, VALIDATION_ERROR, EDITOR_ERROR
                logger.info(f"Scene edit cancelled or failed (status: {status.name}).")
                # Message already printed by editor
                raise typer.Exit(0)  # Exit gracefully

    except (SceneError, ActError, GameError) as e:  # Added GameError
        logger.error(f"Error editing scene: {e}", exc_info=True)
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("set-current")
def set_current_scene(
    ctx: typer.Context,
    scene_id: str = typer.Argument(
        ..., help="ID of the scene to make current"
    ),  # Changed to Argument
) -> None:
    """[bold]Set which scene is currently being played.[/bold]

    Makes the specified scene the 'active' scene within its act. Any subsequent
    commands that operate on the 'active scene' (like adding events) will target
    this scene.

    You must provide the ID of the scene you want to activate.

    [yellow]Example:[/yellow]
        $ sologm scene set-current <scene_id>
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    logger.debug(f"Attempting to set scene '{scene_id}' as current.")
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            try:
                act_id, _ = scene_manager.validate_active_context()
            except SceneError as e:
                # If there's no active scene, we still need the active act
                active_game = scene_manager.game_manager.get_active_game()
                if not active_game:
                    raise GameError(
                        "No active game. Use 'sologm game activate' to set one."
                    ) from e

                active_act = scene_manager.act_manager.get_active_act(active_game.id)
                if not active_act:
                    raise ActError(
                        "No active act. Create one with 'sologm act create'."
                    ) from e

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
                raise typer.Exit(1)  # Exit after showing valid IDs

            # We need the context of the *act* the target scene belongs to.
            # First, try to get the scene directly.
            target_scene = scene_manager.get_scene(scene_id)

            if not target_scene:
                renderer.display_error(f"Scene with ID '{scene_id}' not found.")
                # Optionally, list available scenes in the *current* act if possible
                try:
                    # Try to get current context to list scenes from the same act
                    current_act_id = None
                    try:
                        current_context = scene_manager.get_active_context()
                        current_act_id = current_context["act"].id
                    except SceneError:  # If no active scene, try getting active act
                        active_game = scene_manager.game_manager.get_active_game()
                        if active_game:
                            active_act = scene_manager.act_manager.get_active_act(
                                active_game.id
                            )
                            if active_act:
                                current_act_id = active_act.id

                    if current_act_id:
                        scenes_in_current_act = scene_manager.list_scenes(
                            current_act_id
                        )
                        if scenes_in_current_act:
                            renderer.display_message(
                                "\nScenes in the current active act:"
                            )
                            for s in scenes_in_current_act:
                                renderer.display_message(f"  {s.id} ('{s.title}')")
                except (ActError, GameError):
                    pass  # Ignore errors trying to list scenes if context is bad
                raise typer.Exit(1)

            # We found the target scene, now use its act_id
            act_id = target_scene.act_id
            logger.debug(f"Found target scene {scene_id} belonging to act {act_id}.")

            # Set the current scene using the manager
            new_current = scene_manager.set_current_scene(scene_id)
            logger.info(
                f"Successfully set scene {new_current.id} "
                f"('{new_current.title}') as current for act {act_id}."
            )

            renderer.display_success("Current scene updated successfully!")
            # Pass context if needed by renderer
            renderer.display_scene_info(
                new_current
            )  # Display info of the newly set scene
    except (GameError, SceneError, ActError) as e:
        logger.error(f"Error setting current scene: {e}", exc_info=True)
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:  # Catch unexpected errors
        logger.exception(f"An unexpected error occurred during scene set-current: {e}")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e
