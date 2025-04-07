"""Scene management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from typer import Typer

    app: Typer
from sologm.cli.utils.display import display_scene_info
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import GameError, SceneError

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
    """Add a new scene to the active game."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Create the scene
    scene = scene_manager.create_scene(
        game_id=active_game.id,
        title=title,
        description=description,
    )

    console.print("[bold green]Scene added successfully![/]")
    console.print(f"Title: {scene.title}")
    console.print(f"Description: {scene.description}")
    console.print(f"Status: {scene.status.value}")
    console.print(f"Sequence: {scene.sequence}")


@scene_app.command("list")
def list_scenes() -> None:
    """List all scenes in the active game."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Get scenes
    scenes = scene_manager.list_scenes(active_game.id)

    # Get active scene
    active_scene = scene_manager.get_active_scene(active_game.id)
    active_scene_id = active_scene.id if active_scene else None

    # Use the display helper function
    from sologm.cli.utils.display import display_scenes_table

    display_scenes_table(console, scenes, active_scene_id)


@scene_app.command("info")
def scene_info() -> None:
    """Show information about the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    try:
        _, active_scene = scene_manager.validate_active_context(game_manager)
        display_scene_info(console, active_scene)
    except SceneError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


@scene_app.command("complete")
def complete_scene() -> None:
    """Complete the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    try:
        game_id, active_scene = scene_manager.validate_active_context(game_manager)
        completed_scene = scene_manager.complete_scene(game_id, active_scene.id)
        console.print("[bold green]Scene completed successfully![/]")
        console.print(f"Completed scene: {completed_scene.title}")
    except SceneError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


@scene_app.command("edit")
def edit_scene(
    scene_id: str = typer.Option(
        None, "--id", help="ID of the scene to edit (defaults to active scene)"
    ),
) -> None:
    """Edit the title and description of a scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    try:
        # Get active game
        game_id, active_scene = scene_manager.validate_active_context(game_manager)

        # If no scene_id provided, use the active scene
        if not scene_id:
            scene_id = active_scene.id

        # Get the scene to edit
        scene = scene_manager.get_scene(game_id, scene_id)
        if not scene:
            console.print(f"[bold red]Error:[/] Scene '{scene_id}' not found.")
            raise typer.Exit(1)

        # Prepare the text for editing
        # Format: Title on first line, blank line, then description
        original_text = f"{scene.title}\n\n{scene.description}"

        # Use the editor utility
        from sologm.cli.utils.editor import edit_text

        edited_text, was_modified = edit_text(
            original_text,
            console=console,
            message=f"Editing scene {scene_id}:\nEnter the title on the first line, followed by a blank line, then the description:",
            success_message="Scene updated successfully.",
            cancel_message="Scene unchanged.",
            error_message="Could not open editor",
        )

        if was_modified:
            # Parse the edited text
            lines = edited_text.split("\n")
            new_title = lines[0].strip()

            # Description starts after the first blank line
            description_start = 2  # Default if no blank line found
            for i, line in enumerate(lines[1:], 1):
                if not line.strip():
                    description_start = i + 1
                    break

            new_description = "\n".join(lines[description_start:]).strip()

            # Validate input
            if not new_title:
                console.print("[bold red]Error:[/] Scene title cannot be empty.")
                raise typer.Exit(1)

            # Update the scene
            updated_scene = scene_manager.update_scene(
                game_id=game_id,
                scene_id=scene_id,
                title=new_title,
                description=new_description,
            )

            console.print(f"[bold green]Scene updated successfully![/]")
            display_scene_info(console, updated_scene)
        else:
            console.print("[yellow]No changes made to the scene.[/yellow]")

    except SceneError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@scene_app.command("set-current")
def set_current_scene(
    scene_id: str = typer.Option(..., "--id", help="ID of the scene to make current"),
) -> None:
    """Set which scene is currently being played."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Get list of valid scenes first
    scenes = scene_manager.list_scenes(active_game.id)
    scene_ids = [s.id for s in scenes]

    # Check if scene_id exists before trying to set it
    if scene_id not in scene_ids:
        console.print(f"[bold red]Error:[/] Scene '{scene_id}' not found.")
        console.print("\nValid scene IDs:")
        for sid in scene_ids:
            console.print(f"  {sid}")
        return

    # Set the current scene
    new_current = scene_manager.set_current_scene(active_game.id, scene_id)
    console.print("[bold green]Current scene updated successfully![/]")
    console.print(f"Current scene: {new_current.title}")
