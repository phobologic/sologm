"""Oracle interpretation commands for Solo RPG Helper."""

import typer
from rich.console import Console

from sologm.cli.main import app
from sologm.utils.config import config

# Create oracle subcommand
oracle_app = typer.Typer(help="Oracle interpretation commands")
app.add_typer(oracle_app, name="oracle")

# Create console for rich output
console = Console()


@oracle_app.command("interpret")
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
def select_interpretation(
    interpretation_id: str = typer.Option(
        ..., "--id", help="ID of the interpretation to select"
    ),
) -> None:
    """Select an interpretation to add as an event."""
    console.print(f"[bold green]Interpretation {interpretation_id} selected![/]")
    console.print("Added as an event to the active scene.")
"""Oracle interpretation CLI commands."""

import logging
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from sologm.core.oracle import OracleManager
from sologm.utils.errors import OracleError

logger = logging.getLogger(__name__)
oracle_app = typer.Typer(help="Oracle interpretation commands")
console = Console()

@oracle_app.command("interpret")
def interpret_oracle(
    context: str = typer.Option(
        ..., "--context", "-c", help="Context or question for interpretation"
    ),
    results: str = typer.Option(
        ..., "--results", "-r", help="Oracle results to interpret"
    ),
    count: int = typer.Option(
        3, "--count", "-n", help="Number of interpretations to generate"
    ),
) -> None:
    """Get interpretations for oracle results."""
    try:
        manager = OracleManager()
        
        # Get active game and scene
        game_id = manager.file_manager.get_active_game_id()
        if not game_id:
            console.print("[red]No active game found. Use 'game activate' first.[/red]")
            raise typer.Exit(1)
        
        scene_id = manager.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            console.print("[red]No active scene found. Create or set a scene first.[/red]")
            raise typer.Exit(1)
        
        # Get interpretations
        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = manager.get_interpretations(
            game_id,
            scene_id,
            context,
            results,
            count
        )
        
        # Display results
        console.print("\n[bold]Oracle Interpretations[/bold]")
        console.print(f"Context: {context}")
        console.print(f"Results: {results}\n")
        
        for i, interp in enumerate(interp_set.interpretations, 1):
            panel = Panel(
                Text.from_markup(
                    f"[bold]{interp.title}[/bold]\n\n{interp.description}"
                ),
                title=f"Interpretation {i} [dim][{interp.id}][/dim]",
                border_style="blue"
            )
            console.print(panel)
            console.print()
        
        console.print(
            f"\nInterpretation set ID: [bold]{interp_set.id}[/bold] "
            "(use this ID to select an interpretation)"
        )
        
    except Exception as e:
        logger.error(f"Failed to interpret oracle results: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@oracle_app.command("select")
def select_interpretation(
    interpretation_set_id: str = typer.Option(
        ..., "--set-id", "-s", help="ID of the interpretation set"
    ),
    interpretation_id: str = typer.Option(
        ..., "--id", "-i", help="ID of the interpretation to select"
    ),
) -> None:
    """Select an interpretation to add as an event."""
    try:
        manager = OracleManager()
        
        # Get active game and scene
        game_id = manager.file_manager.get_active_game_id()
        if not game_id:
            console.print("[red]No active game found. Use 'game activate' first.[/red]")
            raise typer.Exit(1)
        
        scene_id = manager.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            console.print("[red]No active scene found. Create or set a scene first.[/red]")
            raise typer.Exit(1)
        
        # Select interpretation
        selected = manager.select_interpretation(
            game_id,
            scene_id,
            interpretation_set_id,
            interpretation_id
        )
        
        # Display result
        panel = Panel(
            Text.from_markup(
                f"[bold]{selected.title}[/bold]\n\n{selected.description}"
            ),
            title="Selected Interpretation",
            border_style="green"
        )
        console.print("\nAdded interpretation as event:")
        console.print(panel)
        
    except Exception as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
