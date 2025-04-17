"""Scene management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer
from rich.console import Console

if TYPE_CHECKING:
    from typer import Typer

    app: Typer
from sologm.cli.utils.display import display_scene_info
from sologm.core.scene import SceneManager
from sologm.database.session import get_db_context
from sologm.utils.errors import ActError, GameError, SceneError

# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")

# Create console for rich output
console = Console()
logger = logging.getLogger(__name__)


@scene_app.command("add")
def add_scene(
    title: str = typer.Option(..., "--title", "-t", help="Title of the scene"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the scene"
    ),
) -> None:
    """Add a new scene to the active act."""

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

            console.print("[bold green]Scene added successfully![/]")
            display_scene_info(console, scene)
    except (GameError, SceneError, ActError) as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("list")
def list_scenes() -> None:
    """List all scenes in the active act."""
    from sologm.cli.utils.display import display_scenes_table

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

        # Use the display helper function - session still open for lazy loading
        display_scenes_table(console, scenes, active_scene_id)


@scene_app.command("info")
def scene_info(
    show_events: bool = typer.Option(
        True, "--events/--no-events", help="Show events associated with this scene"
    ),
) -> None:
    """Show information about the active scene and its events."""

    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            _, active_scene = scene_manager.validate_active_context()

            # Display scene information
            display_scene_info(console, active_scene)

            # If show_events is True, fetch and display events
            if show_events:
                from sologm.cli.utils.display import display_events_table

                # Access event_manager through scene_manager instead of creating a new instance
                event_manager = scene_manager.event_manager
                events = event_manager.list_events(scene_id=active_scene.id)

                # Display events table - decide whether to truncate based on number of events
                truncate_descriptions = (
                    len(events) > 3
                )  # Truncate if more than 3 events
                console.print()  # Add a blank line for separation
                display_events_table(
                    console,
                    events,
                    active_scene,
                    truncate_descriptions=truncate_descriptions,
                )

    except (SceneError, ActError) as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


@scene_app.command("complete")
def complete_scene() -> None:
    """Complete the active scene."""

    try:
        with get_db_context() as session:
            scene_manager = SceneManager(session=session)

            _, active_scene = scene_manager.validate_active_context()
            completed_scene = scene_manager.complete_scene(active_scene.id)
            console.print("[bold green]Scene completed successfully![/]")
            display_scene_info(console, completed_scene)
    except (SceneError, ActError) as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("edit")
def edit_scene(
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
                console.print(f"[bold red]Error:[/] Scene '{scene_id}' not found.")
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

                console.print("[bold green]Scene updated successfully![/]")
                display_scene_info(console, updated_scene)

    except (SceneError, ActError) as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("set-current")
def set_current_scene(
    scene_id: str = typer.Option(..., "--id", help="ID of the scene to make current"),
) -> None:
    """Set which scene is currently being played."""

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
                console.print(f"[bold red]Error:[/] Scene '{scene_id}' not found.")
                console.print("\nValid scene IDs:")
                for sid in scene_ids:
                    console.print(f"  {sid}")
                return

            # Set the current scene
            new_current = scene_manager.set_current_scene(scene_id)
            console.print("[bold green]Current scene updated successfully![/]")
            display_scene_info(console, new_current)
    except (GameError, SceneError, ActError) as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
