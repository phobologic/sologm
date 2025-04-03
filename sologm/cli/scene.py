"""Scene management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from typer import Typer
    app: Typer
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import GameError, SceneError

# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")

# Create console for rich output
console = Console()
logger = logging.getLogger(__name__)


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
        raise GameError("No active game. Use 'sologm game activate' to set " "one.")

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


@scene_app.command("list")
def list_scenes() -> None:
    """List all scenes in the active game."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set " "one.")

    # Get scenes and current scene ID
    scenes = scene_manager.list_scenes(active_game.id)
    if not scenes:
        console.print("No scenes found. Create one with 'sologm scene " "create'.")
        return

    current_scene_id = scene_manager.file_manager.get_active_scene_id(active_game.id)

    # Create table
    table = Table(title=f"Scenes in {active_game.name}")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Description")
    table.add_column("Status", style="green")
    table.add_column("Current", style="yellow", justify="center")
    table.add_column("Sequence", justify="right")

    for scene in scenes:
        table.add_row(
            scene.id,
            scene.title,
            scene.description,
            scene.status,
            "✓" if scene.id == current_scene_id else "",
            str(scene.sequence),
        )

    console.print(table)


@scene_app.command("info")
def scene_info() -> None:
    """Show information about the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set " "one.")

    # Get active scene
    active_scene = scene_manager.get_active_scene(active_game.id)
    if not active_scene:
        console.print("No active scene. Create one with 'sologm scene " "create'.")
        return

    console.print("[bold]Active Scene:[/]")
    console.print(f"  ID: {active_scene.id}")
    console.print(f"  Title: {active_scene.title}")
    console.print(f"  Description: {active_scene.description}")
    console.print(f"  Status: {active_scene.status}")
    console.print(f"  Sequence: {active_scene.sequence}")
    console.print(f"  Created: {active_scene.created_at}")
    console.print(f"  Modified: {active_scene.modified_at}")


@scene_app.command("complete")
def complete_scene() -> None:
    """Complete the active scene."""
    game_manager = GameManager()
    scene_manager = SceneManager()

    # Get active game
    active_game = game_manager.get_active_game()
    if not active_game:
        raise GameError("No active game. Use 'sologm game activate' to set " "one.")

    # Get active scene
    active_scene = scene_manager.get_active_scene(active_game.id)
    if not active_scene:
        raise SceneError("No active scene to complete.")

    # Complete the scene
    completed_scene = scene_manager.complete_scene(active_game.id, active_scene.id)
    console.print("[bold green]Scene completed successfully![/]")
    console.print(f"Completed scene: {completed_scene.title}")


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
        raise GameError("No active game. Use 'sologm game activate' to set " "one.")

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
