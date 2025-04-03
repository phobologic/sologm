"""Oracle interpretation commands for Solo RPG Helper."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
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

        logger.debug("Getting active game ID")
        # Get active game and scene
        game_id = manager.file_manager.get_active_game_id()
        if not game_id:
            logger.debug("No active game found")
            console.print("[red]No active game found. Use 'game activate' first.[/red]")
            raise typer.Exit(1)

        logger.debug(f"Getting active scene ID for game {game_id}")
        scene_id = manager.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            logger.debug("No active scene found")
            console.print(
                "[red]No active scene found. Create or set a scene first.[/red]"
            )
            raise typer.Exit(1)

        # Get interpretations
        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = manager.get_interpretations(
            game_id, scene_id, context, results, count
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
                border_style="blue",
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


@oracle_app.command("retry")
def retry_interpretation() -> None:
    """Request new interpretations using current context and results."""
    try:
        manager = OracleManager()

        # Get active game and scene
        game_id = manager.file_manager.get_active_game_id()
        if not game_id:
            console.print("[red]No active game found. Use 'game activate' first.[/red]")
            raise typer.Exit(1)

        scene_id = manager.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            console.print(
                "[red]No active scene found. Create or set a scene first.[/red]"
            )
            raise typer.Exit(1)

        # Get current interpretation data
        game_data = manager.file_manager.read_yaml(
            manager.file_manager.get_game_path(game_id)
        )
        current = game_data.get("current_interpretation")

        if not current:
            console.print(
                "[red]No current interpretation to retry. Run 'oracle interpret' first.[/red]"
            )
            raise typer.Exit(1)

        # Get new interpretations with incremented retry count
        console.print("\nGenerating new interpretations...", style="bold blue")
        interp_set = manager.get_interpretations(
            game_id,
            scene_id,
            current["context"],
            current["results"],
            retry_attempt=current["retry_count"] + 1,
        )

        # Display results
        console.print("\n[bold]Oracle Interpretations (Retry)[/bold]")
        console.print(f"Context: {current['context']}")
        console.print(f"Results: {current['results']}\n")

        for i, interp in enumerate(interp_set.interpretations, 1):
            panel = Panel(
                Text.from_markup(
                    f"[bold]{interp.title}[/bold]\n\n{interp.description}"
                ),
                title=f"Interpretation {i} [dim][{interp.id}][/dim]",
                border_style="blue",
            )
            console.print(panel)
            console.print()

        console.print(
            f"\nInterpretation set ID: [bold]{interp_set.id}[/bold] "
            "(use this ID to select an interpretation)"
        )

    except Exception as e:
        logger.error(f"Failed to retry interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@oracle_app.command("status")
def show_interpretation_status() -> None:
    """Show current interpretation set status."""
    try:
        manager = OracleManager()

        # Get active game and scene
        game_id = manager.file_manager.get_active_game_id()
        if not game_id:
            console.print("[red]No active game found. Use 'game activate' first.[/red]")
            raise typer.Exit(1)

        scene_id = manager.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            console.print(
                "[red]No active scene found. Create or set a scene first.[/red]"
            )
            raise typer.Exit(1)

        # Get current interpretation data
        game_data = manager.file_manager.read_yaml(
            manager.file_manager.get_game_path(game_id)
        )
        current = game_data.get("current_interpretation")

        if not current:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        # Load interpretation set
        interp_path = Path(
            manager.file_manager.get_interpretations_dir(game_id, scene_id),
            f"{current['id']}.yaml",
        )
        interp_data = manager.file_manager.read_yaml(interp_path)

        # Display current interpretation status
        console.print("\n[bold]Current Oracle Interpretation[/bold]")
        console.print(f"Set ID: [bold]{current['id']}[/bold]")
        console.print(f"Context: {current['context']}")
        console.print(f"Results: {current['results']}")
        console.print(f"Retry count: {current['retry_count']}\n")

        # Show all interpretations in the set
        for i, interp in enumerate(interp_data["interpretations"], 1):
            selected = (
                "[green](Selected)[/green] "
                if interp_data["selected_interpretation"] == i - 1
                else ""
            )
            panel = Panel(
                Text.from_markup(
                    f"[bold]{interp['title']}[/bold]\n\n{interp['description']}"
                ),
                title=f"Interpretation {i} [dim][{interp['id']}][/dim] {selected}",
                border_style="blue",
            )
            console.print(panel)
            console.print()

    except Exception as e:
        logger.error(f"Failed to show interpretation status: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@oracle_app.command("select")
def select_interpretation(
    interpretation_id: str = typer.Option(
        None, "--id", "-i", help="ID of the interpretation to select"
    ),
    interpretation_set_id: str = typer.Option(
        None,
        "--set-id",
        "-s",
        help="ID of the interpretation set (uses current if not specified)",
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
            console.print(
                "[red]No active scene found. Create or set a scene first.[/red]"
            )
            raise typer.Exit(1)

        # If no set ID provided, use current interpretation
        if not interpretation_set_id:
            game_data = manager.file_manager.read_yaml(
                manager.file_manager.get_game_path(game_id)
            )
            current = game_data.get("current_interpretation")
            if not current:
                console.print(
                    "[red]No current interpretation set. Specify --set-id or run 'oracle interpret' first.[/red]"
                )
                raise typer.Exit(1)
            interpretation_set_id = current["id"]

        if not interpretation_id:
            console.print(
                "[red]Please specify which interpretation to select with --id.[/red]"
            )
            raise typer.Exit(1)

        # Select interpretation but don't add as event yet
        selected = manager.select_interpretation(
            game_id, scene_id, interpretation_set_id, interpretation_id, add_event=False
        )

        # Display result and ask for confirmation
        panel = Panel(
            Text.from_markup(
                f"[bold]{selected.title}[/bold]\n\n{selected.description}"
            ),
            title="Selected Interpretation",
            border_style="blue",
        )
        console.print("\nSelected interpretation:")
        console.print(panel)

        # Ask if they want to add it as an event
        if typer.confirm("\nAdd this interpretation as an event?"):
            manager.add_interpretation_event(game_id, scene_id, selected)
            console.print("\n[green]Added interpretation as event.[/green]")
        else:
            console.print("\n[yellow]Interpretation not added as event.[/yellow]")

    except Exception as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
