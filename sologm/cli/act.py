"""CLI commands for managing acts.

This module provides commands for creating, listing, viewing, editing, and
completing acts within a game. Acts represent complete narrative situations
or problems that unfold through multiple connected Scenes.
"""

import logging
from typing import TYPE_CHECKING, Dict, Optional

import typer

# Console import removed, will get from ctx
from rich.prompt import Confirm  # Keep Confirm for interactive input

# Display function imports removed, will use renderer
from sologm.cli.utils.structured_editor import (  # Updated import
    EditorConfig,
    EditorStatus,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.core.act import ActManager
from sologm.core.game import GameManager
from sologm.models.act import Act
from sologm.models.game import Game
from sologm.utils.errors import APIError, GameError

if TYPE_CHECKING:
    from rich.console import Console

    from sologm.cli.rendering.base import Renderer


logger = logging.getLogger(__name__)

# Console instance removed, will get from ctx

act_app = typer.Typer(
    name="act",
    help="Manage acts in your games",
    no_args_is_help=True,
    rich_markup_mode="rich",  # Enable Rich markup in help text
)


@act_app.command("create")
def create_act(
    ctx: typer.Context,
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Title of the act (can be left empty for untitled acts)",
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-s", help="Summary of the act"
    ),
) -> None:
    """[bold]Create a new act in the current game.[/bold]

    If title and summary are not provided, opens an editor to enter them.
    Acts can be created without a title or summary, allowing you to name them
    later once their significance becomes clear.

    [yellow]Note:[/yellow] You must complete the current active act (if any)
    before creating a new one.

    Use `sologm act complete` to complete the current act first.

    [yellow]Examples:[/yellow]
        [green]Create an act with title and summary directly:[/green]
        $ sologm act create --title "The Journey Begins" \\
            --summary "The heroes set out on their quest"

        [green]Create an untitled act:[/green]
        $ sologm act create

        [green]Create an act with just a title:[/green]
        $ sologm act create -t "The Journey Begins"
    """
    logger.debug("Creating new act")
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    from sologm.database.session import get_db_context

    with get_db_context() as session:
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            renderer.display_error("No active game. Activate a game first.")
            raise typer.Exit(1)

        # If title and summary are not provided, open editor
        if title is None or summary is None:
            # Create editor configuration
            editor_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="title",
                        display_name="Title",
                        help_text=(
                            "Title of the act (can be left empty for untitled acts)"
                        ),
                        required=False,
                    ),
                    FieldConfig(
                        name="summary",
                        display_name="Summary",
                        help_text="Summary of the act",
                        multiline=True,
                        required=False,
                    ),
                ],
                wrap_width=70,
            )

            # Create context information
            context_info = (
                f"Creating a new act in game: {active_game.name}\n\n"
                "Acts represent complete narrative situations or problems that "
                "unfold through multiple connected Scenes.\n"
                "You can leave the title and summary empty if you're not sure "
                "what to call this act yet."
            )

            # Create initial data
            initial_data = {
                "title": title or "",
                "summary": summary or "",
            }

            # Open editor
            result_data, status = edit_structured_data(
                initial_data,  # Pass initial data (empty strings)
                console,
                editor_config,
                context_info=context_info,
                is_new=True,  # IMPORTANT: Indicate this is for a new item
                # No need for original_data_for_comments when is_new=True
            )

            # Check status: Proceed only if saved (modified or unchanged)
            if status not in (
                EditorStatus.SAVED_MODIFIED,
                EditorStatus.SAVED_UNCHANGED,
            ):
                # Abort, validation error, or editor error occurred. Message
                # already printed by edit_structured_data.
                logger.info(
                    f"Act creation cancelled due to editor status: {status.name}"
                )
                raise typer.Exit(0)  # Exit gracefully

            # If saved, result_data contains the (potentially empty) parsed data
            title = result_data.get("title") or None
            summary = result_data.get("summary") or None

        try:
            act = game_manager.act_manager.create_act(
                game_id=active_game.id,
                title=title,
                summary=summary,
            )

            # Display success message using renderer
            title_display = f"'{act.title}'" if act.title else "untitled"
            renderer.display_success(f"Act {title_display} created successfully!")

            # Display act details using renderer
            renderer.display_message(f"ID: {act.id}")
            renderer.display_message(f"Sequence: Act {act.sequence}")
            renderer.display_message(f"Active: {act.is_active}")
            if act.title:
                renderer.display_message(f"Title: {act.title}")
            if act.summary:
                renderer.display_message(f"Summary: {act.summary}")
            # TODO: Consider adding renderer.display_act_details(act) method

        except GameError as e:
            renderer.display_error(f"Error: {str(e)}")
            raise typer.Exit(1) from e


@act_app.command("list")
def list_acts(ctx: typer.Context) -> None:
    """[bold]List all acts in the current game.[/bold]

    Displays a table of all acts in the current game, including their
    sequence, title, description, status, and whether they are active.

    [yellow]Examples:[/yellow]
        $ sologm act list
    """
    logger.debug("Listing acts")
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    with get_db_context() as session:
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            renderer.display_error("No active game. Activate a game first.")
            raise typer.Exit(1)

        acts = game_manager.act_manager.list_acts(active_game.id)

        active_act = game_manager.act_manager.get_active_act(active_game.id)
        active_act_id = active_act.id if active_act else None

        # Display acts table using the renderer. The renderer's
        # display_acts_table should handle displaying the game header
        # internally if needed (RichRenderer does).
        renderer.display_acts_table(acts, active_act_id)


