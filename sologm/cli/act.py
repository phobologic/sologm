"""CLI commands for managing acts.

This module provides commands for creating, listing, viewing, editing, and
completing acts within a game. Acts represent complete narrative situations
or problems that unfold through multiple connected Scenes.
"""

import logging
from typing import Dict, Optional

import typer
from rich.console import Console

from sologm.cli.utils.display import (
    display_act_info,
    display_acts_table,
    display_act_completion_success,
    display_act_ai_generation_results,
)
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.core.act import ActManager
from sologm.core.game import GameManager
from sologm.models.act import Act
from sologm.utils.errors import APIError, GameError

logger = logging.getLogger(__name__)

# Create console for rich output
console = Console()

# Create Typer app for act commands
act_app = typer.Typer(
    name="act",
    help="Manage acts in your games",
    no_args_is_help=True,
    rich_markup_mode="rich",  # Enable Rich markup in help text
)


@act_app.command("create")
def create_act(
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

    [yellow]Note:[/yellow] You must complete the current active act (if any) before creating a new one.
    Use [cyan]'sologm act complete'[/cyan] to complete the current act first.

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

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # ActManager will validate if we can create a new act

    # If title and summary are not provided, open editor
    if title is None or summary is None:
        # Create editor configuration
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

        # Create context information
        context_info = f"Creating a new act in game: {active_game.name}\n\n"
        context_info += (
            "Acts represent complete narrative situations or "
            "problems that unfold through multiple connected "
            "Scenes.\n"
        )
        context_info += (
            "You can leave the title and summary empty if "
            "you're not sure what to call this act yet."
        )

        # Create initial data
        initial_data = {
            "title": title or "",
            "summary": summary or "",
        }

        # Open editor
        result, modified = edit_structured_data(
            initial_data,
            console,
            editor_config,
            context_info=context_info,
            is_new=True,
        )

        if not modified:
            console.print("[yellow]Act creation canceled.[/yellow]")
            raise typer.Exit(0)

        title = result.get("title") or None
        summary = result.get("summary") or None

    # Create the act
    try:
        act = game_manager.act_manager.create_act(
            game_id=active_game.id,
            title=title,
            summary=summary,
        )

        # Display success message
        title_display = f"'{act.title}'" if act.title else "untitled"
        console.print(
            f"[bold green]Act {title_display} created successfully![/bold green]"
        )

        # Display act details
        console.print(f"ID: {act.id}")
        console.print(f"Sequence: Act {act.sequence}")
        console.print(f"Active: {act.is_active}")
        if act.title:
            console.print(f"Title: {act.title}")
        if act.summary:
            console.print(f"Summary: {act.summary}")

    except GameError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@act_app.command("list")
def list_acts() -> None:
    """[bold]List all acts in the current game.[/bold]

    Displays a table of all acts in the current game, including their sequence,
    title, description, status, and whether they are active.

    [yellow]Examples:[/yellow]
        $ sologm act list
    """
    logger.debug("Listing acts")

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            console.print("[red]Error:[/] No active game. Activate a game first.")
            raise typer.Exit(1) from e

        # Get all acts for the game
        acts = game_manager.act_manager.list_acts(active_game.id)

        # Get active act ID
        active_act = game_manager.act_manager.get_active_act(active_game.id)
        active_act_id = active_act.id if active_act else None

        # Display compact game header instead of full game info
        from sologm.cli.utils.display import _create_game_header_panel

        console.print(_create_game_header_panel(active_game, console))
        console.print()

        # Display acts table
        display_acts_table(console, acts, active_act_id)


@act_app.command("info")
def act_info() -> None:
    """[bold]Show details of the current active act.[/bold]

    Displays detailed information about the currently active act, including
    its title, description, status, sequence, and any scenes it contains.

    [yellow]Examples:[/yellow]
        $ sologm act info
    """
    logger.debug("Showing act info")

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            console.print("[red]Error:[/] No active game. Activate a game first.")
            raise typer.Exit(1)

        # Get the active act
        active_act = game_manager.act_manager.get_active_act(active_game.id)
        if not active_act:
            console.print(f"[red]Error:[/] No active act in game '{active_game.name}'.")
            console.print("Create one with 'sologm act create'.")
            raise typer.Exit(1)

        # Display compact game header first
        from sologm.cli.utils.display import _create_game_header_panel

        console.print(_create_game_header_panel(active_game, console))

        # Display act info
        display_act_info(console, active_act, active_game.name)


@act_app.command("edit")
def edit_act(
    act_id: Optional[str] = typer.Option(
        None, "--id", help="ID of the act to edit (defaults to active act)"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="New title for the act"
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-s", help="New summary for the act"
    ),
) -> None:
    """[bold]Edit an act in the current game.[/bold]

    If no act ID is provided, edits the current active act.
    If title and summary are not provided, opens an editor to enter them.
    You can update the title and/or summary of the act, or remove them
    by leaving the fields empty.

    [yellow]Examples:[/yellow]
        [green]Edit active act with an interactive editor:[/green]
        $ sologm act edit

        [green]Edit a specific act by ID:[/green]
        $ sologm act edit --id abc123

        [green]Update just the title:[/green]
        $ sologm act edit --title "New Title"

        [green]Update both title and summary for a specific act:[/green]
        $ sologm act edit --id abc123 -t "New Title" -s "New summary of the act"
    """
    logger.debug("Editing act")

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            console.print("[red]Error:[/] No active game. Activate a game first.")
            raise typer.Exit(1)

        # Get the act to edit
        act_manager = ActManager(session=session)

        if act_id:
            # Get the specified act
            act_to_edit = act_manager.get_act(act_id)
            if not act_to_edit:
                console.print(f"[red]Error:[/] Act with ID '{act_id}' not found.")
                raise typer.Exit(1)

            # Verify the act belongs to the active game
            if act_to_edit.game_id != active_game.id:
                console.print(
                    f"[red]Error:[/] Act with ID '{act_id}' does not belong to the active game."
                )
                raise typer.Exit(1)
        else:
            # Get the active act
            act_to_edit = act_manager.get_active_act(active_game.id)
            if not act_to_edit:
                console.print(
                    f"[red]Error:[/] No active act in game '{active_game.name}'."
                )
                console.print("Create one with 'sologm act create'.")
                raise typer.Exit(1)

        # If title and summary are not provided, open editor
        if title is None and summary is None:
            # Create editor configuration
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

            # Create context information
            title_display = act_to_edit.title or "Untitled Act"
            context_info = f"Editing Act {act_to_edit.sequence}: {title_display}\n"
            context_info += f"Game: {active_game.name}\n"
            context_info += f"ID: {act_to_edit.id}\n\n"
            context_info += "You can leave the title empty for an untitled act."

            # Create initial data
            initial_data = {
                "title": act_to_edit.title or "",
                "summary": act_to_edit.summary or "",
            }

            # Open editor
            result, modified = edit_structured_data(
                initial_data,
                console,
                editor_config,
                context_info=context_info,
            )

            if not modified:
                console.print("[yellow]Act edit canceled.[/yellow]")
                raise typer.Exit(0)

            # If parameters were provided directly, use them
            # Otherwise, use the results from the editor
            final_title = title if title is not None else result.get("title") or None
            final_summary = (
                summary if summary is not None else result.get("summary") or None
            )

        else:
            # If parameters were provided directly, use them
            final_title = title
            final_summary = summary

        # Update the act
        try:
            updated_act = game_manager.act_manager.edit_act(
                act_id=act_to_edit.id,
                title=final_title,
                summary=final_summary,
            )

            # Display success message
            title_display = (
                f"'{updated_act.title}'" if updated_act.title else "untitled"
            )
            console.print(
                f"[bold green]Act {title_display} updated successfully![/bold green]"
            )

            # Display updated act details
            console.print(f"ID: {updated_act.id}")
            console.print(f"Sequence: Act {updated_act.sequence}")
            console.print(f"Active: {updated_act.is_active}")
            if updated_act.title:
                console.print(f"Title: {updated_act.title}")
            if updated_act.summary:
                console.print(f"Summary: {updated_act.summary}")

        except GameError as e:
            console.print(f"[red]Error:[/] {str(e)}")
            raise typer.Exit(1) from e


# --- Helper Functions for complete_act ---

def _check_existing_content(act: Act, force: bool) -> bool:
    """Check if act has existing content and confirm replacement if needed.

    Args:
        act: The act to check
        force: Whether to force replacement without confirmation

    Returns:
        True if should proceed, False if cancelled
    """
    if force:
        return True

    has_title = act.title is not None and act.title.strip() != ""
    has_summary = act.summary is not None and act.summary.strip() != ""

    if not has_title and not has_summary:
        return True

    if has_title and has_summary:
        confirm_message = "This will replace your existing title and summary."
    elif has_title:
        confirm_message = "This will replace your existing title."
    else:
        confirm_message = "This will replace your existing summary."

    from rich.prompt import Confirm

    return Confirm.ask(
        f"[yellow]{confirm_message} Continue?[/yellow]", default=False
    )


def _collect_user_context(act: Act, game_name: str) -> Optional[str]:
    """Collect context from the user for AI generation.

    Opens a structured editor to allow the user to provide additional context
    for the AI summary generation. Displays relevant information about the
    act being completed.

    Args:
        act: The act being completed
        game_name: Name of the game the act belongs to

    Returns:
        The user-provided context, or None if the user cancels
    """
    logger.debug("Collecting context for AI generation")

    # Create editor configuration
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="context",
                display_name="Additional Context",
                help_text="Provide any additional context or guidance for the AI summary generation",
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
    )
    context_info += f"Game: {game_name}\n"
    context_info += f"ID: {act.id}\n\n"
    context_info += (
        "Provide any additional context or guidance for the AI summary "
        "generation.\n"
    )
    context_info += "For example:\n"
    context_info += "- Focus on specific themes or character developments\n"
    context_info += "- Highlight particular events or turning points\n"
    context_info += "- Suggest a narrative style or tone for the summary\n\n"
    context_info += (
        "You can leave this empty to let the AI generate based only on "
        "the act's content."
    )

    # Create initial data
    initial_data = {
        "context": "",
    }

    # Open editor
    result, modified = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
    )

    if not modified:
        logger.debug("User cancelled context collection")
        return None

    user_context = result.get("context", "").strip()
    logger.debug(
        f"Collected context: {user_context[:50]}"
        f"{'...' if len(user_context) > 50 else ''}"
    )
    return user_context if user_context else None


