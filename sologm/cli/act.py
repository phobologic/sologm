"""CLI commands for managing acts.

This module provides commands for creating, listing, viewing, editing, and
completing acts within a game. Acts represent complete narrative situations
or problems that unfold through multiple connected Scenes.
"""

import logging
from typing import Optional

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
from sologm.integrations.anthropic import AnthropicClient
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

    # Check if there's an active act
    active_act = game_manager.act_manager.get_active_act(active_game.id)

    if active_act:
        # There's an active act
        title_display = f"'{active_act.title}'" if active_act.title else "untitled"
        console.print(f"[red]Error:[/] You have an active act ({title_display}).")
        console.print("You must complete the current act before creating a new one.")
        console.print("Use 'sologm act complete' to complete the current act first.")
        raise typer.Exit(1)

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
            console.print(f"[red]Error:[/] No active act in game '{active_game.name}'.")
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
        context_info = f"AI-Generated Summary for Act {act.sequence}: {title_display}\n"
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
        title_display = f"'{updated_act.title}'" if updated_act.title else "untitled"
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
        title_display = f"'{updated_act.title}'" if updated_act.title else "untitled"
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
    ai: bool = typer.Option(
        False, "--ai", help="Use AI to generate title and description if not provided"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force AI generation even if title/description already exist",
    ),
) -> None:
    """Complete the current active act and optionally set its title and description.

    If title and description are not provided, opens an editor to enter them.
    Completing an act marks it as finished and allows you to provide a retrospective
    title and description that summarize the narrative events that occurred.

    The --ai flag can be used to generate a title and description based on the
    act's content (when implemented).

    Examples:
        Complete act with an interactive editor:
        $ sologm act complete

        Complete act with specific title and description:
        $ sologm act complete -t "The Fall of the Kingdom" -d "The heroes failed to save the kingdom"

        Complete act with AI-generated title and description (when implemented):
        $ sologm act complete --ai

        Force AI regeneration of title/description (when implemented):
        $ sologm act complete --ai --force
    """
    logger.debug("Completing act")

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

    # Check if we need to generate with AI
    if ai:
        # Check if we should generate title/summary
        should_generate_title = force or not active_act.title
        should_generate_summary = force or not active_act.summary

        if should_generate_title or should_generate_summary:
            console.print(
                "[yellow]AI generation of act title/summary is not yet implemented.[/yellow]"
            )
            console.print("Please provide title and summary manually.")
            # This is where AI generation would be implemented
        elif not force:
            console.print(
                "[yellow]Act already has title and description. Use --force to override.[/yellow]"
            )

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
        context_info = f"Completing Act {active_act.sequence}: {title_display}\n"
        context_info += f"Game: {active_game.name}\n"
        context_info += f"ID: {active_act.id}\n\n"
        context_info += (
            "You can provide a title and description to summarize this act's events."
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
        completed_act = game_manager.act_manager.complete_act(
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
