"""Oracle interpretation commands for Solo RPG Helper."""

import logging
from typing import Any, Dict, Optional, Tuple

import typer
from rich.console import Console

from sologm.cli.rendering.base import Renderer
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    EditorStatus,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.core.oracle import OracleManager
from sologm.core.oracle import OracleManager
from sologm.database.session import get_db_context
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.utils.config import get_config
from sologm.utils.errors import OracleError

logger = logging.getLogger(__name__)
oracle_app = typer.Typer(help="Oracle interpretation commands")


# --- Helper Functions for Editor Interactions ---


def _prompt_for_oracle_input_if_needed(
    context: Optional[str],
    results: Optional[str],
    console: Console,
    renderer: Renderer,
) -> Tuple[str, str]:
    """Prompts user for oracle context and results via editor if not provided.

    Args:
        context: Initial context (can be None).
        results: Initial results (can be None).
        console: Rich console instance.
        renderer: Renderer instance.

    Returns:
        Tuple containing the final context and results.

    Raises:
        typer.Exit: If user cancels or an editor error occurs.
    """
    if context is not None and results is not None:
        return context, results

    renderer.display_message(
        "Context or results not provided. Opening editor...",
        style="italic yellow",
    )

    field_configs = [
        FieldConfig(
            name="context",
            display_name="Oracle Context",
            help_text=("The question or context for the oracle interpretation."),
            required=True,
            multiline=True,
        ),
        FieldConfig(
            name="results",
            display_name="Oracle Results",
            help_text=("The raw results from the oracle (e.g., dice roll, card draw)."),
            required=True,
            multiline=False,  # Typically single line
        ),
    ]
    structured_config = StructuredEditorConfig(fields=field_configs)
    editor_config = EditorConfig(
        edit_message="Enter Oracle Details:",
        success_message="Oracle details updated.",
        cancel_message="Interpretation cancelled.",
    )

    # Prepare initial data (pre-fill if one option was provided)
    initial_data: Dict[str, Any] = {
        "context": context or "",
        "results": results or "",
    }

    edited_data, status = edit_structured_data(
        data=initial_data,
        console=console,
        config=structured_config,
        editor_config=editor_config,
        context_info=("Please provide the context and results for the oracle."),
        is_new=True,
    )

    if status in (
        EditorStatus.SAVED_MODIFIED,
        EditorStatus.SAVED_UNCHANGED,
    ):
        final_context = edited_data.get("context")
        final_results = edited_data.get("results")
        # Basic check after editor, though validation should catch empty required fields
        if not final_context or not final_results:
            renderer.display_error("Context and Results are required.")
            raise typer.Exit(1)
        return final_context, final_results
    elif status == EditorStatus.ABORTED:
        renderer.display_warning("Interpretation cancelled.")
        raise typer.Exit(0)
    else:  # VALIDATION_ERROR or EDITOR_ERROR
        # Error message should be displayed by edit_structured_data
        raise typer.Exit(1)


def _edit_oracle_input(
    initial_context: str,
    initial_results: str,
    console: Console,
    renderer: Renderer,
) -> Tuple[str, str]:
    """Opens editor to allow modification of oracle context and results.

    Args:
        initial_context: The starting context.
        initial_results: The starting results.
        console: Rich console instance.
        renderer: Renderer instance.

    Returns:
        Tuple containing the final context and results.

    Raises:
        typer.Exit: If user cancels or an editor error occurs.
    """
    renderer.display_message(
        "Opening editor to refine context and results...",
        style="italic yellow",
    )

    editor_config = EditorConfig(
        edit_message="Edit Context and Results:",
        success_message="Context/Results updated.",
        cancel_message="Context/Results unchanged.",
        error_message="Could not open editor",
    )
    structured_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="context",
                display_name="Oracle Context",
                help_text=("The question or context for the oracle interpretation."),
                required=True,
                multiline=True,
            ),
            FieldConfig(
                name="results",
                display_name="Oracle Results",
                help_text=(
                    "The raw results from the oracle (e.g., dice roll, card draw)."
                ),
                required=True,
                multiline=False,
            ),
        ]
    )

    initial_data = {"context": initial_context, "results": initial_results}

    edited_data, status = edit_structured_data(
        data=initial_data,
        console=console,
        config=structured_config,
        context_info="Edit the context and/or results before retrying:\n",
        editor_config=editor_config,
        is_new=False,
    )
    if status in (
        EditorStatus.SAVED_MODIFIED,
        EditorStatus.SAVED_UNCHANGED,
    ):
        final_context = edited_data.get("context")
        final_results = edited_data.get("results")
        if not final_context or not final_results:
            renderer.display_error("Context and Results cannot be empty.")
            raise typer.Exit(1)
        return final_context, final_results
    elif status == EditorStatus.ABORTED:
        renderer.display_warning("Retry cancelled.")
        raise typer.Exit(0)
    else:  # VALIDATION_ERROR or EDITOR_ERROR
        raise typer.Exit(1)


