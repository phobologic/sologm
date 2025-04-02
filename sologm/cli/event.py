"""Event tracking commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app, handle_errors

# Create event subcommand
event_app = typer.Typer(help="Event tracking commands")
app.add_typer(event_app, name="event")

# Create console for rich output
console = Console()


@event_app.command("add")
@handle_errors
def add_event(
    text: str = typer.Option(..., "--text", "-t", help="Text of the event"),
) -> None:
    """Add an event to the active scene."""
    console.print("[bold green]Event added successfully![/]")
    console.print(f"Event: {text}")


@event_app.command("list")
@handle_errors
def list_events(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of events to show"),
) -> None:
    """List events in the active scene."""
    console.print("[bold]Events:[/]")
    console.print(f"Showing last {limit} events:")
    console.print("No events found. Add one with 'sologm event add'.")
