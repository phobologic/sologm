"""Game management commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.cli.main import app

import logging

logger = logging.getLogger(__name__)

# Create game subcommand
game_app = typer.Typer(help="Game management commands")
app.add_typer(game_app, name="game")

# Create console for rich output
console = Console()


@game_app.command("create")
def create_game(
    name: str = typer.Option(..., "--name", "-n", help="Name of the game"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the game"
    ),
) -> None:
    """Create a new game."""
    logger.debug(f"Creating game with name='{name}', "
                 "description='{description}'")
    game_manager = GameManager()
    game = game_manager.create_game(name=name, description=description)

    console.print("[bold green]Game created successfully![/]")
    console.print(f"Name: {game.name} ({game.id})")
    console.print(f"Description: {game.description}")


@game_app.command("list")
def list_games() -> None:
    """List all games."""
    logger.debug("Listing all games")
    game_manager = GameManager()
    games = game_manager.list_games()

    if not games:
        console.print("No games found.")
        return

    scene_manager = SceneManager()
    console.print("\nGames:")
    active_game = game_manager.get_active_game()
    for game in games:
        active = ""
        if active_game and game.id == active_game.id:
            active = " [green](active)[/green]"
        # Get actual scene count from disk
        scenes = scene_manager.list_scenes(game.id)
        console.print(f"- {game.name} ({game.id}){active}")
        console.print(f"  Description: {game.description}")
        console.print(f"  Scenes: {len(scenes)}")
        console.print()


@game_app.command("activate")
def activate_game(
    game_id: str = typer.Option(...,
                                "--id",
                                help="ID of the game to activate"),
) -> None:
    """Activate a game."""
    logger.debug(f"Activating game with id='{game_id}'")
    game_manager = GameManager()
    game = game_manager.activate_game(game_id)

    console.print("[bold green]Game activated successfully![/]")
    console.print(f"Name: {game.name} ({game.id})")
    console.print(f"Description: {game.description}")


@game_app.command("info")
def game_info() -> None:
    """Show information about the active game."""
    logger.debug("Getting active game info")
    game_manager = GameManager()
    game = game_manager.get_active_game()

    if not game:
        console.print("No active game. Use 'sologm game activate' to set one.")
        return

    # Get scenes and active scene
    scene_manager = SceneManager()
    scenes = scene_manager.list_scenes(game.id)  # This will clean up missing scenes
    active_scene = scene_manager.get_active_scene(game.id)

    console.print("\n[bold]Active Game:[/]")
    console.print(f"Name: {game.name} ({game.id})")
    console.print(f"Description: {game.description}")
    console.print(f"Created: {game.created_at}")
    console.print(f"Modified: {game.modified_at}")
    console.print(f"Scenes: {len(scenes)}")  # Use actual scene count