@act_app.command("info")
def act_info(ctx: typer.Context) -> None:
    """[bold]Show details of the current active act.[/bold]

    Displays detailed information about the currently active act, including its
    title, description, status, sequence, and any scenes it contains.

    [yellow]Examples:[/yellow]
        $ sologm act info
    """
    logger.debug("Showing act info")
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    with get_db_context() as session:
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            renderer.display_error("No active game. Activate a game first.")
            raise typer.Exit(1)

        # Get the active act
        active_act = game_manager.act_manager.get_active_act(active_game.id)
        if not active_act:
            renderer.display_error(f"No active act in game '{active_game.name}'.")
            renderer.display_message("Create one with `sologm act create`.")
            raise typer.Exit(1)

        # Display act info using the renderer. The renderer's display_act_info
        # should handle displaying the game header internally if needed
        # (RichRenderer does).
        renderer.display_act_info(active_act, active_game.name)


# --- Helper Function 1: Find Act by Identifier ---
def _find_act_by_identifier(
    act_manager: ActManager,
    identifier: str,
    renderer: "Renderer",
) -> Act:
    """Finds a specific act by its ID or slug, raising Exit on error."""
    logger.debug(f"Attempting to find act by identifier='{identifier}'")
    try:
        act = act_manager.get_act_by_identifier_or_error(identifier)
        logger.debug(f"Found act {act.id} using identifier '{identifier}'")
        return act
    except GameError as e:
        logger.error(
            f"GameError while finding act by identifier '{identifier}': {e}",
            exc_info=True,
        )
        renderer.display_error(f"Error finding act: {str(e)}")
        raise typer.Exit(1) from e


# --- Helper Function 2: Get Edit Data (Title/Summary) ---
def _get_edit_data(
    act_to_edit: Act,
    game_for_context: Game,
    cli_title: Optional[str],
    cli_summary: Optional[str],
    console: "Console",
    renderer: "Renderer",
) -> Optional[Dict[str, Optional[str]]]:
    """Gets the title and summary data, either from CLI args or editor.

    Returns a dictionary {'title': ..., 'summary': ...} if an update should
    proceed, otherwise returns None and handles user messages.
    """
    logger.debug("Determining edit data source (CLI vs Editor)")
    if cli_title is None and cli_summary is None:
        # Editor Path
        logger.debug("Using editor to get edit data.")
        editor_config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    help_text="Title of the act (can be left empty for untitled acts)",
                    required=False,
                ),
                FieldConfig(
                    name="summary",
                    display_name="Summary",
                    help_text="Summary of the act",
                    multiline=True,
                    required=False,
                ),
            ],
            wrap_width=70,
        )
        title_display = act_to_edit.title or "Untitled Act"
        context_info = (
            f"Editing Act {act_to_edit.sequence}: {title_display}\n"
            f"Game: {game_for_context.name}\n"
            f"ID: {act_to_edit.id}\n\n"
            "You can leave the title empty for an untitled act."
        )
        initial_data = {
            "title": act_to_edit.title or "",
            "summary": act_to_edit.summary or "",
        }

        result_data, status = edit_structured_data(
            initial_data,
            console,
            editor_config,
            context_info=context_info,
            is_new=False,
            original_data_for_comments=initial_data,
        )

        if status == EditorStatus.SAVED_MODIFIED:
            final_title = result_data.get("title") or None
            final_summary = result_data.get("summary") or None
            logger.info("Act data modified in editor. Proceeding with update.")
            return {"title": final_title, "summary": final_summary}
        elif status == EditorStatus.SAVED_UNCHANGED:
            logger.info("Editor saved, but no changes detected.")
            renderer.display_message("No changes detected. Act not updated.")
            return None  # Indicate no update needed
        else:  # Aborted or error
            # Message already displayed by edit_structured_data
            logger.info(
                f"Act edit cancelled or failed due to editor status: {status.name}"
            )
            return None  # Indicate cancellation/failure
    else:
        # CLI Args Path
        logger.debug("Using CLI arguments for edit data.")
        # Basic check: ensure at least one was provided if we took this path
        if cli_title is None and cli_summary is None:
            # This case should ideally not be reachable if options were defined correctly
            logger.warning("CLI path taken but both title and summary are None.")
            renderer.display_warning("No changes specified via command line options.")
            return None  # Indicate no update needed
        logger.info("Proceeding with update using CLI arguments.")
        return {"title": cli_title, "summary": cli_summary}


