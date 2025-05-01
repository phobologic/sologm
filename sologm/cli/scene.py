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

logger = logging.getLogger(__name__)


# --- Helper Functions ---


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
        wrap_width=70,  # Keep wrap width for editor text formatting
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


# --- Commands ---


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

    If title and description are not provided via options, this command opens a
    structured editor for you to enter them.

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
    console: "Console" = ctx.obj["console"]
    logger.debug("Attempting to add a new scene.")
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)
            active_act: Optional["Act"] = None
            act_id: Optional[str] = None
            game_name: str = "Unknown Game"

            # Get active game and act context *before* potentially opening editor
            try:
                context = scene_manager.get_active_context()
                active_act = context["act"]
                act_id = active_act.id
                game_name = context["game"].name
                logger.debug(
                    "Found active context: Game='%s', Act='%s' (%s)",
                    game_name,
                    active_act.title,
                    act_id,
                )
            except SceneError as e:
                logger.debug(
                    "No active scene found, attempting to find active act.",
                    exc_info=True,
                )
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
                    "Found active game='%s' and act='%s' (%s), but no active scene.",
                    game_name,
                    active_act.title,
                    act_id,
                )

            # --- Editor Logic ---
            if title is None or description is None:
                logger.info("Title or description not provided, opening editor.")
                editor_config = _get_scene_editor_config()
                act_title_display = (
                    active_act.title
                    if active_act and active_act.title
                    else f"Act {active_act.sequence}"
                )
                context_info = _build_scene_editor_context(
                    verb="Adding",
                    game_name=game_name,
                    act_title=act_title_display,
                )
                initial_data = {
                    "title": title or "",
                    "description": description or "",
                }

                result_data, status = edit_structured_data(
                    data=initial_data,
                    console=console,
                    config=editor_config,
                    context_info=context_info,
                    is_new=True,
                )

                if status not in (
                    EditorStatus.SAVED_MODIFIED,
                    EditorStatus.SAVED_UNCHANGED,
                ):
                    logger.info(
                        "Scene creation cancelled via editor (status: %s).",
                        status.name,
                    )
                    raise typer.Exit(0)

                title = result_data.get("title")
                description = result_data.get("description") or None
                logger.debug("Scene data collected from editor.")

            if not act_id:
                logger.error("Failed to determine target Act ID for scene creation.")
                raise ActError(
                    "Could not determine the active act to add the scene to."
                )

            if not title or not title.strip():
                renderer.display_error("Scene title cannot be empty.")
                raise typer.Exit(1)

            logger.debug(
                "Calling scene_manager.create_scene for act %s with title='%s'",
                act_id,
                title,
            )
            scene = scene_manager.create_scene(
                act_id=act_id,
                title=title.strip(),
                description=description.strip() if description else None,
                make_active=True,  # New scenes become active by default
            )

            renderer.display_success("Scene added successfully!")
            renderer.display_scene_info(scene)
    except (GameError, SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("list")
def list_scenes(ctx: typer.Context) -> None:
    """List all scenes in the active act."""
    renderer: "Renderer" = ctx.obj["renderer"]
    with get_db_context() as session:
        scene_manager = SceneManager(session=session)

        try:
            act_id, active_scene = scene_manager.validate_active_context()
            active_scene_id = active_scene.id if active_scene else None
        except SceneError as e:
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

        scenes = scene_manager.list_scenes(act_id)
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
            renderer.display_scene_info(active_scene)

            if show_events:
                event_manager = scene_manager.event_manager
                events = event_manager.list_events(scene_id=active_scene.id)

                # Truncate descriptions if the list is long
                truncate_descriptions = len(events) > 3
                renderer.display_message("")  # Add a blank line for separation
                renderer.display_events_table(
                    events,
                    active_scene,
                    truncate_descriptions=truncate_descriptions,
                )

    except (SceneError, ActError) as e:
        renderer.display_error(f"Error: {str(e)}")


@scene_app.command("edit")
def edit_scene(
    ctx: typer.Context,
    identifier: Optional[str] = typer.Option(  # Rename scene_id to identifier
        None,
        "--id",  # Keep the option name as --id for user convenience
        help="ID or slug of the scene to edit (defaults to active scene)",  # Updated help text
    ),
) -> None:
    """[bold]Edit the title and description of a scene using its ID or slug.[/bold]

    Opens a structured editor to modify the title and description of a scene.
    If no [cyan]--id[/cyan] is provided (with an ID or slug), it edits the
    currently active scene.

    [yellow]Examples:[/yellow]
        [green]Edit the active scene:[/green]
        $ sologm scene edit

        [green]Edit a specific scene by ID:[/green]
        $ sologm scene edit --id <scene_uuid>

        [green]Edit a specific scene by slug:[/green]
        $ sologm scene edit --id <scene-slug>
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)
            scene_to_edit: Optional["Scene"] = None

            if identifier:
                logger.debug(
                    "Attempting to fetch specific scene with identifier: %s", identifier
                )
                # Use the new manager method that handles ID or slug
                scene_to_edit = scene_manager.get_scene_by_identifier_or_error(
                    identifier
                )
                logger.debug(
                    "Found specific scene: %s ('%s') using identifier '%s'",
                    scene_to_edit.id,
                    scene_to_edit.title,
                    identifier,
                )
            else:
                logger.debug("No identifier provided, fetching active scene.")
                # Existing logic to get active scene is fine
                context = scene_manager.get_active_context()
                scene_to_edit = context["scene"]
                logger.debug(
                    "Found active scene: %s ('%s')",
                    scene_to_edit.id,
                    scene_to_edit.title,
                )

            scene_data = {
                "title": scene_to_edit.title or "",
                "description": scene_to_edit.description or "",
            }

            structured_config = _get_scene_editor_config()
            try:
                game_name = scene_to_edit.act.game.name
                act_title = (
                    scene_to_edit.act.title or f"Act {scene_to_edit.act.sequence}"
                )
            except Exception as e:
                logger.warning(
                    "Could not fully load context for editor: %s", e, exc_info=True
                )
                game_name = "Unknown Game"
                act_title = "Unknown Act"

            context_info = _build_scene_editor_context(
                verb="Editing",
                game_name=game_name,
                act_title=act_title,
                scene_title=scene_to_edit.title,
                scene_id=scene_to_edit.id,  # Use actual ID here for display
            )

            editor_config_obj = EditorConfig(
                edit_message=f"Editing Scene: {scene_to_edit.title} ({scene_to_edit.id})",  # Use actual ID
                success_message="Scene updated successfully.",
                cancel_message="Edit cancelled. Scene unchanged.",
                error_message="Could not open editor.",
            )

            edited_data, status = edit_structured_data(
                data=scene_data,
                console=console,
                config=structured_config,
                context_info=context_info,
                editor_config=editor_config_obj,
                is_new=False,
                original_data_for_comments=scene_data,
            )

            if status == EditorStatus.SAVED_MODIFIED:
                logger.info(
                    "Editor returned SAVED_MODIFIED for scene %s.", scene_to_edit.id
                )
                # Pass the actual ID to the update method
                updated_scene = scene_manager.update_scene(
                    scene_id=scene_to_edit.id,
                    title=edited_data["title"],
                    description=edited_data["description"] or None,
                )
                logger.info("Scene %s updated successfully.", scene_to_edit.id)
                renderer.display_scene_info(updated_scene)

            elif status == EditorStatus.SAVED_UNCHANGED:
                logger.info(
                    "Editor returned SAVED_UNCHANGED for scene %s.", scene_to_edit.id
                )
                renderer.display_message(
                    "No changes detected. Scene unchanged."
                )  # Inform user
                raise typer.Exit(0)

            else:  # ABORTED, VALIDATION_ERROR, EDITOR_ERROR
                logger.info("Scene edit cancelled or failed (status: %s).", status.name)
                # Message should be displayed by edit_structured_data or caught below
                raise typer.Exit(0)  # Exit cleanly on abort

    except (SceneError, ActError, GameError) as e:
        logger.error("Error editing scene: %s", e, exc_info=True)
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        # Catch potential errors from edit_structured_data as well
        logger.exception("Unexpected error during scene edit.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("set-current")
def set_current_scene(
    ctx: typer.Context,
    identifier: str = typer.Argument(
        ..., help="ID or slug of the scene to make current"
    ),  # Rename and update help
) -> None:
    """[bold]Set which scene is currently being played using its ID or slug.[/bold]

    Makes the specified scene the 'active' scene within its act. Any subsequent
    commands that operate on the 'active scene' (like adding events) will target
    this scene.

    You must provide the ID or slug of the scene you want to activate.

    [yellow]Example:[/yellow]
        $ sologm scene set-current <scene_uuid_or_slug>
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    logger.debug("Attempting to set scene '%s' as current.", identifier)
    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            # Use the new manager method to find the scene by ID or slug
            # This handles the "not found" case automatically by raising SceneError
            target_scene = scene_manager.get_scene_by_identifier_or_error(identifier)
            logger.debug(
                "Found target scene %s ('%s') using identifier '%s'. Belongs to act %s.",
                target_scene.id,
                target_scene.title,
                identifier,
                target_scene.act_id,
            )

            # The get_scene_by_identifier_or_error already validated existence.
            # The set_current_scene manager method handles the logic of
            # deactivating others within the *same act* as the target scene.
            # No need for the complex act_id determination and validation here anymore.

            # Pass the actual ID to the manager method
            new_current = scene_manager.set_current_scene(target_scene.id)
            logger.info(
                "Successfully set scene %s ('%s') as current for act %s.",
                new_current.id,
                new_current.title,
                new_current.act_id,
            )

            renderer.display_success("Current scene updated successfully!")
            renderer.display_scene_info(new_current)

    except (
        GameError,
        SceneError,
        ActError,
    ) as e:  # Keep catching these specific errors
        logger.error("Error setting current scene: %s", e, exc_info=True)
        renderer.display_error(
            f"Error: {str(e)}"
        )  # Display the specific error (e.g., "Scene not found...")
        raise typer.Exit(1) from e
    except Exception as e:
        logger.exception("An unexpected error occurred during scene set-current: %s", e)
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e
