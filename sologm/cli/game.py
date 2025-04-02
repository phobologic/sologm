"""Game management commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app, handle_errors

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


@game_app.command("list")
@handle_errors
def list_games() -> None:
    """List all games."""
    console.print("[bold]Games:[/]")
    console.print("No games found. Create one with 'sologm game create'.")


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
