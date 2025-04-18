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
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="New title for the act"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description for the act"
    ),
) -> None:
    """[bold]Edit the current active act.[/bold]

    If title and description are not provided, opens an editor to enter them.
    You can update the title and/or description of the act, or remove them
    by leaving the fields empty.

    [yellow]Examples:[/yellow]
        [green]Edit act with an interactive editor:[/green]
        $ sologm act edit

        [green]Update just the title:[/green]
        $ sologm act edit --title "New Title"

        [green]Update both title and description:[/green]
        $ sologm act edit -t "New Title" -d "New description of the act"
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

        # Get the active act
        act_manager = ActManager(session=session)
        active_act = act_manager.get_active_act(active_game.id)
        if not active_act:
            console.print(f"[red]Error:[/] No active act in game '{active_game.name}'.")
            console.print("Create one with 'sologm act create'.")
            raise typer.Exit(1)

        # If title and description are not provided, open editor
        if title is None and description is None:
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
            title_display = active_act.title or "Untitled Act"
            context_info = f"Editing Act {active_act.sequence}: {title_display}\n"
            context_info += f"Game: {active_game.name}\n"
            context_info += f"ID: {active_act.id}\n\n"
            context_info += "You can leave the title empty for an untitled act."

            # Create initial data
            initial_data = {
                "title": active_act.title or "",
                "summary": active_act.summary or "",
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

            title = result.get("title") or None
            summary = result.get("summary") or None

        # Update the act
        try:
            updated_act = game_manager.act_manager.edit_act(
                act_id=active_act.id,
                title=title,
                summary=summary,
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

    # Helper methods for UI interaction
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

    from sologm.cli.utils.display import display_act_ai_generation_results

    def _collect_regeneration_feedback(
        results: Dict[str, str], act: Act, game_name: str
    ) -> Optional[Dict[str, str]]:
        """Collect feedback for regenerating AI content.

        Args:
            results: Dictionary containing previously generated title and summary
            act: The act being completed
            game_name: Name of the game the act belongs to

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
                        "Provide feedback on how you want the new generation to differ"
                    ),
                    multiline=True,
                    required=True,
                ),
                FieldConfig(
                    name="keep_elements",
                    display_name="Elements to Keep",
                    help_text=(
                        "Specify any elements from the previous generation "
                        "you want to preserve"
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
            'be more subtle"\n\n'
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
            "feedback": "I'd like the new generation to...",
            "keep_elements": "",
        }

        # Open editor
        result, modified = edit_structured_data(
            initial_data,
            console,
            editor_config,
            context_info=context_info,
            editor_config=EditorConfig(
                message="Edit your regeneration feedback below:",
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
            "keep_elements": result.get("keep_elements", "").strip(),
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
                        "Edit the AI-generated summary (1-3 paragraphs recommended)"
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
            "(1-3 paragraphs)\n"
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
                message="Edit the AI-generated content below:",
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
        results: Dict[str, str], act: Act, game_name: str, act_manager: ActManager
    ) -> Optional[Dict[str, str]]:
        """Handle the accept/edit/regenerate feedback loop.

        Args:
            results: Dictionary containing generated title and summary
            act: The act being completed
            game_name: Name of the game the act belongs to
            act_manager: ActManager instance for business logic

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
                feedback_data = _collect_regeneration_feedback(results, act, game_name)

                if not feedback_data:
                    console.print(
                        "[yellow]Regeneration cancelled. Returning to prompt.[/yellow]"
                    )
                    continue

                try:
                    console.print("[yellow]Regenerating summary with AI...[/yellow]")

                    # Generate new content with feedback
                    new_results = act_manager.generate_act_summary_with_feedback(
                        act.id, feedback_data["feedback"], previous_generation=results
                    )

                    # Display the new results
                    _display_ai_results(new_results, act)

                    # Continue the loop with the new results
                    results = new_results

                except APIError as e:
                    console.print(f"[red]AI Error:[/] {str(e)}")
                    console.print("[yellow]Returning to previous content.[/yellow]")
                    continue


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

            # Handle AI generation if requested
            if ai:
                # Check if we should proceed with generation
                if not _check_existing_content(active_act, force):
                    console.print("[yellow]Operation cancelled.[/yellow]")
                    return

                # If no context was provided via command line, collect it interactively
                if not context:
                    logger.debug(
                        "No context provided via command line, collecting interactively"
                    )
                    context = _collect_user_context(active_act, active_game.name)
                    if context is None:
                        console.print("[yellow]Operation cancelled.[/yellow]")
                        return

                try:
                    # Generate summary using AI
                    console.print("[yellow]Generating summary with AI...[/yellow]")
                    summary_data = act_manager.generate_act_summary(
                        active_act.id, context
                    )

                    # Display the generated content
                    display_act_ai_generation_results(console, summary_data, active_act)

                    # Handle user feedback
                    final_data = _handle_user_feedback_loop(
                        summary_data, active_act, active_game.name, act_manager
                    )

                    if final_data is None:
                        console.print("[yellow]Operation cancelled.[/yellow]")
                        return

                    # Complete the act with the final data
                    completed_act = act_manager.complete_act_with_ai(
                        active_act.id,
                        final_data.get("title"),
                        final_data.get("summary"),
                    )

                    # Display success message
                    display_act_completion_success(console, completed_act)
                    return

                except APIError as e:
                    console.print(f"[red]AI Error:[/] {str(e)}")
                    console.print("Falling back to manual entry.")
                except Exception as e:
                    console.print(f"[red]Error:[/] {str(e)}")
                    console.print("Falling back to manual entry.")

            # Handle manual completion
            # Create editor configuration
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

            # Create context information
            title_display = active_act.title or "Untitled Act"
            context_info = f"Completing Act {active_act.sequence}: {title_display}\n"
            context_info += f"Game: {active_game.name}\n"
            context_info += f"ID: {active_act.id}\n\n"
            context_info += (
                "You can provide a title and description to summarize this "
                "act's events."
            )

            # Create initial data
            initial_data = {
                "title": active_act.title or "",
                "summary": active_act.summary or "",
            }

            # Open editor
            result, modified = edit_structured_data(
                initial_data,
                console,
                editor_config,
                context_info=context_info,
            )

            if not modified:
                console.print("[yellow]Act completion canceled.[/yellow]")
                raise typer.Exit(0)

            title = result.get("title") or None
            summary = result.get("summary") or None

            # Complete the act
            try:
                completed_act = act_manager.complete_act(
                    act_id=active_act.id, title=title, summary=summary
                )

                # Display success message
                _display_completion_success(completed_act)

            except GameError as e:
                console.print(f"[red]Error:[/] {str(e)}")
                raise typer.Exit(1)

        except GameError as e:
            console.print(f"[red]Error:[/] {str(e)}")
            raise typer.Exit(1)