@act_app.command("edit")
def edit_act(
    ctx: typer.Context,
    identifier: Optional[str] = typer.Option(  # Renamed act_id to identifier
        None,
        "--id",
        help="ID or slug of the act to edit (defaults to active act)",  # Updated help text
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="New title for the act"
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-s", help="New summary for the act"
    ),
) -> None:
    """[bold]Edit an act using its ID/slug or the active act.[/bold]

    If an identifier (--id) is provided, edits that specific act regardless
    of active status. If no identifier is provided, edits the current active act
    within the active game.

    If title and summary are not provided via options, opens an editor.

    [yellow]Examples:[/yellow]
        [green]Edit active act with an interactive editor:[/green]
        $ sologm act edit

        [green]Edit a specific act (active or not) by ID or slug:[/green]
        $ sologm act edit --id abc123
        $ sologm act edit --id act-1-the-first-step

        [green]Update just the title of the active act:[/green]
        $ sologm act edit --title "New Title"

        [green]Update summary for a specific act:[/green]
        $ sologm act edit --id act-1-the-first-step -s "New summary"
    """
    logger.debug(f"Executing edit_act command (identifier='{identifier}')")
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]
    from sologm.database.session import get_db_context

    with get_db_context() as session:
        game_manager = GameManager(session=session)
        act_manager = ActManager(session=session)

        act_to_edit: Optional[Act] = None
        game_for_context: Optional[Game] = None

        if identifier:
            # --- Path 1: Identifier Provided ---
            logger.debug("Identifier provided, finding specific act.")
            # Helper handles errors and exits if act not found
            act_to_edit = _find_act_by_identifier(act_manager, identifier, renderer)
            try:
                # Fetch the game this act belongs to for context
                game_for_context = game_manager.get_game_by_id(act_to_edit.game_id)
                if not game_for_context:
                    # This should be unlikely if DB constraints are correct
                    logger.error(
                        f"Could not find game with ID {act_to_edit.game_id} "
                        f"associated with act {act_to_edit.id}"
                    )
                    renderer.display_error(
                        f"Internal error: Could not find game for act {act_to_edit.id}."
                    )
                    raise typer.Exit(1)
                logger.debug(
                    f"Found associated game for context: {game_for_context.name} "
                    f"({game_for_context.id})"
                )
            except GameError as e:
                logger.error(
                    f"Error fetching game {act_to_edit.game_id} for act "
                    f"{act_to_edit.id}: {e}",
                    exc_info=True,
                )
                renderer.display_error(
                    f"Internal error: Could not load game context for act: {str(e)}"
                )
                raise typer.Exit(1) from e

        else:
            # --- Path 2: No Identifier Provided ---
            logger.debug("No identifier provided, finding active game and act.")
            # Get active game (required for this path)
            active_game = game_manager.get_active_game()
            if not active_game:
                renderer.display_error(
                    "No active game. Activate a game first or specify an act --id."
                )
                raise typer.Exit(1)
            logger.debug(f"Active game: {active_game.name} ({active_game.id})")
            game_for_context = active_game  # Use active game for context

            # Get active act within the active game
            try:
                act_to_edit = act_manager.get_active_act(active_game.id)
                if not act_to_edit:
                    logger.warning(f"No active act found in game '{active_game.name}'.")
                    renderer.display_error(
                        f"No active act in game '{active_game.name}'."
                    )
                    renderer.display_message("Create one with `sologm act create`.")
                    raise typer.Exit(1)
                logger.debug(f"Found active act: {act_to_edit.id}")
            except GameError as e:
                # Catch error ONLY from get_active_act
                logger.error(f"GameError while finding active act: {e}", exc_info=True)
                renderer.display_error(f"Error finding active act: {str(e)}")
                raise typer.Exit(1) from e

        # --- Now we have act_to_edit and game_for_context ---
        # --- Step 3: Get Edit Data (uses helper) ---
        # Helper handles editor interaction, cancellation messages, and returns None if no update needed
        edit_data = _get_edit_data(
            act_to_edit, game_for_context, title, summary, console, renderer
        )

        # --- Step 4: Perform Update if data was obtained ---
        if edit_data is not None:
            logger.debug(
                f"Proceeding to update act {act_to_edit.id} with data: {edit_data}"
            )
            try:
                # Call the manager method within its own try block
                updated_act = act_manager.edit_act(  # Use act_manager directly
                    act_id=act_to_edit.id,
                    title=edit_data["title"],
                    summary=edit_data["summary"],
                )
                logger.info(f"Successfully updated act {updated_act.id}")

                # Display success message using renderer
                title_display = (
                    f"'{updated_act.title}'" if updated_act.title else "untitled"
                )
                renderer.display_success(f"Act {title_display} updated successfully!")

                # Display updated act details using renderer
                renderer.display_message(f"ID: {updated_act.id}")
                renderer.display_message(f"Sequence: Act {updated_act.sequence}")
                renderer.display_message(
                    f"Active: {updated_act.is_active}"
                )  # Display active status even if editing inactive
                if updated_act.title:
                    renderer.display_message(f"Title: {updated_act.title}")
                if updated_act.summary:
                    renderer.display_message(f"Summary: {updated_act.summary}")

            except (GameError, ValueError) as e:
                # Catch error ONLY from the edit_act manager call
                logger.error(f"Error during act update: {e}", exc_info=True)
                renderer.display_error(f"Error updating act: {str(e)}")
                raise typer.Exit(1) from e
        else:
            logger.debug(
                "No edit data returned, update skipped (cancelled or no changes)."
            )

    logger.debug("edit_act command finished.")


def _check_existing_content(act: Act, force: bool, renderer: "Renderer") -> bool:
    """Check if act has existing content and confirm replacement if needed.

    Args:
        act: The act to check.
        force: Whether to force replacement without confirmation.
        renderer: The renderer instance for displaying messages.

    Returns:
        True if should proceed, False if cancelled.
    """
    logger.debug(f"Checking existing content for act {act.id} (force={force})")
    if force:
        logger.debug("Force flag is True, skipping content check and confirmation.")
        return True

    has_title = act.title is not None and act.title.strip() != ""
    has_summary = act.summary is not None and act.summary.strip() != ""
    logger.debug(f"Act has_title={has_title}, has_summary={has_summary}")

    if not has_title and not has_summary:
        logger.debug("Act has no existing title or summary, proceeding.")
        return True

    if has_title and has_summary:
        confirm_message = "This will replace your existing title and summary."
    elif has_title:
        confirm_message = "This will replace your existing title."
    else:
        confirm_message = "This will replace your existing summary."

    logger.debug("Existing content found, asking for confirmation.")
    # Use Confirm directly for the prompt itself.
    # The message could potentially use renderer.display_warning if needed.
    confirmed = Confirm.ask(
        f"[yellow]{confirm_message} Continue?[/yellow]", default=False
    )
    logger.debug(f"User confirmation result: {confirmed}")
    return confirmed


