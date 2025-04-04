"""Game management commands for Solo RPG Helper."""

import logging

from rich.console import Console
import typer

from sologm.cli.display import display_game_info, display_games_table
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import GameError

logger = logging.getLogger(__name__)

# Create game subcommand
game_app = typer.Typer(help="Game management commands")

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
    try:
        logger.debug(f"Creating game with name='{name}', description='{description}'")
        game_manager = GameManager()
        game = game_manager.create_game(name=name, description=description)

        console.print("[bold green]Game created successfully![/]")
        console.print(f"Name: {game.name} ({game.id})")
        console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error creating game: {str(e)}[/red]")


@game_app.command("list")
def list_games() -> None:
    """List all games."""
    try:
        logger.debug("Listing all games")
        game_manager = GameManager()
        games = game_manager.list_games()
        active_game = game_manager.get_active_game()
        display_games_table(console, games, active_game)
    except GameError as e:
        console.print(f"[red]Error listing games: {str(e)}[/red]")


@game_app.command("activate")
def activate_game(
    game_id: str = typer.Option(..., "--id", help="ID of the game to activate"),
) -> None:
    """Activate a game."""
    try:
        logger.debug(f"Activating game with id='{game_id}'")
        game_manager = GameManager()
        game = game_manager.activate_game(game_id)

        console.print("[bold green]Game activated successfully![/]")
        console.print(f"Name: {game.name} ({game.id})")
        console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error activating game: {str(e)}[/red]")


@game_app.command("info")
def game_info() -> None:
    """Show information about the active game."""
    try:
        logger.debug("Getting active game info")
        game_manager = GameManager()
        game = game_manager.get_active_game()
        if not game:
            console.print("No active game. Use 'sologm game activate' to set one.")
            return

        scene_manager = SceneManager()
        active_scene = scene_manager.get_active_scene(game.id)
        display_game_info(console, game, active_scene)
    except GameError as e:
        console.print(f"[red]Error getting game info: {str(e)}[/red]")
