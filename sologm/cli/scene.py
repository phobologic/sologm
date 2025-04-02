"""Scene management commands for Solo RPG Helper."""

import logging
import typer
from rich.console import Console
from rich.table import Table

from sologm.cli.main import app, handle_errors
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import GameError, SceneError

# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")
app.add_typer(scene_app, name="scene")

# Create console for rich output
console = Console()
logger = logging.getLogger(__name__)


@handle_errors
@scene_app.command("create")
def create_scene(
    title: str = typer.Option(..., "--title", "-t", help="Title of the scene"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the scene"
    ),
) -> None:
    """Create a new scene in the active game."""
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

    console.print("[bold green]Scene created successfully![/]")
    console.print(f"Title: {scene.title}")
    console.print(f"Description: {scene.description}")
    console.print(f"Status: {scene.status}")
    console.print(f"Sequence: {scene.sequence}")


@handle_errors
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
    if not scenes:
        console.print("No scenes found. Create one with 'sologm scene create'.")
        return

    # Create table
    table = Table(title=f"Scenes in {active_game.name}")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Description")
    table.add_column("Status", style="green")
    table.add_column("Sequence", justify="right")

    for scene in scenes:
        table.add_row(
            scene.id,
            scene.title,
            scene.description,
            scene.status,
            str(scene.sequence)
        )

    console.print(table)


@handle_errors
@scene_app.command("info")
def scene_info() -> None:
    """Show information about the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Get active scene
    active_scene = scene_manager.get_active_scene(active_game.id)
    if not active_scene:
        console.print("No active scene. Create one with 'sologm scene create'.")
        return

    console.print("[bold]Active Scene:[/]")
    console.print(f"ID: {active_scene.id}")
    console.print(f"Title: {active_scene.title}")
    console.print(f"Description: {active_scene.description}")
    console.print(f"Status: {active_scene.status}")
    console.print(f"Sequence: {active_scene.sequence}")
    console.print(f"Created: {active_scene.created_at}")
    console.print(f"Modified: {active_scene.modified_at}")


@handle_errors
@scene_app.command("complete")
def complete_scene() -> None:
    """Complete the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Get active scene
    active_scene = scene_manager.get_active_scene(active_game.id)
    if not active_scene:
        raise SceneError("No active scene to complete.")

    # Complete the scene
    completed_scene = scene_manager.complete_scene(active_game.id, active_scene.id)
    console.print("[bold green]Scene completed successfully![/]")
    console.print(f"Completed scene: {completed_scene.title}")

@handle_errors
@scene_app.command("set-current")
def set_current_scene(
    scene_id: str = typer.Option(..., "--id", help="ID of the scene to make current")
) -> None:
    """Set which scene is currently being played."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set one.")

    # Set the current scene
    new_current = scene_manager.set_current_scene(active_game.id, scene_id)
    console.print("[bold green]Current scene updated successfully![/]")
    console.print(f"Current scene: {new_current.title}")
