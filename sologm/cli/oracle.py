"""Oracle interpretation commands for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm.cli.utils import display
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
        None, "--count", "-n", help="Number of interpretations to generate"
    ),
    show_prompt: bool = typer.Option(
        False,
        "--show-prompt",
        help="Show the prompt that would be sent to the AI without sending it",
    ),
) -> None:
    """Get interpretations for oracle results."""
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

        # Use the provided count or default to the config value
        if count is None:
            from sologm.utils.config import get_config

            config = get_config()
            count = int(config.get("default_interpretations", 5))

        if show_prompt:
            # Get the prompt that would be sent to the AI
            prompt = oracle_manager.build_interpretation_prompt_for_active_context(
                context, results, count
            )
            console.print("\n[bold blue]Prompt that would be sent to AI:[/bold blue]")
            console.print(prompt)
            return

        # Get the active context
        scene, act, game = oracle_manager.get_active_context()

        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = oracle_manager.get_interpretations(
            scene.id, context, results, count
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
    edit_context: bool = typer.Option(
        False, "--edit", "-e", help="Edit the context before retrying"
    ),
) -> None:
    """Request new interpretations using current context and results."""
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

        # Get the active context
        scene, act, game = oracle_manager.get_active_context()

        current_interp_set = oracle_manager.get_current_interpretation_set(scene.id)
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

        # Get the current context
        context = current_interp_set.context
        oracle_results = current_interp_set.oracle_results

        # If edit_context flag is set or user confirms editing
        if edit_context or typer.confirm(
            "Would you like to edit the context before retrying?"
        ):
            from sologm.cli.utils.structured_editor import (
                EditorConfig,
                FieldConfig,
                StructuredEditorConfig,
                edit_structured_data,
            )

            # Create editor configurations
            editor_config = EditorConfig(
                edit_message="Current context:",
                success_message="Context updated.",
                cancel_message="Context unchanged.",
                error_message="Could not open editor",
            )

            # Configure the structured editor fields
            structured_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="context",
                        display_name="Oracle Context",
                        help_text="The question or context for the oracle "
                        "interpretation",
                        required=True,
                        multiline=True,
                    ),
                ]
            )

            # Use the structured editor
            context_data = {"context": context}
            edited_data, was_modified = edit_structured_data(
                data=context_data,
                console=console,
                config=structured_config,
                context_info="Edit the context for the oracle interpretation:\n",
                editor_config=editor_config,
                is_new=False,  # This is an existing context
            )

            if was_modified:
                context = edited_data["context"]

        console.print("\nGenerating new interpretations...", style="bold blue")
        new_interp_set = oracle_manager.get_interpretations(
            scene.id,
            context,  # Use the potentially updated context
            oracle_results,
            count=count,
            retry_attempt=current_interp_set.retry_attempt + 1,
            previous_set_id=current_interp_set.id,  # Pass the current set ID
        )

        display.display_interpretation_set(console, new_interp_set)

    except OracleError as e:
        logger.error(f"Failed to retry interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("list")
def list_interpretation_sets(
    act_id: Optional[str] = typer.Option(
        None, "--act-id", "-a", help="ID of the act to list interpretations from"
    ),
    scene_id: Optional[str] = typer.Option(
        None, "--scene-id", "-s", help="ID of the scene to list interpretations from"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of interpretation sets to show"
    ),
) -> None:
    """List oracle interpretation sets for the current scene or act.

    If neither scene-id nor act-id is provided, uses the active scene.
    """
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

            # If neither scene_id nor act_id is provided, use active context
            if not scene_id and not act_id:
                try:
                    active_scene, active_act, _ = oracle_manager.get_active_context()
                    scene_id = active_scene.id
                    act_id = active_act.id
                except OracleError as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
                    console.print(
                        "[yellow]Please specify --scene-id or --act-id[/yellow]"
                    )
                    raise typer.Exit(1) from e

            # Get interpretation sets
            interp_sets = oracle_manager.list_interpretation_sets(
                scene_id=scene_id, act_id=act_id, limit=limit
            )

            if not interp_sets:
                if scene_id:
                    console.print(
                        f"[yellow]No interpretation sets found for scene ID: {scene_id}[/yellow]"
                    )
                else:
                    console.print(
                        f"[yellow]No interpretation sets found for act ID: {act_id}[/yellow]"
                    )
                raise typer.Exit(0)

            # Display the interpretation sets
            display.display_interpretation_sets_table(console, interp_sets)

    except OracleError as e:
        logger.error(f"Failed to list interpretation sets: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("show")
def show_interpretation_set(
    set_id: str = typer.Argument(..., help="ID of the interpretation set to show"),
) -> None:
    """Show details of a specific interpretation set."""
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

            # Get the interpretation set
            interp_set = oracle_manager.get_interpretation_set(set_id)

            # Display the interpretation set
            display.display_interpretation_set(console, interp_set, show_context=True)

    except OracleError as e:
        logger.error(f"Failed to show interpretation set: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e


@oracle_app.command("status")
def show_interpretation_status() -> None:
    """Show current interpretation set status."""
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

        # Get the active context
        scene, act, game = oracle_manager.get_active_context()

        current_interp_set = oracle_manager.get_current_interpretation_set(scene.id)
        if not current_interp_set:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        # Display the interpretation status using the display helper
        display.display_interpretation_status(console, current_interp_set)

        # Display the interpretation set
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
        None,
        "--id",
        "-i",
        help="Identifier of the interpretation to select (number, slug, or UUID)",
    ),
    interpretation_set_id: str = typer.Option(
        None,
        "--set-id",
        "-s",
        help="ID of the interpretation set (uses current if not specified)",
    ),
    edit: bool = typer.Option(
        False,
        "--edit",
        "-e",
        help="Edit the event description before adding",
    ),
) -> None:
    """Select an interpretation to add as an event.

    You can specify the interpretation using:
    - A sequence number (1, 2, 3...)
    - The slug (derived from the title)
    - The full UUID
    """
    from sologm.database.session import get_db_context

    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

        # Get the active context
        scene, act, game = oracle_manager.get_active_context()

        if not interpretation_set_id:
            current_interp_set = oracle_manager.get_current_interpretation_set(scene.id)
            if not current_interp_set:
                console.print(
                    "[red]No current interpretation set. Specify --set-id "
                    "or run 'oracle interpret' first.[/red]"
                )
                raise typer.Exit(1)
            interpretation_set_id = current_interp_set.id

        if not interpretation_id:
            console.print(
                "[red]Please specify which interpretation to select with --id. "
                "You can use the number (1, 2, 3...), the slug, or the UUID.[/red]"
            )
            raise typer.Exit(1)

        # Mark the interpretation as selected
        selected = oracle_manager.select_interpretation(
            interpretation_set_id, interpretation_id
        )

        console.print("\nSelected interpretation:")
        display.display_interpretation(console, selected)

        if typer.confirm("\nAdd this interpretation as an event?"):
            # Get the interpretation set to access context and results
            interp_set = oracle_manager.get_interpretation_set(interpretation_set_id)

            # Create a more comprehensive default description
            default_description = (
                f"Question: {interp_set.context}\n"
                f"Oracle: {interp_set.oracle_results}\n"
                f"Interpretation: {selected.title} - {selected.description}"
            )

            # Allow editing if requested or if user confirms
            custom_description = default_description
            if edit or typer.confirm("Would you like to edit the event description?"):
                from sologm.cli.utils.structured_editor import (
                    EditorConfig,
                    FieldConfig,
                    StructuredEditorConfig,
                    edit_structured_data,
                )

                # Create editor configurations
                editor_config = EditorConfig(
                    edit_message="Edit the event description:",
                    success_message="Event description updated.",
                    cancel_message="Event description unchanged.",
                    error_message="Could not open editor",
                )

                # Configure the structured editor fields
                structured_config = StructuredEditorConfig(
                    fields=[
                        FieldConfig(
                            name="description",
                            display_name="Event Description",
                            help_text="The detailed description of the event",
                            required=True,
                            multiline=True,
                        ),
                    ]
                )

                # Use the structured editor
                event_data = {"description": default_description}
                edited_data, was_modified = edit_structured_data(
                    data=event_data,
                    console=console,
                    config=structured_config,
                    context_info="Edit the event description below:\n",
                    editor_config=editor_config,
                    is_new=True,  # This is a new event
                )

                if was_modified:
                    custom_description = edited_data["description"]

            # Add the event with possibly edited description
            event = oracle_manager.add_interpretation_event(
                selected, custom_description
            )
            console.print("[bold green]Interpretation added as event.[/]")

            # Get the scene for display
            scene = oracle_manager.scene_manager.get_scene(scene.id)

            # Display the event in a more consistent way
            events = [event]  # Create a list with just this event
            display.display_events_table(console, events, scene)
        else:
            console.print("[yellow]Interpretation not added as event.[/yellow]")

    except OracleError as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e
