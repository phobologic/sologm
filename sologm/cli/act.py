"""CLI commands for managing acts.

This module provides commands for creating, listing, viewing, editing, and completing
acts within a game. Acts represent complete narrative situations or problems that
unfold through multiple connected Scenes.
"""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm.cli.utils.display import (
    display_act_info,
    display_acts_table,
    display_game_info,
)
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.cli.utils.styled_text import StyledText
from sologm.core.act import ActManager
from sologm.core.game import GameManager
from sologm.models.act import ActStatus
from sologm.utils.errors import GameError

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
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description of the act"
    ),
) -> None:
    """Create a new act in the current game.

    If title and description are not provided, opens an editor to enter them.
    Acts can be created without a title or description, allowing you to name them
    later once their significance becomes clear.

    Note: You must complete the current active act (if any) before creating a new one.
    Use 'sologm act complete' to complete the current act first.

    Examples:
        Create an act with title and description directly:
        $ sologm act create --title "The Journey Begins" --description "The heroes set out on their quest"

        Create an untitled act:
        $ sologm act create

        Create an act with just a title:
        $ sologm act create -t "The Journey Begins"
    """
    logger.debug("Creating new act")

    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # Check if there's an active act that needs to be completed
    act_manager = ActManager()
    active_act = act_manager.get_active_act(active_game.id)

    if active_act and active_act.status != ActStatus.COMPLETED:
        # There's an active act that's not completed
        title_display = f"'{active_act.title}'" if active_act.title else "untitled"
        console.print(
            f"[red]Error:[/] You have an active act ({title_display}) that is not completed."
        )
        console.print("You must complete the current act before creating a new one.")
        console.print("Use 'sologm act complete' to complete the current act first.")
        raise typer.Exit(1)

    # If title and description are not provided, open editor
    if title is None or description is None:
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
                    name="description",
                    display_name="Description",
                    help_text="Description of the act",
                    multiline=True,
                    required=False,
                ),
            ],
            wrap_width=70,
        )

        # Create context information
        context_info = f"Creating a new act in game: {active_game.name}\n\n"
        context_info += "Acts represent complete narrative situations or problems that unfold through multiple connected Scenes.\n"
        context_info += "You can leave the title and description empty if you're not sure what to call this act yet."

        # Create initial data
        initial_data = {
            "title": title or "",
            "description": description or "",
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
        description = result.get("description") or None

    # Create the act
    try:
        act = act_manager.create_act(
            game_id=active_game.id,
            title=title,
            description=description,
        )

        # Display success message
        title_display = f"'{act.title}'" if act.title else "untitled"
        console.print(
            f"[bold green]Act {title_display} created successfully![/bold green]"
        )

        # Display act details
        console.print(f"ID: {act.id}")
        console.print(f"Sequence: Act {act.sequence}")
        console.print(f"Status: {act.status.value}")
        console.print(f"Active: {act.is_active}")
        if act.title:
            console.print(f"Title: {act.title}")
        if act.description:
            console.print(f"Description: {act.description}")

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

    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # Get all acts for the game
    act_manager = ActManager()
    acts = act_manager.list_acts(active_game.id)

    # Get active act ID
    active_act = act_manager.get_active_act(active_game.id)
    active_act_id = active_act.id if active_act else None

    # Display game info
    display_game_info(console, active_game)
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

    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # Get the active act
    act_manager = ActManager()
    active_act = act_manager.get_active_act(active_game.id)
    if not active_act:
        console.print(f"[red]Error:[/] No active act in game '{active_game.name}'.")
        console.print("Create one with 'sologm act create'.")
        raise typer.Exit(1)

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

    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # Get the active act
    act_manager = ActManager()
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
                    name="description",
                    display_name="Description",
                    help_text="Description of the act",
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
        context_info += f"Status: {active_act.status.value}\n"
        context_info += f"ID: {active_act.id}\n\n"
        context_info += "You can leave the title empty for an untitled act."

        # Create initial data
        initial_data = {
            "title": active_act.title or "",
            "description": active_act.description or "",
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
        description = result.get("description") or None

    # Update the act
    try:
        updated_act = act_manager.edit_act(
            act_id=active_act.id,
            title=title,
            description=description,
        )

        # Display success message
        title_display = f"'{updated_act.title}'" if updated_act.title else "untitled"
        console.print(
            f"[bold green]Act {title_display} updated successfully![/bold green]"
        )

        # Display updated act details
        console.print(f"ID: {updated_act.id}")
        console.print(f"Sequence: Act {updated_act.sequence}")
        console.print(f"Status: {updated_act.status.value}")
        if updated_act.title:
            console.print(f"Title: {updated_act.title}")
        if updated_act.description:
            console.print(f"Description: {updated_act.description}")

    except GameError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)


@act_app.command("complete")
def complete_act(
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Title for the completed act"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description for the completed act"
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

    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)

    # Get the active act
    act_manager = ActManager()
    active_act = act_manager.get_active_act(active_game.id)
    if not active_act:
        console.print(f"[red]Error:[/] No active act in game '{active_game.name}'.")
        console.print("Create one with 'sologm act create'.")
        raise typer.Exit(1)

    # Check if we need to generate with AI
    if ai:
        # Check if we should generate title/description
        should_generate_title = force or not active_act.title
        should_generate_description = force or not active_act.description

        if should_generate_title or should_generate_description:
            console.print(
                "[yellow]AI generation of act title/description is not yet implemented.[/yellow]"
            )
            console.print("Please provide title and description manually.")
            # This is where AI generation would be implemented
        elif not force:
            console.print(
                "[yellow]Act already has title and description. Use --force to override.[/yellow]"
            )

    # If title and description are not provided, open editor
    if title is None and description is None and not ai:
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
                    name="description",
                    display_name="Description",
                    help_text="Description of the completed act",
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
            "description": active_act.description or "",
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
        description = result.get("description") or None

    # Complete the act
    try:
        completed_act = act_manager.complete_act(
            act_id=active_act.id,
            title=title,
            description=description,
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
        console.print(f"Status: {completed_act.status.value}")
        if completed_act.title:
            console.print(f"Title: {completed_act.title}")
        if completed_act.description:
            console.print(f"Description: {completed_act.description}")

    except GameError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)
