"""Oracle interpretation commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

from sologm.cli.utils import display
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
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
        help="Show the prompt that would be sent to the AI without sending it",
    ),
) -> None:
    """Get interpretations for oracle results."""
    try:
        game_manager = GameManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager
        )

        # Get game and scene details for prompt building
        game = game_manager.get_game(game_id)
        scene = scene_manager.get_scene(game_id, scene_id)

        # Get recent events
        from sologm.core.event import EventManager

        event_manager = EventManager()
        recent_events = event_manager.list_events(game_id, scene_id, limit=5)
        recent_event_descriptions = [event.description for event in recent_events]

        # Build prompt
        prompt = oracle_manager._build_prompt(
            game.description,
            scene.description,
            recent_event_descriptions,
            context,
            results,
            count,
        )

        if show_prompt:
            console.print("\n[bold blue]Prompt that would be sent to AI:[/bold blue]")
            console.print(prompt)
            return

        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = oracle_manager.get_interpretations(
            game_id, scene_id, context, results, count
        )

        display.display_interpretation_set(console, interp_set)

    except OracleError as e:
        logger.error(f"Failed to interpret oracle results: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("retry")
def retry_interpretation(
    count: int = typer.Option(
        None, "--count", "-c", help="Number of interpretations to generate"
    ),
) -> None:
    """Request new interpretations using current context and results."""
    try:
        game_manager = GameManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager
        )

        current_interp_set = oracle_manager.get_current_interpretation_set(scene_id)
        if not current_interp_set:
            console.print(
                "[red]No current interpretation to retry. Run "
                "'oracle interpret' first.[/red]"
            )
            raise typer.Exit(1)

        # Use the provided count or default to the config value
        if count is None:
            from sologm.utils.config import get_config
            config = get_config()
            count = int(config.get("default_interpretations", 5))

        console.print("\nGenerating new interpretations...", style="bold blue")
        new_interp_set = oracle_manager.get_interpretations(
            game_id,
            scene_id,
            current_interp_set.context,
            current_interp_set.oracle_results,
            count=count,
            retry_attempt=current_interp_set.retry_attempt + 1,
            previous_set_id=current_interp_set.id  # Pass the current set ID
        )

        display.display_interpretation_set(console, new_interp_set)

    except OracleError as e:
        logger.error(f"Failed to retry interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("status")
def show_interpretation_status() -> None:
    """Show current interpretation set status."""
    try:
        game_manager = GameManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager
        )

        current_interp_set = oracle_manager.get_current_interpretation_set(scene_id)
        if not current_interp_set:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        console.print("\n[bold]Current Oracle Interpretation[/bold]")
        console.print(f"Set ID: [bold]{current_interp_set.id}[/bold]")
        console.print(f"Context: {current_interp_set.context}")
        console.print(f"Results: {current_interp_set.oracle_results}")
        console.print(f"Retry count: {current_interp_set.retry_attempt}")

        # Check if any interpretation is selected
        has_selection = any(
            interp.is_selected for interp in current_interp_set.interpretations
        )
        console.print(f"Resolved: {has_selection}\n")

        display.display_interpretation_set(
            console, current_interp_set, show_context=False
        )

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
        game_manager = GameManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager
        )

        if not interpretation_set_id:
            current_interp_set = oracle_manager.get_current_interpretation_set(scene_id)
            if not current_interp_set:
                console.print(
                    "[red]No current interpretation set. Specify --set-id "
                    "or run 'oracle interpret' first.[/red]"
                )
                raise typer.Exit(1)
            interpretation_set_id = current_interp_set.id
            interpretation_set_id = current_interp_set.id

        if not interpretation_id:
            console.print(
                "[red]Please specify which interpretation to select with --id.[/red]"
            )
            raise typer.Exit(1)

        selected = oracle_manager.select_interpretation(
            interpretation_set_id, interpretation_id, add_event=False
        )

        console.print("\nSelected interpretation:")
        display.display_interpretation(console, selected)

        if typer.confirm("\nAdd this interpretation as an event?"):
            oracle_manager.add_interpretation_event(scene_id, selected)
            console.print("\n[green]Added interpretation as event.[/green]")
        else:
            console.print("\n[yellow]Interpretation not added as event.[/yellow]")

    except OracleError as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e
