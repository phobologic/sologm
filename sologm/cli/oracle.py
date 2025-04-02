"""Oracle interpretation commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app, handle_errors
from sologm.utils.config import config

# Create oracle subcommand
oracle_app = typer.Typer(help="Oracle interpretation commands")
app.add_typer(oracle_app, name="oracle")

# Create console for rich output
console = Console()


@oracle_app.command("interpret")
@handle_errors
def interpret_oracle(
    context: str = typer.Option(
        ..., "--context", "-c", help="Context or question for interpretation"
    ),
    results: str = typer.Option(
        ..., "--results", "-r", help="Oracle results to interpret"
    ),
    count: int = typer.Option(
        None,
        "--count",
        "-n",
        help="Number of interpretations to generate",
    ),
) -> None:
    """Interpret oracle results."""
    # Use default from config if count not provided
    if count is None:
        count = config.get("default_interpretations", 5)

    console.print("[bold]Oracle Interpretation:[/]")
    console.print(f"Context: {context}")
    console.print(f"Oracle Results: {results}")
    console.print(f"Generating {count} interpretations...")
    console.print(
        "[yellow]This is a placeholder. API integration will be implemented later.[/]"
    )


@oracle_app.command("select")
@handle_errors
def select_interpretation(
    interpretation_id: str = typer.Option(
        ..., "--id", help="ID of the interpretation to select"
    ),
) -> None:
    """Select an interpretation to add as an event."""
    console.print(f"[bold green]Interpretation {interpretation_id} selected![/]")
    console.print("Added as an event to the active scene.")
