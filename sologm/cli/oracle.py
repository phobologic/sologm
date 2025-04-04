"""Oracle interpretation commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

from sologm.cli import display
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
        game_id, scene_id = manager.validate_active_context()

        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = manager.get_interpretations(
            game_id, scene_id, context, results, count
        )

        display.display_interpretation_set(console, interp_set)

    except OracleError as e:
        logger.error(f"Failed to interpret oracle results: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("retry")
def retry_interpretation() -> None:
    """Request new interpretations using current context and results."""
    try:
        manager = OracleManager()
        game_id, scene_id = manager.validate_active_context()

        current = manager.get_current_interpretation(game_id)
        if not current:
            console.print(
                "[red]No current interpretation to retry. Run "
                "'oracle interpret' first.[/red]"
            )
            raise typer.Exit(1)

        console.print("\nGenerating new interpretations...", style="bold blue")
        interp_set = manager.get_interpretations(
            game_id,
            scene_id,
            current["context"],
            current["results"],
            retry_attempt=current["retry_count"] + 1,
        )

        display.display_interpretation_set(console, interp_set)

    except OracleError as e:
        logger.error(f"Failed to retry interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("status")
def show_interpretation_status() -> None:
    """Show current interpretation set status."""
    try:
        manager = OracleManager()
        game_id, scene_id = manager.validate_active_context()

        current = manager.get_current_interpretation(game_id)
        if not current:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        interp_set = manager.get_interpretation_set(
            game_id, scene_id, current["id"]
        )

        console.print("\n[bold]Current Oracle Interpretation[/bold]")
        console.print(f"Set ID: [bold]{current['id']}[/bold]")
        console.print(f"Context: {current['context']}")
        console.print(f"Results: {current['results']}")
        console.print(f"Retry count: {current['retry_count']}\n")

        display.display_interpretation_set(console, interp_set, show_context=False)

    except OracleError as e:
        logger.error(f"Failed to show interpretation status: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


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
        game_id, scene_id = manager.validate_active_context()

        if not interpretation_set_id:
            current = manager.get_current_interpretation(game_id)
            if not current:
                console.print(
                    "[red]No current interpretation set. Specify --set-id "
                    "or run 'oracle interpret' first.[/red]"
                )
                raise typer.Exit(1)
            interpretation_set_id = current["id"]

        if not interpretation_id:
            console.print(
                "[red]Please specify which interpretation to select with --id.[/red]"
            )
            raise typer.Exit(1)

        selected = manager.select_interpretation(
            game_id, scene_id, interpretation_set_id, interpretation_id, add_event=False
        )

        console.print("\nSelected interpretation:")
        display.display_interpretation(console, selected)

        if typer.confirm("\nAdd this interpretation as an event?"):
            manager.add_interpretation_event(game_id, scene_id, selected)
            console.print("\n[green]Added interpretation as event.[/green]")
        else:
            console.print("\n[yellow]Interpretation not added as event.[/yellow]")

    except OracleError as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e