def _get_event_description_from_interpretation(
    selected_interpretation: "Interpretation",  # Use quotes for forward ref if needed
    interpretation_set: "InterpretationSet",  # Use quotes for forward ref if needed
    edit_flag: bool,
    console: Console,
    renderer: Renderer,
) -> str:
    """Generates default event description and optionally edits it.

    Args:
        selected_interpretation: The selected Interpretation object.
        interpretation_set: The InterpretationSet object containing the interpretation.
        edit_flag: Boolean indicating if --edit was passed.
        console: Rich console instance.
        renderer: Renderer instance.

    Returns:
        The final event description string.

    Raises:
        typer.Exit: If user cancels during edit or an editor error occurs.
    """
    # Use the already fetched interpretation set
    default_description = (
        f"Question: {interpretation_set.context}\n"
        f"Oracle: {interpretation_set.oracle_results}\n"
        f"Interpretation: {selected_interpretation.title} - {selected_interpretation.description}"
    )

    event_description = default_description
    if edit_flag or typer.confirm("Would you like to edit the event description?"):
        editor_config = EditorConfig(
            edit_message="Edit the event description:",
            success_message="Event description updated.",
            cancel_message="Event description unchanged.",
            error_message="Could not open editor",
        )
        structured_config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="description",
                    display_name="Event Description",
                    help_text="The detailed description of the event.",
                    required=True,
                    multiline=True,
                ),
            ]
        )
        event_data = {"description": default_description}
        edited_data, status = edit_structured_data(
            data=event_data,
            console=console,
            config=structured_config,
            context_info="Edit the event description below:\n",
            editor_config=editor_config,
            is_new=True,  # Treat as new input for description
        )

        if status in (
            EditorStatus.SAVED_MODIFIED,
            EditorStatus.SAVED_UNCHANGED,
        ):
            # Use edited data even if unchanged from default
            event_description = edited_data.get("description", default_description)
            if not event_description:
                renderer.display_error("Event description cannot be empty.")
                raise typer.Exit(1)
        elif status == EditorStatus.ABORTED:
            renderer.display_warning("Event creation cancelled during edit.")
            raise typer.Exit(0)
        else:  # VALIDATION_ERROR or EDITOR_ERROR
            raise typer.Exit(1)

    return event_description


# --- Typer Commands ---