def _collect_regeneration_feedback(
    results: Dict[str, str],
    act: Act,
    game_name: str,
    original_context: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Collect feedback for regenerating AI content.

    Args:
        results: Dictionary containing previously generated title and summary
        act: The act being completed
        game_name: Name of the game the act belongs to
        original_context: The original context provided for the first generation

    Returns:
        Dictionary with feedback and elements to keep, or None if user cancels
    """
    logger.debug("Collecting regeneration feedback")

    # Create editor configuration
    editor_config = StructuredEditorConfig(
        fields=[
            FieldConfig(
                name="feedback",
                display_name="Regeneration Feedback",
                help_text=(
                    "Provide feedback on how you want the new generation to differ "
                    "(leave empty for a completely new attempt)"
                ),
                multiline=True,
                required=False,
            ),
            FieldConfig(
                name="context",
                display_name="Original Context",
                help_text=(
                    "Original context provided for generation. You can modify this "
                    "to include additional information."
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
    )
    context_info += f"Game: {game_name}\n"
    context_info += f"ID: {act.id}\n\n"
    context_info += (
        "Please provide feedback on how you want the new generation to "
        "differ from the previous one.\n"
    )
    context_info += "You can leave this empty to get a completely new attempt.\n\n"
    context_info += (
        "Be specific about what you liked and didn't like about the "
        "previous generation.\n\n"
    )
    context_info += "Examples of effective feedback:\n"
    context_info += (
        '- "Make the title more dramatic and focus on the conflict with '
        'the dragon"\n'
    )
    context_info += (
        '- "The summary is too focused on side characters. Center it on '
        "the protagonist's journey\"\n"
    )
    context_info += (
        '- "Change the tone to be more somber and reflective of the '
        'losses in this act"\n'
    )
    context_info += (
        '- "I like the theme of betrayal in the summary but want it to '
        'be more subtle"\n'
    )
    context_info += (
        '- "Keep the reference to the ancient ruins, but make the title '
        'more ominous"\n\n'
    )
    context_info += "PREVIOUS GENERATION:\n"
    context_info += f"Title: {results.get('title', '')}\n"
    context_info += f"Summary: {results.get('summary', '')}\n\n"

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

    # Open editor
    result, modified = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
        editor_config=EditorConfig(
            edit_message="Edit your regeneration feedback below (or leave empty for a new attempt):",
            success_message="Feedback collected successfully.",
            cancel_message="Regeneration cancelled.",
            error_message="Could not open editor. Please try again.",
        ),
    )

    if not modified:
        logger.debug("User cancelled regeneration feedback collection")
        return None

    return {
        "feedback": result.get("feedback", "").strip(),
        "context": result.get("context", "").strip(),
    }


def _edit_ai_content(
    results: Dict[str, str], act: Act, game_name: str
) -> Optional[Dict[str, str]]:
    """Allow user to edit AI-generated content.

    Args:
        results: Dictionary containing generated title and summary
        act: The act being completed
        game_name: Name of the game the act belongs to

    Returns:
        Dictionary with edited title and summary, or None if user cancels
    """
    logger.debug("Opening editor for AI content")

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
                help_text=(
                    "Edit the AI-generated summary (3-5 paragraphs recommended)"
                ),
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
    )
    context_info += f"Game: {game_name}\n"
    context_info += f"ID: {act.id}\n\n"
    context_info += "Edit the AI-generated title and summary below.\n"
    context_info += (
        "- The title should capture the essence or theme of the act (1-7 words)\n"
    )
    context_info += (
        "- The summary should highlight key events and narrative arcs "
        "(3-5 paragraphs)\n"
    )

    # Add original content as comments if it exists
    original_data = {}
    if act.title:
        original_data["title"] = act.title
    if act.summary:
        original_data["summary"] = act.summary

    # Open editor
    edited_results, modified = edit_structured_data(
        results,
        console,
        editor_config,
        context_info=context_info,
        original_data=original_data if original_data else None,
        editor_config=EditorConfig(
            edit_message="Edit the AI-generated content below:",
            success_message="AI-generated content updated successfully.",
            cancel_message="Edit cancelled.",
            error_message="Could not open editor. Please try again.",
        ),
    )

    if not modified:
        logger.debug("User cancelled editing")
        return None

    # Validate the edited content
    if not edited_results.get("title") or not edited_results.get("title").strip():
        console.print("[red]Error:[/] Title cannot be empty.")
        return None

    if (
        not edited_results.get("summary")
        or not edited_results.get("summary").strip()
    ):
        console.print("[red]Error:[/] Summary cannot be empty.")
        return None

    # Show a preview of the edited content
    from sologm.cli.utils.display import display_act_edited_content_preview

    display_act_edited_content_preview(console, edited_results)

    # Ask for confirmation
    from rich.prompt import Confirm

    if Confirm.ask(
        "[yellow]Use this edited content?[/yellow]",
        default=True,
    ):
        logger.debug("User confirmed edited content")
        return edited_results
    else:
        logger.debug("User rejected edited content")
        return None


def _handle_user_feedback_loop(
    results: Dict[str, str],
    act: Act,
    game_name: str,
    act_manager: ActManager,
    original_context: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Handle the accept/edit/regenerate feedback loop.

    Args:
        results: Dictionary containing generated title and summary
        act: The act being completed
        game_name: Name of the game the act belongs to
        act_manager: ActManager instance for business logic
        original_context: The original context provided for the first generation

    Returns:
        Final dictionary with title and summary, or None if user cancels
    """
    logger.debug("Starting user feedback loop")

    while True:
        # Get user choice using the display helper
        from sologm.cli.utils.display import display_act_ai_feedback_prompt

        choice = display_act_ai_feedback_prompt(console)

        logger.debug(f"User chose: {choice}")

        if choice == "A":  # Accept
            logger.debug("User accepted the generated content")
            return results

        elif choice == "E":  # Edit
            logger.debug("User chose to edit the generated content")
            edited_results = _edit_ai_content(results, act, game_name)

            if edited_results:
                return edited_results

            # If editing was cancelled, return to the prompt
            console.print("[yellow]Edit cancelled. Returning to prompt.[/yellow]")
            continue

        elif choice == "R":  # Regenerate
            logger.debug("User chose to regenerate content")

            # Collect regeneration feedback
            feedback_data = _collect_regeneration_feedback(
                results, act, game_name, original_context
            )

            if not feedback_data:
                console.print(
                    "[yellow]Regeneration cancelled. Returning to prompt.[/yellow]"
                )
                continue

            try:
                console.print("[yellow]Regenerating summary with AI...[/yellow]")

                # Generate new content with feedback
                if feedback_data["feedback"] or feedback_data["context"]:
                    # If user provided feedback or updated context, use it
                    new_results = act_manager.generate_act_summary_with_feedback(
                        act.id,
                        feedback_data["feedback"],
                        previous_generation=results,
                        context=feedback_data["context"],
                    )
                else:
                    # If user didn't provide feedback or context, just generate a new summary
                    # without referencing the previous one
                    console.print(
                        "[yellow]Generating completely new attempt...[/yellow]"
                    )
                    new_results = act_manager.generate_act_summary(act.id)

                # Display the new results
                display_act_ai_generation_results(console, new_results, active_act)

                # Continue the loop with the new results
                results = new_results

            except APIError as e:
                console.print(f"[red]AI Error:[/] {str(e)}")
                console.print("[yellow]Returning to previous content.[/yellow]")
                continue


def _handle_ai_completion(
    act_manager: ActManager,
    active_act: Act,
    active_game: Game,
    console: Console,
    context: Optional[str],
    force: bool,
) -> Optional[Act]:
    """Handles the AI-driven act completion flow.

    Args:
        act_manager: Instance of ActManager
        active_act: The act being completed
        active_game: The game the act belongs to
        console: Rich console instance
        context: Optional context provided via CLI
        force: Whether to force completion

    Returns:
        The completed Act object on success, or None if the process is cancelled or fails.
    """
    logger.debug("Handling AI completion path")

    # 1. Check existing content
    if not _check_existing_content(active_act, force):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return None

    # 2. Collect context if needed
    original_context = context  # Keep track for regeneration feedback
    if not context:
        context = _collect_user_context(active_act, active_game.name)
        # User might cancel context collection, context will be None which is handled by generate_act_summary

    try:
        # 3. Generate initial summary
        console.print("[yellow]Generating summary with AI...[/yellow]")
        summary_data = act_manager.generate_act_summary(active_act.id, context)

        # 4. Display results
        display_act_ai_generation_results(console, summary_data, active_act)

        # 5. Handle user feedback loop
        final_data = _handle_user_feedback_loop(
            summary_data, active_act, active_game.name, act_manager, original_context
        )

        if final_data is None:
            console.print("[yellow]Operation cancelled during feedback.[/yellow]")
            return None  # User cancelled the loop

        # 6. Complete the act with final AI data
        completed_act = act_manager.complete_act_with_ai(
            active_act.id,
            final_data.get("title"),
            final_data.get("summary"),
        )
        return completed_act  # Success

    except APIError as e:
        console.print(f"[red]AI Error:[/] {str(e)}")
        console.print("[yellow]Falling back to manual entry might be needed.[/yellow]")
        return None  # Indicate AI failure
    except Exception as e:
        logger.error(f"Unexpected error during AI completion: {e}", exc_info=True)
        console.print(f"[red]Error during AI processing:[/] {str(e)}")
        return None  # Indicate general failure


def _handle_manual_completion(
    act_manager: ActManager,
    active_act: Act,
    active_game: Game,
    console: Console,
) -> Optional[Act]:
    """Handles the manual act completion flow using the editor.

    Args:
        act_manager: Instance of ActManager
        active_act: The act being completed
        active_game: The game the act belongs to
        console: Rich console instance

    Returns:
        The completed Act object on success, or None if the editor is cancelled.
    """
    logger.debug("Handling manual completion path")

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
    context_info = f"Completing Act {active_act.sequence}: {title_display}\n"
    context_info += f"Game: {active_game.name}\n"
    context_info += f"ID: {active_act.id}\n\n"
    context_info += (
        "You can provide a title and description to summarize this "
        "act's events."
    )

    # 3. Prepare initial data
    initial_data = {
        "title": active_act.title or "",
        "summary": active_act.summary or "",
    }

    # 4. Call editor
    result, modified = edit_structured_data(
        initial_data,
        console,
        editor_config,
        context_info=context_info,
    )

    # 5. Handle cancellation
    if not modified:
        console.print("[yellow]Act completion canceled.[/yellow]")
        return None

    # 6. Extract results
    title = result.get("title") or None
    summary = result.get("summary") or None

    # 7. Complete the act (outer function handles GameError)
    completed_act = act_manager.complete_act(
        act_id=active_act.id, title=title, summary=summary
    )

    # 8. Return completed act
    return completed_act


# --- Main Command ---

@act_app.command("complete")
def complete_act(
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Title for the completed act"
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-s", help="Summary for the completed act"
    ),
    ai: bool = typer.Option(False, "--ai", help="Use AI to generate title and summary"),
    context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        help="Additional context to include in the summary generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force completion even if title/summary already exist",
    ),
) -> None:
    """[bold]Complete the current active act and optionally set its title and summary.[/bold]

    If title and summary are not provided, opens an editor to enter them.

    Completing an act marks it as finished and allows you to provide a
    retrospective title and summary that summarize the narrative events that
    occurred.

    The [cyan]--ai[/cyan] flag can be used to generate a title and summary based on the
    act's content using AI. You can provide additional context with [cyan]--context[/cyan].

    [yellow]Examples:[/yellow]
        [green]Complete act with an interactive editor:[/green]
        $ sologm act complete

        [green]Complete act with specific title and summary:[/green]
        $ sologm act complete -t "The Fall of the Kingdom" -s \\
          "The heroes failed to save the kingdom"

        [green]Complete act with AI-generated title and summary:[/green]
        $ sologm act complete --ai

        [green]Complete act with AI-generated content and additional context:[/green]
        $ sologm act complete --ai \\
          --context "Focus on the themes of betrayal and redemption"

        [green]Force AI regeneration of title/summary:[/green]
        $ sologm act complete --ai --force
    """
    logger.debug("Completing act")

    # Main command flow
    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize managers with the session
        game_manager = GameManager(session=session)
        act_manager = ActManager(session=session)

        try:
            # Validate active game and act
            active_game = game_manager.get_active_game()
            if not active_game:
                console.print("[red]Error:[/] No active game. Activate a game first.")
                raise typer.Exit(1) from e

            active_act = act_manager.get_active_act(active_game.id)
            if not active_act:
                console.print(
                    f"[red]Error:[/] No active act in game '{active_game.name}'."
                )
                console.print("Create one with 'sologm act create'.")
                raise typer.Exit(1)

            completed_act: Optional[Act] = None
            if ai:
                # Handle AI path
                completed_act = _handle_ai_completion(
                    act_manager, active_act, active_game, console, context, force
                )
                # If AI fails or is cancelled, completed_act will be None
                # We implicitly stop here if AI path doesn't succeed
            else:
                # Handle manual path
                completed_act = _handle_manual_completion(
                    act_manager, active_act, active_game, console
                )
                # If manual edit is cancelled, completed_act will be None

            # Display success only if completion happened successfully
            if completed_act:
                display_act_completion_success(console, completed_act)
            else:
                logger.debug("Act completion did not finish successfully or was cancelled.")
                # Optionally, add a message here if needed, e.g.:
                # console.print("[yellow]Act completion process ended.[/yellow]")

        except GameError as e:
            # Catch errors from validation or manual completion
            console.print(f"[red]Error:[/] {str(e)}")
            raise typer.Exit(1) from e
        # Note: APIError and other exceptions during AI flow are handled within _handle_ai_completion
