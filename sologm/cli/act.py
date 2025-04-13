"""CLI commands for managing acts.

This module provides commands for creating, listing, viewing, editing, and completing
acts within a game. Acts represent complete narrative situations or problems that
unfold through multiple connected Scenes.
"""

import logging
from typing import Optional, List, Dict, Any

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
from sologm.models.act import ActStatus
from sologm.utils.errors import GameError, APIError

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
    active_act = game_manager.act_manager.get_active_act(active_game.id)

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
        act = game_manager.act_manager.create_act(
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


@act_app.command("summary")
def generate_act_summary(
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="Additional context to include in the summary generation"
    ),
    act_id: Optional[str] = typer.Option(
        None, "--act-id", "-a", help="ID of the act to summarize (defaults to current act)"
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
    
    # Get the active game
    game_manager = GameManager()
    active_game = game_manager.get_active_game()
    if not active_game:
        console.print("[red]Error:[/] No active game. Activate a game first.")
        raise typer.Exit(1)
    
    # Get the act to summarize
    act_manager = ActManager()
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
    
    # Collect data for the summary
    try:
        # Get all scenes in the act with their events
        scenes = act_manager.scene_manager.list_scenes(act.id)
        
        # Prepare the data for the AI prompt
        act_data = _prepare_act_data_for_summary(active_game, act, scenes, context)
        
        # Generate the summary using Anthropic
        console.print("[yellow]Generating summary with AI...[/yellow]")
        summary_data = _generate_act_summary(act_data)
        
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
        context_info += f"Status: {act.status.value}\n"
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
            description=result.get("summary"),
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


def _prepare_act_data_for_summary(game, act, scenes, additional_context=None):
    """Prepare act data for the summary generation prompt.
    
    Args:
        game: The game object
        act: The act to summarize
        scenes: List of scenes in the act
        additional_context: Optional additional context from the user
        
    Returns:
        Dict containing structured data about the act
    """
    # Collect all events from all scenes
    events_by_scene = {}
    for scene in scenes:
        # Get events for this scene
        if hasattr(scene, "events") and scene.events:
            events_by_scene[scene.id] = scene.events
        else:
            # If events aren't loaded, load them
            scene_events = act.act_manager.scene_manager.event_manager.list_events(scene_id=scene.id)
            events_by_scene[scene.id] = scene_events
    
    # Format the data
    act_data = {
        "game": {
            "name": game.name,
            "description": game.description,
        },
        "act": {
            "sequence": act.sequence,
            "title": act.title,
            "description": act.description,
            "status": act.status.value,
        },
        "scenes": [],
        "additional_context": additional_context,
    }
    
    # Add scene data
    for scene in scenes:
        scene_data = {
            "sequence": scene.sequence,
            "title": scene.title,
            "description": scene.description,
            "events": [],
        }
        
        # Add events for this scene
        for event in events_by_scene.get(scene.id, []):
            scene_data["events"].append({
                "description": event.description,
                "source": event.source_name if hasattr(event, "source_name") else "Unknown",
                "created_at": event.created_at.isoformat() if event.created_at else None,
            })
        
        act_data["scenes"].append(scene_data)
    
    return act_data


def _generate_act_summary(act_data):
    """Generate a summary for the act using Anthropic API.
    
    Args:
        act_data: Structured data about the act
        
    Returns:
        Dict with generated title and summary
    """
    try:
        # Create Anthropic client
        client = AnthropicClient()
        
        # Build the prompt
        prompt = _build_summary_prompt(act_data)
        
        # Send to Anthropic
        response = client.send_message(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        # Parse the response
        return _parse_summary_response(response)
        
    except Exception as e:
        logger.error(f"Error generating act summary: {str(e)}", exc_info=True)
        raise APIError(f"Failed to generate act summary: {str(e)}")


def _build_summary_prompt(act_data):
    """Build the prompt for the summary generation.
    
    Args:
        act_data: Structured data about the act
        
    Returns:
        String prompt for Anthropic
    """
    game = act_data["game"]
    act = act_data["act"]
    scenes = act_data["scenes"]
    additional_context = act_data.get("additional_context")
    
    # Build the prompt
    prompt = f"""You are an expert storyteller and narrative analyst. I need you to create a concise summary and title for an act in a tabletop roleplaying game.

GAME INFORMATION:
Title: {game['name']}
Description: {game['description']}

ACT INFORMATION:
Sequence: Act {act['sequence']}
Current Title: {act['title'] or 'Untitled'}
Current Description: {act['description'] or 'No description'}
Status: {act['status']}

SCENES IN THIS ACT:
"""

    # Add scenes and their events
    for scene in scenes:
        prompt += f"\nSCENE {scene['sequence']}: {scene['title'] or 'Untitled'}\n"
        prompt += f"Description: {scene['description'] or 'No description'}\n"
        
        if scene['events']:
            prompt += "Events:\n"
            for event in scene['events']:
                prompt += f"- {event['description']}\n"
        else:
            prompt += "No events recorded for this scene.\n"
    
    # Add additional context if provided
    if additional_context:
        prompt += f"\nADDITIONAL CONTEXT:\n{additional_context}\n"
    
    # Add instructions
    prompt += """
TASK:
1. Create a compelling title for this act (1-7 words)
2. Write a concise summary of the act (1-3 paragraphs)

The title should capture the essence or theme of the act.
The summary should highlight key events, character developments, and narrative arcs.

Format your response exactly as follows:

TITLE: [Your suggested title]

SUMMARY:
[Your 1-3 paragraph summary]

Do not include any other text or explanations outside this format.
"""
    
    return prompt


def _parse_summary_response(response):
    """Parse the response from Anthropic.
    
    Args:
        response: Text response from Anthropic
        
    Returns:
        Dict with title and summary
    """
    # Default values
    title = ""
    summary = ""
    
    # Parse the response
    lines = response.strip().split('\n')
    
    # Extract title
    for i, line in enumerate(lines):
        if line.startswith("TITLE:"):
            title = line[6:].strip()
            break
    
    # Extract summary
    summary_start = False
    summary_lines = []
    
    for line in lines:
        if line.startswith("SUMMARY:"):
            summary_start = True
            continue
        
        if summary_start:
            summary_lines.append(line)
    
    summary = "\n".join(summary_lines).strip()
    
    return {
        "title": title,
        "summary": summary,
    }


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

    # Get the active game
    game_manager = GameManager()
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
        updated_act = game_manager.act_manager.edit_act(
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
        completed_act = game_manager.act_manager.complete_act(
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
