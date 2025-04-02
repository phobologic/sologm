"""Scene management commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app, handle_errors

# Create scene subcommand
scene_app = typer.Typer(help="Scene management commands")
app.add_typer(scene_app, name="scene")

# Create console for rich output
console = Console()


@scene_app.command("create")
@handle_errors
def create_scene(
    title: str = typer.Option(..., "--title", "-t", help="Title of the scene"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the scene"
    ),
) -> None:
    """Create a new scene in the active game."""
    console.print("[bold green]Scene created successfully![/]")
    console.print(f"Title: {title}")
    console.print(f"Description: {description}")


@scene_app.command("list")
@handle_errors
def list_scenes() -> None:
    """List all scenes in the active game."""
    console.print("[bold]Scenes:[/]")
    console.print("No scenes found. Create one with 'sologm scene create'.")


@scene_app.command("info")
@handle_errors
def scene_info() -> None:
    """Show information about the active scene."""
    console.print("[bold]Active Scene:[/]")
    console.print("No active scene. Create one with 'sologm scene create'.")


@scene_app.command("complete")
@handle_errors
def complete_scene() -> None:
    """Complete the active scene."""
    console.print("[bold green]Scene completed successfully![/]")
