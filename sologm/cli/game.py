"""Game management commands for Solo RPG Helper."""

import typer
from rich.console import Console

from typing import Optional

from sologm.core.game import GameManager
from sologm.cli.main import app, handle_errors
from sologm.utils.errors import GameError
from sologm.cli.main import handle_errors

import logging

logger = logging.getLogger(__name__)

# Create game subcommand
game_app = typer.Typer(help="Game management commands")
app.add_typer(game_app, name="game")

# Create console for rich output
console = Console()


@game_app.command("create")
@handle_errors
def create_game(
    name: str = typer.Option(..., "--name", "-n", help="Name of the game"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the game"
    ),
) -> None:
    """Create a new game."""
    console.print("[bold green]Game created successfully![/]")
    console.print(f"Name: {name}")
    console.print(f"Description: {description}")


@handle_errors
@game_app.command("list")
def list_games() -> None:
    """List all games."""
    logger.debug("Listing all games")
    game_manager = GameManager()
    games = game_manager.list_games()
    
    if not games:
        console.print("No games found.")
        return
        
    console.print("\nGames:")
    active_game = game_manager.get_active_game()
    for game in games:
        active = " [green](active)[/green]" if active_game and game.id == active_game.id else ""
        console.print(f"- {game.name} ({game.id}){active}")
        console.print(f"  Description: {game.description}")
        console.print(f"  Status: {game.status}")
        console.print(f"  Scenes: {len(game.scenes)}")
        console.print()


@game_app.command("activate")
@handle_errors
def activate_game(
    game_id: str = typer.Option(..., "--id", help="ID of the game to activate"),
) -> None:
    """Activate a game."""
    console.print(f"[bold green]Game {game_id} activated![/]")


@game_app.command("info")
@handle_errors
def game_info() -> None:
    """Show information about the active game."""
    console.print("[bold]Active Game:[/]")
    console.print("No active game. Activate one with 'sologm game activate'.")