def _collect_user_context(
    act: Act, game_name: str, console: "Console", renderer: "Renderer"
) -> Optional[str]:
    """Collect context from the user for AI generation.

    Opens a structured editor to allow the user to provide additional context
    for the AI summary generation. Displays relevant information about the
    act being completed.

    Args:
        act: The act being completed.
        game_name: Name of the game the act belongs to.
        console: The console instance for the editor.
        renderer: The renderer instance for displaying messages.

    Returns:
        The user-provided context, or None if the user cancels.
    """
    logger.debug(f"[_collect_user_context] Entering function for act {act.id}.")

    # Create editor configuration
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="context",
                display_name="Additional Context",
                help_text=(
                    "Provide any additional context or guidance for the AI "
                    "summary generation"
                ),
                multiline=True,
                required=False,
            ),
        ],
        wrap_width=70,
    )

    # Create context information header
    title_display = act.title or "Untitled Act"
    context_info = (
        f"AI Summary Generation for Act {act.sequence}: {title_display}\n"
        f"Game: {game_name}\n"
        f"ID: {act.id}\n\n"
        "Provide any additional context or guidance for the AI summary generation.\n"
        "For example:\n"
        "- Focus on specific themes or character developments\n"
        "- Highlight particular events or turning points\n"
        "- Suggest a narrative style or tone for the summary\n\n"
        "You can leave this empty to let the AI generate based only on the "
        "act's content."
    )

    # Create initial data
    initial_data = {
        "context": "",
    }

    logger.debug("Calling edit_structured_data for context collection")
    result_data, status = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
        is_new=True,  # Treat context collection as creating something new
    )
    logger.debug(
        f"[_collect_user_context] Editor returned status: {status.name}, "
        f"data: {result_data}"
    )

    # Check status: Proceed only if saved
    if status not in (EditorStatus.SAVED_MODIFIED, EditorStatus.SAVED_UNCHANGED):
        # Message already printed by edit_structured_data
        logger.debug(
            "[_collect_user_context] User cancelled context collection "
            f"(status: {status.name})"
        )
        return None

    user_context = result_data.get("context", "").strip()
    logger.debug(
        f"[_collect_user_context] Collected context (truncated): "
        f"'{user_context[:100]}{'...' if len(user_context) > 100 else ''}'"
    )
    return user_context if user_context else None


