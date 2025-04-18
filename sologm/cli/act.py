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
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.core.act import ActManager
from sologm.core.game import GameManager
from sologm.utils.errors import APIError, GameError

logger = logging.getLogger(__name__)

# Create console for rich output
console = Console()

# Create Typer app for act commands
act_app = typer.Typer(
    name="act",
    help="Manage acts in your games",
    no_args_is_help=True,
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
    """Create a new act in the current game.

    If title and summary are not provided, opens an editor to enter them.
    Acts can be created without a title or summary, allowing you to name them
    later once their significance becomes clear.

    Note: You must complete the current active act (if any) before creating a new one.
    Use 'sologm act complete' to complete the current act first.

    Examples:
        Create an act with title and summary directly:
        $ sologm act create --title "The Journey Begins" \
            --summary "The heroes set out on their quest"

        Create an untitled act:
        $ sologm act create

        Create an act with just a title:
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
        raise typer.Exit(1)


@act_app.command("summary")
def generate_act_summary(
    context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        help="Additional context to include in the summary generation",
    ),
    act_id: Optional[str] = typer.Option(
        None,
        "--act-id",
        "-a",
        help="ID of the act to summarize (defaults to current act)",
    ),
) -> None:
    """Generate a summary and title for an act using AI.

    This command uses the Anthropic API to analyze the act's content (scenes and events)
    and generate a concise summary and title. The generated content is presented in an
    editor where you can review and modify it before saving.

    Examples:
        Generate summary for the current act:
        $ sologm act summary

        Generate summary with additional context:
        $ sologm act summary --context "Focus on the character's internal struggles"

        Generate summary for a specific act:
        $ sologm act summary --act-id abc123
    """
    logger.debug("Generating act summary")

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize managers with the session
        game_manager = GameManager(session=session)
        active_game = game_manager.get_active_game()
        if not active_game:
            console.print("[red]Error:[/] No active game. Activate a game first.")
            raise typer.Exit(1)

        # Get the act to summarize
        act_manager = ActManager(session=session)
        if act_id:
            act = act_manager.get_act(act_id)
            if not act:
                console.print(f"[red]Error:[/] Act with ID '{act_id}' not found.")
                raise typer.Exit(1)
        else:
            act = act_manager.get_active_act(active_game.id)
            if not act:
                console.print(
                    f"[red]Error:[/] No active act in game '{active_game.name}'."
                )
                console.print("Create one with 'sologm act create'.")
                raise typer.Exit(1)

        # Generate the summary
        try:
            # Generate the summary using AI
            console.print("[yellow]Generating summary with AI...[/yellow]")
            summary_data = act_manager.generate_act_summary(act.id, context)

            # Create editor configuration
            editor_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="title",
                        display_name="Title",
                        help_text="AI-generated title for the act",
                        required=True,
                    ),
                    FieldConfig(
                        name="summary",
                        display_name="Summary",
                        help_text="AI-generated summary of the act",
                        multiline=True,
                        required=True,
                    ),
                ],
                wrap_width=70,
            )

            # Create context information
            title_display = act.title or "Untitled Act"
            context_info = (
                f"AI-Generated Summary for Act {act.sequence}: {title_display}\n"
            )
            context_info += f"Game: {active_game.name}\n"
            context_info += f"ID: {act.id}\n\n"
            context_info += "Review and edit the AI-generated title and summary below."

            # Open editor with the generated content
            result, modified = edit_structured_data(
                summary_data,
                console,
                editor_config,
                context_info=context_info,
            )

            if not modified:
                console.print("[yellow]Summary generation canceled.[/yellow]")
                raise typer.Exit(0)

            # Update the act with the edited summary and title
            updated_act = act_manager.edit_act(
                act_id=act.id,
                title=result.get("title"),
                summary=result.get("summary"),
            )

            # Display success message
            title_display = (
                f"'{updated_act.title}'" if updated_act.title else "untitled"
            )
            console.print(
                f"[bold green]Act {title_display} updated with AI-generated summary![/bold green]"
            )

        except APIError as e:
            console.print(f"[red]AI Error:[/] {str(e)}")
            raise typer.Exit(1)
        except GameError as e:
            console.print(f"[red]Error:[/] {str(e)}")
            raise typer.Exit(1)


@act_app.command("list")
def list_acts() -> None:
    """List all acts in the current game.

    Displays a table of all acts in the current game, including their sequence,
    title, description, status, and whether they are active.

    Examples:
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
            raise typer.Exit(1)

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
    """Show details of the current active act.

    Displays detailed information about the currently active act, including
    its title, description, status, sequence, and any scenes it contains.

    Examples:
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
    """Edit the current active act.

    If title and description are not provided, opens an editor to enter them.
    You can update the title and/or description of the act, or remove them
    by leaving the fields empty.

    Examples:
        Edit act with an interactive editor:
        $ sologm act edit

        Update just the title:
        $ sologm act edit --title "New Title"

        Update both title and description:
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
            raise typer.Exit(1)


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
    """Complete the current active act and optionally set its title and summary.

    If title and summary are not provided, opens an editor to enter them.
    Completing an act marks it as finished and allows you to provide a retrospective
    title and summary that summarize the narrative events that occurred.

    The --ai flag can be used to generate a title and summary based on the
    act's content using AI. You can provide additional context with --context.

    Examples:
        Complete act with an interactive editor:
        $ sologm act complete

        Complete act with specific title and summary:
        $ sologm act complete -t "The Fall of the Kingdom" -s "The heroes failed to save the kingdom"

        Complete act with AI-generated title and summary:
        $ sologm act complete --ai

        Complete act with AI-generated content and additional context:
        $ sologm act complete --ai --context "Focus on the themes of betrayal and redemption"

        Force AI regeneration of title/summary:
        $ sologm act complete --ai --force
    """
    logger.debug("Completing act")

    # Helper methods for AI generation flow
    def _handle_ai_generation(
        act_id: str, user_context: Optional[str]
    ) -> Dict[str, str]:
        """Handle the AI generation process for act summary and title.

        Args:
            act_id: ID of the act to generate summary for
            user_context: Optional additional context from the user

        Returns:
            Dictionary containing generated title and summary

        Raises:
            APIError: If there's an error with the AI API
        """
        logger.debug(f"Handling AI generation for act {act_id}")
        try:
            # Generate summary using the ActManager
            summary_data = act_manager.generate_act_summary(act_id, user_context)
            logger.debug(f"Generated summary data: {summary_data}")
            return summary_data
        except Exception as e:
            logger.error(f"Error in AI generation: {str(e)}", exc_info=True)
            raise

    def _collect_context(act: Act, game_name: str) -> Optional[str]:
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
        context_info += "Provide any additional context or guidance for the AI summary generation.\n"
        context_info += "For example:\n"
        context_info += "- Focus on specific themes or character developments\n"
        context_info += "- Highlight particular events or turning points\n"
        context_info += "- Suggest a narrative style or tone for the summary\n\n"
        context_info += "You can leave this empty to let the AI generate based only on the act's content."

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
            f"Collected context: {user_context[:50]}{'...' if len(user_context) > 50 else ''}"
        )
        return user_context if user_context else None

    def _process_ai_results(results: Dict[str, str], act: Act) -> None:
        """Process and display AI-generated content.

        Formats and displays the AI-generated title and summary with appropriate styling.
        If the act already has a title or summary, displays them for comparison.

        Args:
            results: Dictionary containing generated title and summary
            act: The act being completed
        """
        logger.debug("Processing AI results for display")

        from rich.panel import Panel

        # Define border styles for different content types
        BORDER_STYLES = {
            "generated": "green",
            "existing": "blue",
        }

        # Display generated title
        if "title" in results and results["title"]:
            title_panel = Panel(
                results["title"],
                title="[bold]AI-Generated Title[/bold]",
                border_style=BORDER_STYLES["generated"],
                expand=False,
            )
            console.print(title_panel)

            # Display existing title for comparison if it exists
            if act.title:
                existing_title_panel = Panel(
                    act.title,
                    title="[bold]Current Title[/bold]",
                    border_style=BORDER_STYLES["existing"],
                    expand=False,
                )
                console.print(existing_title_panel)

        # Display generated summary
        if "summary" in results and results["summary"]:
            summary_panel = Panel(
                results["summary"],
                title="[bold]AI-Generated Summary[/bold]",
                border_style=BORDER_STYLES["generated"],
                expand=False,
            )
            console.print(summary_panel)

            # Display existing summary for comparison if it exists
            if act.summary:
                existing_summary_panel = Panel(
                    act.summary,
                    title="[bold]Current Summary[/bold]",
                    border_style=BORDER_STYLES["existing"],
                    expand=False,
                )
                console.print(existing_summary_panel)

    def _collect_regeneration_context(
        results: Dict[str, str], act: Act, game_name: str
    ) -> Optional[str]:
        """Collect context for regenerating AI content.

        Opens a structured editor to allow the user to provide feedback on how they
        want the new generation to differ from the previous one. Includes the previously
        generated content as reference.

        Args:
            results: Dictionary containing previously generated title and summary
            act: The act being completed
            game_name: Name of the game the act belongs to

        Returns:
            The user-provided regeneration context, or None if the user cancels
        """
        logger.debug("Collecting regeneration context")

        # Create editor configuration with improved guidance
        editor_config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="feedback",
                    display_name="Regeneration Feedback",
                    help_text="Provide feedback on how you want the new generation to differ",
                    multiline=True,
                    required=True,
                ),
                FieldConfig(
                    name="keep_elements",
                    display_name="Elements to Keep",
                    help_text="Specify any elements from the previous generation you want to preserve",
                    multiline=True,
                    required=False,
                ),
            ],
            wrap_width=70,
        )

        # Create enhanced context information header with more guidance
        title_display = act.title or "Untitled Act"
        context_info = (
            f"Regeneration Feedback for Act {act.sequence}: {title_display}\n"
        )
        context_info += f"Game: {game_name}\n"
        context_info += f"ID: {act.id}\n\n"
        context_info += "Please provide feedback on how you want the new generation to differ from the previous one.\n"
        context_info += "Be specific about what you liked and didn't like about the previous generation.\n\n"
        context_info += "Examples of effective feedback:\n"
        context_info += '- "Make the title more dramatic and focus on the conflict with the dragon"\n'
        context_info += '- "The summary is too focused on side characters. Center it on the protagonist\'s journey"\n'
        context_info += '- "Change the tone to be more somber and reflective of the losses in this act"\n'
        context_info += '- "I like the theme of betrayal in the summary but want it to be more subtle"\n\n'
        context_info += "PREVIOUS GENERATION:\n"
        context_info += f"Title: {results.get('title', '')}\n"
        context_info += f"Summary: {results.get('summary', '')}\n\n"

        if act.title or act.summary:
            context_info += "CURRENT ACT CONTENT:\n"
            if act.title:
                context_info += f"Title: {act.title}\n"
            if act.summary:
                context_info += f"Summary: {act.summary}\n"

        # Create initial data with suggested structure
        initial_data = {
            "feedback": "I'd like the new generation to...",
            "keep_elements": "",
        }

        # Open editor with improved configuration
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
            logger.debug("User cancelled regeneration context collection")
            return None

        feedback = result.get("feedback", "").strip()
        keep_elements = result.get("keep_elements", "").strip()

        # Combine feedback and keep_elements into a structured format
        combined_feedback = feedback
        if keep_elements:
            combined_feedback += f"\n\nELEMENTS TO PRESERVE:\n{keep_elements}"

        logger.debug(
            f"Collected regeneration feedback: {combined_feedback[:50]}{'...' if len(combined_feedback) > 50 else ''}"
        )
        return combined_feedback if combined_feedback else None

    def _handle_user_feedback(
        results: Dict[str, str], act: Act, game_name: str
    ) -> Optional[Dict[str, str]]:
        """Handle user feedback on AI-generated content.

        Prompts the user to accept, edit, or regenerate the AI-generated content.

        Args:
            results: Dictionary containing generated title and summary
            act: The act being completed
            game_name: Name of the game the act belongs to

        Returns:
            Optional dictionary with updated title and summary, or None if user cancels
        """
        logger.debug("Handling user feedback on AI-generated content")

        from rich.prompt import Prompt

        # Prompt user for action
        choices = "(A)ccept, (E)dit, or (R)egenerate"
        default_choice = "E"

        choice = Prompt.ask(
            f"[yellow]What would you like to do with this content?[/yellow] {choices}",
            choices=["A", "E", "R", "a", "e", "r"],
            default=default_choice,
        ).upper()

        logger.debug(f"User chose: {choice}")

        if choice == "A":  # Accept
            logger.debug("User accepted the generated content")
            return results

        elif choice == "E":  # Edit
            logger.debug("User chose to edit the generated content")

            # Create editor configuration with improved help text
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
                        help_text="Edit the AI-generated summary (1-3 paragraphs recommended)",
                        multiline=True,
                        required=True,
                    ),
                ],
                wrap_width=70,
            )

            # Create enhanced context information with more guidance
            title_display = act.title or "Untitled Act"
            context_info = f"Editing AI-Generated Content for Act {act.sequence}: {title_display}\n"
            context_info += f"Game: {game_name}\n"
            context_info += f"ID: {act.id}\n\n"
            context_info += "Edit the AI-generated title and summary below.\n"
            context_info += "- The title should capture the essence or theme of the act (1-7 words)\n"
            context_info += "- The summary should highlight key events and narrative arcs (1-3 paragraphs)\n"

            # Add original content as comments if it exists
            original_data = {}
            if act.title:
                original_data["title"] = act.title
            if act.summary:
                original_data["summary"] = act.summary

            # Open editor with the generated content and improved configuration
            edited_results, modified = edit_structured_data(
                results,
                console,
                editor_config,
                context_info=context_info,
                original_data=original_data if original_data else None,
                editor_config=EditorConfig(
                    message="Edit the AI-generated content below:",
                    success_message="AI-generated content updated successfully.",
                    cancel_message="Edit cancelled. Returning to previous options.",
                    error_message="Could not open editor. Please try again.",
                ),
            )

            if not modified:
                logger.debug("User cancelled editing")
                console.print("[yellow]Edit cancelled. Returning to prompt.[/yellow]")
                # Recursive call to handle user feedback again
                return _handle_user_feedback(results, act, game_name)

            # Validate the edited content
            if (
                not edited_results.get("title")
                or not edited_results.get("title").strip()
            ):
                console.print("[red]Error:[/] Title cannot be empty. Please try again.")
                return _handle_user_feedback(results, act, game_name)

            if (
                not edited_results.get("summary")
                or not edited_results.get("summary").strip()
            ):
                console.print(
                    "[red]Error:[/] Summary cannot be empty. Please try again."
                )
                return _handle_user_feedback(results, act, game_name)

            logger.debug("User edited the content")

            # Show a preview of the edited content
            from rich.panel import Panel

            console.print("\n[bold]Preview of your edited content:[/bold]")

            title_panel = Panel(
                edited_results["title"],
                title="[bold]Edited Title[/bold]",
                border_style="green",
                expand=False,
            )
            console.print(title_panel)

            summary_panel = Panel(
                edited_results["summary"],
                title="[bold]Edited Summary[/bold]",
                border_style="green",
                expand=False,
            )
            console.print(summary_panel)

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
                console.print("[yellow]Edit cancelled. Returning to prompt.[/yellow]")
                return _handle_user_feedback(results, act, game_name)

        elif choice == "R":  # Regenerate
            logger.debug("User chose to regenerate content")

            # Collect regeneration context
            regeneration_context = _collect_regeneration_context(
                results, act, game_name
            )

            if regeneration_context is None:
                logger.debug("User cancelled regeneration context collection")
                console.print(
                    "[yellow]Regeneration cancelled. Returning to prompt.[/yellow]"
                )
                # Recursive call to handle user feedback again
                return _handle_user_feedback(results, act, game_name)

            # Generate new content with the updated context
            try:
                console.print("[yellow]Regenerating summary with AI...[/yellow]")

                # Include previous generation in context with structured format
                full_context = (
                    f"PREVIOUS GENERATION:\n"
                    f"Title: {results.get('title', '')}\n"
                    f"Summary: {results.get('summary', '')}\n\n"
                    f"USER FEEDBACK:\n{regeneration_context}\n\n"
                    f"INSTRUCTIONS:\n"
                    f"Generate a new title and summary that addresses the user's feedback. "
                    f"Make sure your new generation is noticeably different from the previous one "
                    f"while incorporating any elements the user wants to preserve."
                )

                # Generate new summary
                new_results = _handle_ai_generation(act.id, full_context)

                # Display the new results
                _process_ai_results(new_results, act)

                # Handle feedback on the new results
                return _handle_user_feedback(new_results, act, game_name)

            except APIError as e:
                console.print(f"[red]AI Error:[/] {str(e)}")
                console.print("[yellow]Returning to previous content.[/yellow]")
                # Return to previous content
                return _handle_user_feedback(results, act, game_name)

        # Should never reach here due to Prompt validation
        return results

    def _complete_act_with_data(
        act_id: str, title: Optional[str], summary: Optional[str]
    ) -> Act:
        """Complete the act with the provided data.

        Args:
            act_id: ID of the act to complete
            title: Optional title for the completed act
            summary: Optional summary for the completed act

        Returns:
            The completed act
        """
        logger.debug(f"Completing act {act_id} with title and summary")
        return act_manager.complete_act(act_id=act_id, title=title, summary=summary)

    from sologm.database.session import get_db_context

    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        game_manager = GameManager(session=session)
        act_manager = ActManager(session=session)

        try:
            # Validate active game and act
            active_game = game_manager.get_active_game()
            if not active_game:
                console.print("[red]Error:[/] No active game. Activate a game first.")
                raise typer.Exit(1)

            active_act = act_manager.get_active_act(active_game.id)
            if not active_act:
                console.print(
                    f"[red]Error:[/] No active act in game '{active_game.name}'."
                )
                console.print("Create one with 'sologm act create'.")
                raise typer.Exit(1)

            # Handle AI generation if requested
            if ai:
                # If no context was provided via command line, collect it interactively
                if not context:
                    logger.debug(
                        "No context provided via command line, collecting interactively"
                    )
                    context = _collect_context(active_act, active_game.name)
                    if context:
                        logger.debug(
                            f"Context collected interactively: {context[:50]}{'...' if len(context) > 50 else ''}"
                        )
                else:
                    logger.debug(
                        f"Context provided via command line: {context[:50]}{'...' if len(context) > 50 else ''}"
                    )

                # Check if we should generate title/summary
                should_generate_title = force or not active_act.title
                should_generate_summary = force or not active_act.summary

                if should_generate_title or should_generate_summary:
                    try:
                        console.print("[yellow]Generating summary with AI...[/yellow]")

                        # Generate summary using AI
                        summary_data = _handle_ai_generation(active_act.id, context)

                        # Display the generated content
                        _process_ai_results(summary_data, active_act)

                        # Handle user feedback
                        final_data = _handle_user_feedback(
                            summary_data, active_act, active_game.name
                        )

                        if final_data is None:
                            console.print("[yellow]Operation cancelled.[/yellow]")
                            return

                        # Use the final data (original or modified based on user feedback)
                        title = final_data.get("title")
                        summary = final_data.get("summary")

                        # Complete the act with the final data
                        completed_act = _complete_act_with_data(
                            active_act.id, title, summary
                        )

                        # Display success message
                        title_display = (
                            f"'{completed_act.title}'"
                            if completed_act.title
                            else "untitled"
                        )
                        console.print(
                            f"[bold green]Act {title_display} completed successfully with AI-generated content![/bold green]"
                        )

                        # Display completed act details
                        console.print(f"ID: {completed_act.id}")
                        console.print(f"Sequence: Act {completed_act.sequence}")
                        console.print(f"Active: {completed_act.is_active}")

                        # Exit early since we've completed the act
                        return

                    except APIError as e:
                        console.print(f"[red]AI Error:[/] {str(e)}")
                        console.print("Falling back to manual entry.")
                    except Exception as e:
                        console.print(f"[red]Error:[/] {str(e)}")
                        console.print("Falling back to manual entry.")
                elif not force:
                    # Ask for confirmation before replacing existing content
                    has_title = (
                        active_act.title is not None and active_act.title.strip() != ""
                    )
                    has_summary = (
                        active_act.summary is not None
                        and active_act.summary.strip() != ""
                    )

                    if has_title and has_summary:
                        confirm_message = (
                            "This will replace your existing title and summary."
                        )
                    elif has_title:
                        confirm_message = "This will replace your existing title."
                    else:
                        confirm_message = "This will replace your existing summary."

                    from rich.prompt import Confirm

                    if Confirm.ask(
                        f"[yellow]{confirm_message} Continue?[/yellow]", default=False
                    ):
                        logger.debug("User confirmed replacing existing content")
                        # Generate summary using AI
                        try:
                            console.print(
                                "[yellow]Generating summary with AI...[/yellow]"
                            )

                            # Generate summary using AI
                            summary_data = _handle_ai_generation(active_act.id, context)

                            # Display the generated content
                            _process_ai_results(summary_data, active_act)

                            # Handle user feedback
                            final_data = _handle_user_feedback(
                                summary_data, active_act, active_game.name
                            )

                            if final_data is None:
                                console.print("[yellow]Operation cancelled.[/yellow]")
                                return

                            # Use the final data (original or modified based on user feedback)
                            title = final_data.get("title")
                            summary = final_data.get("summary")

                            # Complete the act with the final data
                            completed_act = _complete_act_with_data(
                                active_act.id, title, summary
                            )

                            # Display success message
                            title_display = (
                                f"'{completed_act.title}'"
                                if completed_act.title
                                else "untitled"
                            )
                            console.print(
                                f"[bold green]Act {title_display} completed successfully with AI-generated content![/bold green]"
                            )

                            # Display completed act details
                            console.print(f"ID: {completed_act.id}")
                            console.print(f"Sequence: Act {completed_act.sequence}")
                            console.print(f"Active: {completed_act.is_active}")

                            # Exit early since we've completed the act
                            return

                        except APIError as e:
                            console.print(f"[red]AI Error:[/] {str(e)}")
                            console.print("Falling back to manual entry.")
                        except Exception as e:
                            console.print(f"[red]Error:[/] {str(e)}")
                            console.print("Falling back to manual entry.")
                    else:
                        logger.debug("User cancelled replacing existing content")
                        console.print("[yellow]Operation cancelled.[/yellow]")
                        return

            # If title and summary are not provided, open editor
            if title is None and summary is None and not ai:
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
                context_info = (
                    f"Completing Act {active_act.sequence}: {title_display}\n"
                )
                context_info += f"Game: {active_game.name}\n"
                context_info += f"ID: {active_act.id}\n\n"
                context_info += "You can provide a title and description to summarize this act's events."

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
                    act_id=active_act.id,
                    title=title,
                    summary=summary,
                )

                # Display success message
                title_display = (
                    f"'{completed_act.title}'" if completed_act.title else "untitled"
                )
                console.print(
                    f"[bold green]Act {title_display} completed successfully![/bold green]"
                )

                # Display completed act details
                console.print(f"ID: {completed_act.id}")
                console.print(f"Sequence: Act {completed_act.sequence}")
                console.print(f"Active: {completed_act.is_active}")
                if completed_act.title:
                    console.print(f"Title: {completed_act.title}")
                if completed_act.summary:
                    console.print(f"Summary: {completed_act.summary}")

            except GameError as e:
                console.print(f"[red]Error:[/] {str(e)}")
                raise typer.Exit(1)
        except GameError as e:
            console.print(f"[red]Error:[/] {str(e)}")
            raise typer.Exit(1)
