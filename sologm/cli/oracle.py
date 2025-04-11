"""Oracle interpretation commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

from sologm.cli.utils import display
from sologm.core.act import ActManager
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
        None, "--count", "-n", help="Number of interpretations to generate"
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
        act_manager = ActManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        # Use the provided count or default to the config value
        if count is None:
            from sologm.utils.config import get_config

            config = get_config()
            count = int(config.get("default_interpretations", 5))

        if show_prompt:
            # Get the prompt that would be sent to the AI
            prompt = oracle_manager.build_interpretation_prompt_for_active_context(
                game_manager, scene_manager, act_manager, context, results, count
            )
            console.print("\n[bold blue]Prompt that would be sent to AI:[/bold blue]")
            console.print(prompt)
            return

        # Validate active context (will raise OracleError if no active game/scene)
        game_id, act_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager, act_manager
        )

        console.print("\nGenerating interpretations...", style="bold blue")
        interp_set = oracle_manager.get_interpretations(
            game_id, act_id, scene_id, context, results, count
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
    try:
        game_manager = GameManager()
        act_manager = ActManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, act_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager, act_manager
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
            game_id,
            act_id,
            scene_id,
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


@oracle_app.command("status")
def show_interpretation_status() -> None:
    """Show current interpretation set status."""
    try:
        game_manager = GameManager()
        act_manager = ActManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, act_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager, act_manager
        )

        current_interp_set = oracle_manager.get_current_interpretation_set(scene_id)
        if not current_interp_set:
            console.print("[yellow]No current interpretation set.[/yellow]")
            raise typer.Exit(0)

        # Use a more consistent display approach
        from rich.panel import Panel

        from sologm.cli.utils.styled_text import StyledText

        st = StyledText
        panel_title = st.title("Current Oracle Interpretation")

        # Create metadata with consistent formatting
        metadata = {
            "Set ID": current_interp_set.id,
            "Retry count": current_interp_set.retry_attempt,
            "Resolved": any(
                interp.is_selected for interp in current_interp_set.interpretations
            ),
        }

        # Create panel content
        panel_content = st.combine(
            st.subtitle("Context:"),
            " ",
            current_interp_set.context,
            "\n",
            st.subtitle("Results:"),
            " ",
            current_interp_set.oracle_results,
            "\n",
            st.format_metadata(metadata),
        )

        # Create and display the panel
        panel = Panel(
            panel_content,
            title=panel_title,
            border_style="bright_blue",
            title_align="left",
        )
        console.print(panel)
        console.print()

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
    try:
        game_manager = GameManager()
        act_manager = ActManager()
        scene_manager = SceneManager()
        oracle_manager = OracleManager()

        game_id, act_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager, act_manager
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
                scene_id, selected, custom_description
            )
            console.print("[bold green]Interpretation added as event.[/]")

            # Get the scene for display
            scene = scene_manager.get_scene(game_id, scene_id)

            # Display the event in a more consistent way
            events = [event]  # Create a list with just this event
            display.display_events_table(console, events, scene)
        else:
            console.print("[yellow]Interpretation not added as event.[/yellow]")

    except OracleError as e:
        logger.error(f"Failed to select interpretation: {e}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) from e