def _collect_regeneration_feedback(
    results: Dict[str, str],
    act: Act,
    game_name: str,
    console: "Console",
    renderer: "Renderer",
    original_context: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Collect feedback for regenerating AI content.

    Args:
        results: Dictionary containing previously generated title and summary.
        act: The act being completed.
        game_name: Name of the game the act belongs to.
        console: The console instance for the editor.
        renderer: The renderer instance for displaying messages.
        original_context: The original context provided for the first generation.

    Returns:
        Dictionary with feedback and context, or None if user cancels.
    """
    original_context_log = (
        f"'{original_context[:100]}{'...' if original_context and len(original_context) > 100 else ''}'"
        if original_context
        else "None"
    )
    logger.debug(
        f"[_collect_regeneration_feedback] Entering function for act {act.id}. "
        f"Original context (truncated): {original_context_log}"
    )

    # Create editor configuration
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="feedback",
                display_name="Regeneration Feedback",
                help_text=(
                    "Provide feedback on how you want the new generation to "
                    "differ (leave empty for a completely new attempt)"
                ),
                multiline=True,
                required=False,
            ),
            FieldConfig(
                name="context",
                display_name="Original Context",
                help_text=(
                    "Original context provided for generation. You can modify "
                    "this to include additional information."
                ),
                multiline=True,
                required=False,
            ),
        ],
        wrap_width=70,
    )

    # Create context information header
    title_display = act.title or "Untitled Act"
    context_info = (
        f"Regeneration Feedback for Act {act.sequence}: {title_display}\n"
        f"Game: {game_name}\n"
        f"ID: {act.id}\n\n"
        "Please provide feedback on how you want the new generation to differ "
        "from the previous one.\n"
        "You can leave this empty to get a completely new attempt.\n\n"
        "Be specific about what you liked and didn't like about the previous "
        "generation.\n\n"
        "Examples of effective feedback:\n"
        '- "Make the title more dramatic and focus on the conflict with the dragon"\n'
        '- "The summary is too focused on side characters. Center it on the '
        "protagonist's journey\"\n"
        '- "Change the tone to be more somber and reflective of the losses in '
        'this act"\n'
        '- "I like the theme of betrayal in the summary but want it to be more '
        'subtle"\n'
        '- "Keep the reference to the ancient ruins, but make the title more '
        'ominous"\n\n'
        "PREVIOUS GENERATION:\n"
        f"Title: {results.get('title', '')}\n"
        f"Summary: {results.get('summary', '')}\n\n"
    )

    if act.title or act.summary:
        context_info += "CURRENT ACT CONTENT:\n"
        if act.title:
            context_info += f"Title: {act.title}\n"
        if act.summary:
            context_info += f"Summary: {act.summary}\n"

    # Create initial data
    initial_data = {
        "feedback": "",
        "context": original_context or "",
    }
    logger.debug(
        "[_collect_regeneration_feedback] Initial data for feedback editor: "
        f"{initial_data}"
    )

    # Open editor - this is like creating new feedback, so is_new=True
    logger.debug("Calling edit_structured_data for regeneration feedback")
    result_data, status = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
        is_new=True,  # Treat feedback collection as creating something new
        editor_config=EditorConfig(
            edit_message="Edit your regeneration feedback below (or leave "
            "empty for a new attempt):",
            success_message="Feedback collected successfully.",
            cancel_message="Regeneration cancelled.",
            error_message="Could not open editor. Please try again.",
        ),
    )
    logger.debug(
        f"[_collect_regeneration_feedback] Editor returned status: {status.name}, "
        f"data: {result_data}"
    )

    # Check status: Proceed only if saved
    if status not in (EditorStatus.SAVED_MODIFIED, EditorStatus.SAVED_UNCHANGED):
        # Message already printed by edit_structured_data
        logger.debug(
            "[_collect_regeneration_feedback] User cancelled regeneration "
            f"feedback collection (status: {status.name})"
        )
        return None

    # Return the collected feedback and context
    feedback_dict = {
        "feedback": result_data.get("feedback", "").strip(),
        "context": result_data.get("context", "").strip(),  # Potentially modified
    }
    logger.debug(
        "[_collect_regeneration_feedback] Returning collected feedback data: "
        f"{feedback_dict}"
    )
    return feedback_dict


def _edit_ai_content(
    results: Dict[str, str],
    act: Act,
    game_name: str,
    console: "Console",
    renderer: "Renderer",
) -> Optional[Dict[str, str]]:
    """Allow user to edit AI-generated content.

    Args:
        results: Dictionary containing generated title and summary.
        act: The act being completed.
        game_name: Name of the game the act belongs to.
        console: The console instance for the editor.
        renderer: The renderer instance for displaying messages.

    Returns:
        Dictionary with edited title and summary, or None if user cancels.
    """
    logger.debug(f"Opening editor for AI content for act {act.id}")

    # Create editor configuration
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="title",
                display_name="Title",
                help_text="Edit the AI-generated title (1-7 words recommended)",
                required=True,
            ),
            FieldConfig(
                name="summary",
                display_name="Summary",
                help_text="Edit the AI-generated summary (3-5 paragraphs recommended)",
                multiline=True,
                required=True,
            ),
        ],
        wrap_width=70,
    )

    # Create context information
    title_display = act.title or "Untitled Act"
    context_info = (
        f"Editing AI-Generated Content for Act {act.sequence}: {title_display}\n"
        f"Game: {game_name}\n"
        f"ID: {act.id}\n\n"
        "Edit the AI-generated title and summary below.\n"
        "- The title should capture the essence or theme of the act (1-7 words)\n"
        "- The summary should highlight key events and narrative arcs "
        "(3-5 paragraphs)\n"
    )

    # Add original content as comments if it exists
    original_data = {}
    if act.title:
        original_data["title"] = act.title
    if act.summary:
        original_data["summary"] = act.summary
    logger.debug(f"Original act content for comments: {original_data}")

    # Open editor
    logger.debug("Calling edit_structured_data for AI content edit")
    edited_results, status = edit_structured_data(
        results,  # Pass the AI results as the data to edit
        console,
        editor_config,
        context_info=context_info,
        # Pass the original act content (if any) to show as comments
        original_data_for_comments=original_data if original_data else None,
        is_new=False,  # This is an edit of the AI content
        editor_config=EditorConfig(
            edit_message="Edit the AI-generated content below:",
            success_message="AI-generated content updated successfully.",
            cancel_message="Edit cancelled or no changes made.",  # Updated message
            error_message="Could not open editor. Please try again.",
        ),
    )
    logger.debug(f"Editor returned status: {status.name}, data: {edited_results}")

    # Check status: Only proceed if saved (modified or unchanged)
    if status not in (EditorStatus.SAVED_MODIFIED, EditorStatus.SAVED_UNCHANGED):
        # Message already printed by edit_structured_data
        logger.debug(f"User cancelled editing AI content (status: {status.name})")
        return None

    # Validate the edited content (result is stored in edited_results)
    # Perform validation even if SAVED_UNCHANGED, although it should pass if
    # the original AI content was valid.
    title = edited_results.get("title", "").strip()
    summary = edited_results.get("summary", "").strip()
    logger.debug(f"Validating edited title='{title}', summary='{summary}'")

    if not title:
        logger.warning("Validation failed: Edited title is empty.")
        renderer.display_error("Title cannot be empty after edit.")
        # Maybe re-prompt or return None? Returning None for now.
        return None

    if not summary:
        logger.warning("Validation failed: Edited summary is empty.")
        renderer.display_error("Summary cannot be empty after edit.")
        # Maybe re-prompt or return None? Returning None for now.
        return None

    # Show a preview of the edited content using the renderer
    logger.debug("Displaying edited content preview")
    renderer.display_act_edited_content_preview(edited_results)

    # Ask for confirmation
    logger.debug("Asking user to confirm edited content")
    confirmed = Confirm.ask(
        "[yellow]Use this edited content?[/yellow]",
        default=True,
    )
    logger.debug(f"User confirmation result: {confirmed}")

    if confirmed:
        logger.debug("User confirmed edited content, returning results.")
        return edited_results
    else:
        logger.debug("User rejected edited content, returning None.")
        return None


def _handle_user_feedback_loop(
    results: Dict[str, str],
    act: Act,
    game_name: str,
    act_manager: ActManager,
    console: "Console",
    renderer: "Renderer",
    original_context: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Handle the accept/edit/regenerate feedback loop.

    Args:
        results: Dictionary containing generated title and summary.
        act: The act being completed.
        game_name: Name of the game the act belongs to.
        act_manager: ActManager instance for business logic.
        console: The console instance for editors/prompts.
        renderer: The renderer instance for displaying messages.
        original_context: The original context provided for the first generation.

    Returns:
        Final dictionary with title and summary, or None if user cancels.
    """
    original_context_log = (
        f"'{original_context[:100]}{'...' if original_context and len(original_context) > 100 else ''}'"
        if original_context
        else "None"
    )
    logger.debug(
        f"[_handle_user_feedback_loop] Entering feedback loop for act {act.id}. "
        f"Initial original_context (truncated): {original_context_log}"
    )
    current_results = results.copy()  # Work with a copy

    while True:
        # Get user choice using the renderer
        logger.debug("Calling renderer.display_act_ai_feedback_prompt")
        choice = renderer.display_act_ai_feedback_prompt(console=console)

        logger.debug(f"User chose: {choice}")

        # Handle potential None choice if prompt is cancelled in renderer
        if choice is None:  # Handle potential cancellation from prompt
            logger.debug(
                "[_handle_user_feedback_loop] User cancelled feedback prompt, "
                "exiting loop."
            )
            return None

        if choice == "A":  # Accept
            logger.debug(
                "[_handle_user_feedback_loop] User accepted the generated content, "
                "exiting loop."
            )
            return current_results

        elif choice == "E":  # Edit
            logger.debug("User chose to edit the generated content.")
            logger.debug("Calling _edit_ai_content")
            edited_results = _edit_ai_content(
                current_results, act, game_name, console, renderer
            )

            if edited_results:
                logger.debug("Edit successful and confirmed, returning edited results.")
                return edited_results

            # If editing was cancelled, return to the prompt
            logger.debug("Edit was cancelled or rejected, returning to prompt.")
            renderer.display_warning("Edit cancelled. Returning to prompt.")
            continue

        elif choice == "R":  # Regenerate
            logger.debug(
                "[_handle_user_feedback_loop] User chose to regenerate content"
            )

            # Collect regeneration feedback
            logger.debug(
                "[_handle_user_feedback_loop] Calling _collect_regeneration_feedback"
            )
            original_context_log_for_collector = (
                f"'{original_context[:100]}{'...' if original_context and len(original_context) > 100 else ''}'"
                if original_context
                else "None"
            )
            logger.debug(
                "[_handle_user_feedback_loop] Passing original_context to feedback "
                f"collector (truncated): {original_context_log_for_collector}"
            )
            feedback_data = _collect_regeneration_feedback(
                current_results,
                act,
                game_name,
                console,
                renderer,
                original_context,  # Pass original context
            )

            if not feedback_data:
                logger.debug(
                    "[_handle_user_feedback_loop] Regeneration feedback cancelled, returning to prompt."
                )
                renderer.display_warning("Regeneration cancelled. Returning to prompt.")
                continue

            try:
                renderer.display_message(
                    "Regenerating summary with AI...", style="yellow"
                )

                # Always use the context returned from the feedback editor,
                # even if feedback itself is empty. This context will either be
                # the original context (if unchanged in the editor) or modified.
                regeneration_context = feedback_data.get("context")
                regeneration_feedback = feedback_data.get("feedback")
                context_log = (
                    f"'{regeneration_context[:100]}{'...' if regeneration_context and len(regeneration_context) > 100 else ''}'"
                    if regeneration_context
                    else "None"
                )
                logger.debug(
                    "[_handle_user_feedback_loop] Regeneration context from feedback "
                    f"editor (truncated): {context_log}"
                )
                logger.debug(
                    "[_handle_user_feedback_loop] Regeneration feedback: "
                    f"'{regeneration_feedback}'"
                )

                if regeneration_feedback:
                    logger.debug(
                        "[_handle_user_feedback_loop] Calling "
                        "generate_act_summary_with_feedback with feedback and context."
                    )
                    new_results = act_manager.generate_act_summary_with_feedback(
                        act.id,
                        feedback=regeneration_feedback,
                        previous_generation=current_results,
                        context=regeneration_context,  # Pass potentially updated context
                    )
                else:
                    # If no feedback, generate again but *still use the context*
                    # from the feedback editor (which might be the original or
                    # modified). This prevents losing the original context if
                    # only regeneration is requested.
                    logger.debug(
                        "[_handle_user_feedback_loop] Calling generate_act_summary "
                        "with potentially updated context (no new feedback)."
                    )
                    # Call base generation, passing context from feedback_data
                    new_results = act_manager.generate_act_summary(
                        act.id, additional_context=regeneration_context
                    )
                logger.info(
                    "[_handle_user_feedback_loop] AI regeneration successful for act "
                    f"{act.id}"
                )

                # Display the new results using the renderer
                logger.debug(
                    "[_handle_user_feedback_loop] Calling renderer.display_act_ai_generation_results"
                )
                renderer.display_act_ai_generation_results(new_results, act)

                # Continue the loop with the new results
                current_results = new_results
                continue  # Continue loop with new results

            except APIError as e:
                logger.error(f"APIError during regeneration: {e}", exc_info=True)
                renderer.display_error(f"AI Error: {str(e)}")
                renderer.display_warning("Returning to previous content.")
                continue  # Go back to prompt with old results


def _handle_ai_completion(
    act_manager: ActManager,
    active_act: Act,
    active_game: Game,
    console: "Console",
    renderer: "Renderer",
    context: Optional[str],  # Context from CLI --context option
    force: bool,
) -> Optional[Act]:
    """Handles the AI-driven act completion flow.

    Args:
        act_manager: Instance of ActManager.
        active_act: The act being completed.
        active_game: The game the act belongs to.
        console: Rich console instance for editor/prompts.
        renderer: Renderer instance for display.
        context: Optional context provided via CLI.
        force: Whether to force completion.

    Returns:
        The completed Act object on success, or None if the process is
        cancelled or fails.
    """
    context_log = (
        f"'{context[:100]}{'...' if context and len(context) > 100 else ''}'"
        if context
        else "None"
    )
    logger.debug(
        f"[_handle_ai_completion] Entering function for act {active_act.id}. "
        f"CLI context (truncated): {context_log}, force: {force}"
    )

    # 1. Check existing content - do not regenerate if force is not true and
    # content already exists in title/summary
    logger.debug("Checking existing content before AI generation")
    should_proceed = _check_existing_content(active_act, force, renderer)
    if not should_proceed:
        logger.warning("AI completion cancelled by user during existing content check.")
        renderer.display_warning("Operation cancelled.")
        return None
    logger.debug("Existing content check passed or forced.")

    # 2. Collect context if needed
    # Keep track of the initial CLI context for regeneration feedback
    original_context = context
    original_context_log = (
        f"'{original_context[:100]}{'...' if original_context and len(original_context) > 100 else ''}'"
        if original_context
        else "None"
    )
    logger.debug(
        f"[_handle_ai_completion] Stored original_context (truncated): "
        f"{original_context_log}"
    )
    if not context:
        logger.debug(
            "[_handle_ai_completion] No context provided via CLI, attempting to "
            "collect from user."
        )
        logger.debug("[_handle_ai_completion] Calling _collect_user_context")
        context = _collect_user_context(active_act, active_game.name, console, renderer)
        context_log_after = (
            f"'{context[:100]}{'...' if context and len(context) > 100 else ''}'"
            if context
            else "None"
        )
        logger.debug(
            "[_handle_ai_completion] Context after user collection (truncated): "
            f"{context_log_after}"
        )
        if context is None:
            # Message already displayed by _collect_user_context or editor
            logger.warning(
                "[_handle_ai_completion] AI completion cancelled during user "
                "context collection."
            )
            return None
        logger.debug("[_handle_ai_completion] User context collected successfully.")
        # User might cancel context collection, context will be None which
        # is handled by generate_act_summary. Update original_context.
        original_context = context

    try:
        # 3. Generate initial summary
        context_log_before_ai = (
            f"'{context[:100]}{'...' if context and len(context) > 100 else ''}'"
            if context
            else "None"
        )
        logger.debug(
            f"[_handle_ai_completion] Calling act_manager.generate_act_summary "
            f"for act {active_act.id} with context (truncated)="
            f"{context_log_before_ai}"
        )
        renderer.display_message("Generating summary with AI...", style="yellow")
        summary_data = act_manager.generate_act_summary(active_act.id, context)
        logger.info(
            "[_handle_ai_completion] Initial AI summary generated for act "
            f"{active_act.id}"
        )

        # 4. Display results using renderer
        logger.debug("Displaying initial AI generation results")
        renderer.display_act_ai_generation_results(summary_data, active_act)

        # 5. Handle user feedback loop
        logger.debug("[_handle_ai_completion] Entering user feedback loop")
        original_context_log_before_loop = (
            f"'{original_context[:100]}{'...' if original_context and len(original_context) > 100 else ''}'"
            if original_context
            else "None"
        )
        logger.debug(
            "[_handle_ai_completion] Passing original_context to feedback loop "
            f"(truncated): {original_context_log_before_loop}"
        )
        final_data = _handle_user_feedback_loop(
            summary_data,
            active_act,
            active_game.name,
            act_manager,
            console,
            renderer,
            original_context,  # Pass original context for regeneration feedback
        )

        if final_data is None:
            logger.warning(
                "[_handle_ai_completion] AI completion cancelled during feedback loop."
            )
            renderer.display_warning("Operation cancelled during feedback.")
            return None  # User cancelled the loop
        logger.debug(
            "[_handle_ai_completion] Feedback loop completed successfully. "
            f"Final data: {final_data}"
        )

        # 6. Complete the act with final AI data
        logger.debug(
            f"Calling act_manager.complete_act_with_ai for act {active_act.id} "
            f"with title='{final_data.get('title')}', "
            f"summary='{final_data.get('summary')}'"
        )
        completed_act = act_manager.complete_act_with_ai(
            active_act.id,
            final_data.get("title"),
            final_data.get("summary"),
        )
        logger.info(f"Act {active_act.id} completed successfully using AI data.")
        return completed_act  # Success

    except APIError as e:
        logger.error(f"APIError during AI completion: {e}", exc_info=True)
        renderer.display_error(f"AI Error: {str(e)}")
        renderer.display_warning("Falling back to manual entry might be needed.")
        return None  # Indicate AI failure
    except Exception as e:
        logger.error(f"Unexpected error during AI completion: {e}", exc_info=True)
        renderer.display_error(f"Error during AI processing: {str(e)}")
        return None  # Indicate general failure


def _handle_manual_completion(
    act_manager: ActManager,
    active_act: Act,
    active_game: Game,
    console: "Console",
    renderer: "Renderer",
) -> Optional[Act]:
    """Handles the manual act completion flow using the editor.

    Args:
        act_manager: Instance of ActManager.
        active_act: The act being completed.
        active_game: The game the act belongs to.
        console: Rich console instance for editor.
        renderer: Renderer instance for display.

    Returns:
        The completed Act object on success, or None if the editor is cancelled.
    """
    logger.debug(
        f"[_handle_manual_completion] Entering function for act {active_act.id}."
    )

    # 1. Setup editor config
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="title",
                display_name="Title",
                help_text="Title of the completed act",
                required=False,
            ),
            FieldConfig(
                name="summary",
                display_name="Summary",
                help_text="Summary of the completed act",
                multiline=True,
                required=False,
            ),
        ],
        wrap_width=70,
    )

    # 2. Build context info
    title_display = active_act.title or "Untitled Act"
    context_info = (
        f"Completing Act {active_act.sequence}: {title_display}\n"
        f"Game: {active_game.name}\n"
        f"ID: {active_act.id}\n\n"
        "You can provide a title and description to summarize this act's events."
    )

    # 3. Prepare initial data
    initial_data = {
        "title": active_act.title or "",
        "summary": active_act.summary or "",
    }
    logger.debug(f"Initial data for manual completion editor: {initial_data}")

    # 4. Call editor
    logger.debug("Calling edit_structured_data for manual completion")
    result_data, status = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
        is_new=False,  # Explicitly set is_new=False for clarity
        original_data_for_comments=initial_data,  # Show original as comments
    )
    logger.debug(f"Editor returned status: {status.name}, data: {result_data}")

    # 5. Handle cancellation based on status
    if status not in (EditorStatus.SAVED_MODIFIED, EditorStatus.SAVED_UNCHANGED):
        # Abort, validation error, or editor error occurred. Message already
        # printed by edit_structured_data.
        logger.debug(f"Completion cancelled due to editor status: {status.name}")
        return None  # Signal cancellation to the main complete_act function

    # If we reach here, the user saved successfully (with or without changes).
    logger.debug("Editor saved successfully (modified or unchanged).")

    # 6. Extract results (always use the data returned by the editor)
    title = result_data.get("title") or None
    summary = result_data.get("summary") or None
    logger.debug(f"Extracted title='{title}', summary='{summary}' from editor")

    # 7. Complete the act (outer function handles GameError)
    logger.debug(
        f"Calling act_manager.complete_act for act {active_act.id} "
        f"with title='{title}', summary='{summary}'"
    )
    completed_act = act_manager.complete_act(
        act_id=active_act.id, title=title, summary=summary
    )
    logger.info(f"Act {active_act.id} completed successfully using manual data.")

    # 8. Return completed act
    return completed_act