@oracle_app.command("interpret")
def interpret_oracle(
    ctx: typer.Context,
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="Context or question for interpretation"
    ),
    results: Optional[str] = typer.Option(
        None, "--results", "-r", help="Oracle results to interpret"
    ),
    count: Optional[int] = typer.Option(  # Allow None initially
        None, "--count", "-n", help="Number of interpretations to generate"
    ),
    show_prompt: bool = typer.Option(
        False,
        "--show-prompt",
        help="Show the prompt that would be sent to the AI without sending it",
    ),
) -> None:
    """Get interpretations for oracle results.

    If context or results are not provided via options, an editor will be
    opened to prompt for them.

    Args:
        ctx: Typer context.
        context: Context or question for interpretation.
        results: Oracle results to interpret.
        count: Number of interpretations to generate.
        show_prompt: Show the prompt without sending it to the AI.
    """
    renderer: Renderer = ctx.obj["renderer"]
    console: Console = ctx.obj["console"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

            # Prompt for input via editor if needed
            if not show_prompt:  # Don't prompt if only showing prompt
                context, results = _prompt_for_oracle_input_if_needed(
                    context, results, console, renderer
                )
            elif context is None or results is None:
                # If showing prompt, context/results must be provided via options
                renderer.display_error(
                    "Cannot show prompt without providing both --context and --results."
                )
                raise typer.Exit(1)

            # Determine the number of interpretations
            if count is None:
                config = get_config()
                count_int = int(config.get("default_interpretations", 5))
            else:
                count_int = count  # Already an int if provided

            # Ensure context and results are available before proceeding
            if not context or not results:
                # This should theoretically be caught by the editor logic if it ran,
                # but provides an extra safeguard.
                renderer.display_error(
                    "Context and Results are required for interpretation."
                )
                raise typer.Exit(1)

            if show_prompt:
                prompt = oracle_manager.build_interpretation_prompt_for_active_context(
                    context,
                    results,
                    count_int,
                )
                renderer.display_message(
                    "\nPrompt that would be sent to AI:", style="bold blue"
                )
                renderer.display_message(prompt)
                return

            scene, act, game = oracle_manager.get_active_context()

            renderer.display_message(
                "\nGenerating interpretations...", style="bold blue"
            )
            interp_set = oracle_manager.get_interpretations(
                scene_id=scene.id,
                context=context,
                oracle_results=results,
                count=count_int,
            )

            renderer.display_interpretation_set(interp_set)
    except OracleError as e:
        logger.error(f"Failed to interpret oracle results: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@oracle_app.command("retry")
def retry_interpretation(
    ctx: typer.Context,
    count: Optional[int] = typer.Option(
        None, "--count", "-c", help="Number of interpretations to generate"
    ),
) -> None:
    """Request new interpretations, editing context and results first.

    Args:
        ctx: Typer context.
        count: Number of interpretations to generate.
    """
    renderer: Renderer = ctx.obj["renderer"]
    console: Console = ctx.obj["console"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)
            scene, act, game = oracle_manager.get_active_context()

            current_interp_set = oracle_manager.get_current_interpretation_set(scene.id)
            if not current_interp_set:
                renderer.display_error(
                    "No current interpretation to retry. Run 'oracle interpret' first."
                )
                raise typer.Exit(1)

            # Determine the number of interpretations
            if count is None:
                config = get_config()
                count_int = int(config.get("default_interpretations", 5))
            else:
                count_int = count  # Already an int if provided

            # Get the current context and results to pre-fill the editor
            initial_context = current_interp_set.context
            initial_results = current_interp_set.oracle_results

            # Edit context/results via editor
            final_context, final_results = _edit_oracle_input(
                initial_context, initial_results, console, renderer
            )

            renderer.display_message(
                "\nGenerating new interpretations...", style="bold blue"
            )
            new_interp_set = oracle_manager.get_interpretations(
                scene_id=scene.id,
                context=final_context,
                oracle_results=final_results,
                count=count_int,
                retry_attempt=current_interp_set.retry_attempt + 1,
                previous_set_id=current_interp_set.id,
            )

            renderer.display_interpretation_set(new_interp_set)
    except OracleError as e:
        logger.error(f"Failed to retry interpretation: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@oracle_app.command("list")
def list_interpretation_sets(
    ctx: typer.Context,
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

    Args:
        ctx: Typer context.
        act_id: ID of the act to list interpretations from.
        scene_id: ID of the scene to list interpretations from.
        limit: Maximum number of interpretation sets to show.
    """
    renderer: Renderer = ctx.obj["renderer"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

            # Determine target scope (scene or act)
            if not scene_id and not act_id:
                try:
                    active_scene, active_act, _ = oracle_manager.get_active_context()
                    scene_id = active_scene.id
                    act_id = active_act.id
                except OracleError as e:
                    renderer.display_error(f"Error determining active context: {e}")
                    renderer.display_warning(
                        "Please specify --scene-id or run this command within an "
                        "active game/act/scene."
                    )
                    raise typer.Exit(1) from e

            interp_sets = oracle_manager.list_interpretation_sets(
                scene_id=scene_id, act_id=act_id, limit=limit
            )

            if not interp_sets:
                if scene_id:
                    renderer.display_warning(
                        f"No interpretation sets found for scene ID: {scene_id}"
                    )
                else:
                    renderer.display_warning(
                        f"No interpretation sets found for act ID: {act_id}"
                    )
                raise typer.Exit(0)

            renderer.display_interpretation_sets_table(interp_sets)

    except OracleError as e:
        logger.error(f"Failed to list interpretation sets: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@oracle_app.command("show")
def show_interpretation_set(
    ctx: typer.Context,
    set_id: str = typer.Argument(..., help="ID of the interpretation set to show"),
) -> None:
    """Show details of a specific interpretation set.

    Args:
        ctx: Typer context.
        set_id: ID of the interpretation set to show.
    """
    renderer: Renderer = ctx.obj["renderer"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)

            interp_set = oracle_manager.get_interpretation_set(set_id)
            renderer.display_interpretation_set(interp_set, show_context=True)

    except OracleError as e:
        logger.error(f"Failed to show interpretation set: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@oracle_app.command("status")
def show_interpretation_status(ctx: typer.Context) -> None:
    """Show the currently active interpretation set for the current scene.

    Args:
        ctx: Typer context.
    """
    renderer: Renderer = ctx.obj["renderer"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)
            scene, act, game = oracle_manager.get_active_context()

            current_interp_set = oracle_manager.get_current_interpretation_set(scene.id)
            if not current_interp_set:
                renderer.display_warning(
                    "No current interpretation set for the active scene."
                )
                raise typer.Exit(0)

            renderer.display_interpretation_status(current_interp_set)
            renderer.display_interpretation_set(current_interp_set, show_context=False)

    except OracleError as e:
        logger.error(f"Failed to show interpretation status: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@oracle_app.command("select")
def select_interpretation(
    ctx: typer.Context,
    interpretation_identifier: str = typer.Argument(
        ...,
        help="Identifier of the interpretation to select (number, slug, or UUID).",
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

    Specify the interpretation using its sequence number (1, 2, 3...),
    slug (derived from the title), or the full UUID as a required argument.

    Args:
        ctx: Typer context.
        interpretation_identifier: Identifier (number, slug, UUID) of the
                                   interpretation to select.
        interpretation_set_id: ID of the interpretation set (uses current if None).
        edit: Edit the event description before adding.
    """
    renderer: Renderer = ctx.obj["renderer"]
    console: Console = ctx.obj["console"]

    try:
        with get_db_context() as session:
            oracle_manager = OracleManager(session=session)
            scene, act, game = oracle_manager.get_active_context()

            if not interpretation_set_id:
                current_interp_set = oracle_manager.get_current_interpretation_set(
                    scene.id
                )
                if not current_interp_set:
                    renderer.display_error(
                        "No current interpretation set. Specify --set-id or run "
                        "'oracle interpret' first."
                    )
                    raise typer.Exit(1)
                target_set_id = current_interp_set.id
                target_interp_set = current_interp_set  # Use already fetched set
            else:
                target_set_id = interpretation_set_id
                # Fetch the specified set if ID was provided
                target_interp_set = oracle_manager.get_interpretation_set(target_set_id)

            # No need to check if interpretation_identifier is None,
            # Typer handles required arguments.

            # Use the argument name here
            selected = oracle_manager.select_interpretation(
                target_set_id, interpretation_identifier
            )

            renderer.display_message("\nSelected interpretation:")
            renderer.display_interpretation(selected)

            if typer.confirm("\nAdd this interpretation as an event?"):
                # Get event description, potentially editing it
                event_description = _get_event_description_from_interpretation(
                    selected_interpretation=selected,
                    interpretation_set=target_interp_set,
                    edit_flag=edit,
                    console=console,
                    renderer=renderer,
                )

                # Add the event
                event = oracle_manager.add_interpretation_event(
                    selected, event_description
                )
                renderer.display_success("Interpretation added as event.")

                # Fetch the updated scene to potentially show the new event count etc.
                updated_scene = oracle_manager.scene_manager.get_scene(scene.id)
                if not updated_scene:
                    # Should not happen if context was valid, but handle defensively
                    renderer.display_warning(
                        "Could not retrieve updated scene details."
                    )
                    updated_scene = scene  # Fallback to original scene context

                events = [event]
                renderer.display_events_table(events, updated_scene)
            else:
                renderer.display_warning("Interpretation not added as event.")

    except OracleError as e:
        logger.error(f"Failed to select interpretation: {e}")
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
