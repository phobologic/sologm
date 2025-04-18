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