@act_app.command("complete")
def complete_act(
    ctx: typer.Context,
    ai: bool = typer.Option(False, "--ai", help="Use AI to generate title and summary"),
    context: Optional[str] = typer.Option(  # This is the CLI --context option
        None,
        "--context",
        "-c",
        help="Additional context to include in the AI summary generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=(
            "Force AI generation even if title/summary already exist "
            "(overwrites existing)"
        ),
    ),
) -> None:
    """[bold]Complete the current active act.[/bold]

    Completing an act marks it as finished. This command will either use AI
    (if `--ai` is specified) to generate a title and summary, or it will open
    a structured editor for you to provide them manually based on the act's
    events.

    The `--ai` flag generates a title and summary using AI based on the act's
    content. You can provide additional guidance with `--context`. Use `--force`
    with `--ai` to proceed even if the act already has a title or summary
    (they will be replaced by the AI generation).

    [yellow]Examples:[/yellow]
        [green]Complete act using the interactive editor:[/green]
        $ sologm act complete

        [green]Complete act with AI-generated title and summary:[/green]
        $ sologm act complete --ai

        [green]Complete act with AI-generated content and additional context:[/green]
        $ sologm act complete --ai \\
          --context "Focus on the themes of betrayal and redemption"

        [green]Force AI regeneration, overwriting existing title/summary:[/green]
        $ sologm act complete --ai --force
    """
    context_log_str = (
        f"'{context[:100]}{'...' if context and len(context) > 100 else ''}'"
        if context
        else "None"
    )
    logger.debug(
        f"[complete_act] Entering command: ai={ai}, "
        f"CLI context (truncated)={context_log_str}, force={force}"
    )
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor/prompts
    # Main command flow
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    logger.debug("[complete_act] Entering database session context")
    with get_db_context() as session:
        # Initialize managers with the session
        game_manager = GameManager(session=session)
        act_manager = ActManager(session=session)

        try:
            # Validate active game and act
            logger.debug("Validating active game")
            active_game = game_manager.get_active_game()
            if not active_game:
                logger.error("No active game found during act completion.")
                renderer.display_error("No active game. Activate a game first.")
                raise typer.Exit(1)
            logger.debug(f"Active game found: {active_game.id}")

            logger.debug("Validating active act")
            active_act = act_manager.get_active_act(active_game.id)
            if not active_act:
                logger.warning(f"No active act found in game '{active_game.name}'.")
                renderer.display_error(f"No active act in game '{active_game.name}'.")
                renderer.display_message("Create one with `sologm act create`.")
                raise typer.Exit(1)
            logger.debug(f"Active act found: {active_act.id}")

            completed_act: Optional[Act] = None
            if ai:
                logger.debug("[complete_act] AI completion path chosen.")
                logger.debug("[complete_act] Calling _handle_ai_completion")
                completed_act = _handle_ai_completion(
                    act_manager,
                    active_act,
                    active_game,
                    console,
                    renderer,
                    context,  # Pass the CLI context
                    force,
                )
                logger.debug(
                    f"[complete_act] _handle_ai_completion returned: {completed_act}"
                )
                # If AI fails or is cancelled, completed_act will be None
            else:
                logger.debug("[complete_act] Manual completion path chosen.")
                logger.debug("[complete_act] Calling _handle_manual_completion")
                completed_act = _handle_manual_completion(
                    act_manager, active_act, active_game, console, renderer
                )
                logger.debug(
                    "[complete_act] _handle_manual_completion returned: "
                    f"{completed_act}"
                )
                # If manual edit is cancelled, completed_act will be None

            # Display success only if completion happened successfully
            if completed_act:
                logger.info(f"Act {completed_act.id} completion process successful.")
                logger.debug("Calling renderer.display_act_completion_success")
                renderer.display_act_completion_success(completed_act)
            else:
                logger.warning(
                    f"Act {active_act.id} completion did not finish successfully "
                    "or was cancelled."
                )
                # Optionally add a message: renderer.display_warning(...)

        except GameError as e:
            # Catch errors from validation or manual/AI completion helpers
            logger.error(f"GameError during act completion: {e}", exc_info=True)
            renderer.display_error(f"Error: {str(e)}")
            raise typer.Exit(1) from e
    logger.debug("[complete_act] Exiting command")
