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
    show_prompt: bool = typer.Option(
        False,
        "--show-prompt",
        help="Show the prompt that would be sent to the AI without sending it"
    ),
) -> None:
    """Get interpretations for oracle results."""
    try:
        manager = OracleManager()
        game_id, scene_id = manager.validate_active_context()

        # Get game and scene details for prompt building
        game_data = manager._read_game_data(game_id)
        scene_data = manager._read_scene_data(game_id, scene_id)
        events_data = manager._read_events_data(game_id, scene_id)

        # Get recent events
        recent_events = [
            event["description"]
            for event in sorted(
                events_data.get("events", []),
                key=lambda x: x["created_at"],
                reverse=True,
            )[:5]
        ]

        # Build prompt
        prompt = manager._build_prompt(
            game_data["description"],
            scene_data["description"],
            recent_events,
            context,
            results,
            count,
        )

        if show_prompt:
            console.print("\n[bold blue]Prompt that would be sent to AI:[/bold blue]")
            console.print(prompt)
            return

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

        current_ref = manager.get_current_interpretation_reference(game_id)
        if not current_ref:
            console.print(
                "[red]No current interpretation to retry. Run "
                "'oracle interpret' first.[/red]"
            )
            raise typer.Exit(1)

        # Get the actual interpretation set
        try:
            interp_set = manager.get_interpretation_set(
                game_id, current_ref["scene_id"], current_ref["id"]
            )

            console.print("\nGenerating new interpretations...", style="bold blue")
            new_interp_set = manager.get_interpretations(
                game_id,
                scene_id,
                interp_set.context,
                interp_set.oracle_results,
                retry_attempt=current_ref["retry_count"] + 1,
            )

            display.display_interpretation_set(console, new_interp_set)

        except Exception as e:
            console.print(f"[red]Error loading interpretation set: {str(e)}[/red]")
            raise typer.Exit(1) from e

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

        current_ref = manager.get_current_interpretation_reference(game_id)
        if not current_ref:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        interp_set = manager.get_interpretation_set(
            game_id, current_ref["scene_id"], current_ref["id"]
        )

        console.print("\n[bold]Current Oracle Interpretation[/bold]")
        console.print(f"Set ID: [bold]{current_ref['id']}[/bold]")
        console.print(f"Context: {interp_set.context}")
        console.print(f"Results: {interp_set.oracle_results}")
        console.print(f"Retry count: {current_ref['retry_count']}")
        console.print(f"Resolved: {current_ref['resolved']}\n")

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
            current_ref = manager.get_current_interpretation_reference(game_id)
            if not current_ref:
                console.print(
                    "[red]No current interpretation set. Specify --set-id "
                    "or run 'oracle interpret' first.[/red]"
                )
                raise typer.Exit(1)
            interpretation_set_id = current_ref["id"]
            scene_id = current_ref["scene_id"]

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
