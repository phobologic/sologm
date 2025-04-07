"""Game management commands for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

from sologm.cli.utils.display import (
    display_game_info,
    display_game_status,
    display_games_table,
)
from sologm.cli.utils.markdown import generate_game_markdown
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.utils.errors import GameError

logger = logging.getLogger(__name__)

# Create game subcommand
game_app = typer.Typer(help="Game management commands")

# Create console for rich output
console = Console()


@game_app.command("create")
def create_game(
    name: str = typer.Option(..., "--name", "-n", help="Name of the game"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the game"
    ),
) -> None:
    """Create a new game."""
    try:
        logger.debug(f"Creating game with name='{name}', description='{description}'")
        game_manager = GameManager()
        game = game_manager.create_game(name=name, description=description)

        console.print("[bold green]Game created successfully![/]")
        console.print(f"Name: {game.name} ({game.id})")
        console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error creating game: {str(e)}[/red]")


@game_app.command("list")
def list_games() -> None:
    """List all games."""
    try:
        logger.debug("Listing all games")
        game_manager = GameManager()
        games = game_manager.list_games()
        active_game = game_manager.get_active_game()
        display_games_table(console, games, active_game)
    except GameError as e:
        console.print(f"[red]Error listing games: {str(e)}[/red]")


@game_app.command("activate")
def activate_game(
    game_id: str = typer.Option(..., "--id", help="ID of the game to activate"),
) -> None:
    """Activate a game."""
    try:
        logger.debug(f"Activating game with id='{game_id}'")
        game_manager = GameManager()
        game = game_manager.activate_game(game_id)

        console.print("[bold green]Game activated successfully![/]")
        console.print(f"Name: {game.name} ({game.id})")
        console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error activating game: {str(e)}[/red]")


@game_app.command("info")
def game_info(
    status: bool = typer.Option(
        False,
        "--status",
        "-s",
        help="Show detailed game status including recent events",
    ),
) -> None:
    """Show information about the active game."""
    try:
        logger.debug("Getting active game info")
        game_manager = GameManager()
        oracle_manager = OracleManager()
        game = game_manager.get_active_game()
        if not game:
            console.print("No active game. Use 'sologm game activate' to set one.")
            return

        scene_manager = SceneManager()
        active_scene = scene_manager.get_active_scene(game.id)

        if status:
            # Get additional status information
            event_manager = EventManager()
            dice_manager = DiceManager()
            recent_events = []
            recent_rolls = []
            if active_scene:
                logger.debug(f"Getting recent events and dice rolls for scene {active_scene.id}")
                recent_events = event_manager.list_events(
                    game.id, active_scene.id, limit=5
                )[:5]  # Ensure we get at most 5 events
                logger.debug(f"Retrieved {len(recent_events)} recent events")

                recent_rolls = dice_manager.get_recent_rolls(active_scene.id, limit=3)
                logger.debug(f"Retrieved {len(recent_rolls)} recent dice rolls for scene {active_scene.id}")
                # Log details of each roll to verify data
                for i, roll in enumerate(recent_rolls):
                    logger.debug(f"Roll {i+1}: {roll.notation} = {roll.total} (ID: {roll.id})")

            logger.debug("Calling display_game_status with recent_rolls parameter")
            display_game_status(
                console,
                game,
                active_scene,
                recent_events,
                scene_manager=scene_manager,
                oracle_manager=oracle_manager,
                recent_rolls=recent_rolls,
            )
        else:
            display_game_info(console, game, active_scene)
    except GameError as e:
        console.print(f"[red]Error getting game info: {str(e)}[/red]")


@game_app.command("edit")
def edit_game(
    game_id: str = typer.Option(
        None, "--id", help="ID of the game to edit (defaults to active game)"
    ),
) -> None:
    """Edit the name and description of a game."""
    try:
        import textwrap

        import yaml

        game_manager = GameManager()

        # Get the game (active or specified)
        game = None
        if game_id:
            game = game_manager.get_game(game_id)
            if not game:
                console.print(f"[red]Game with ID {game_id} not found[/red]")
                raise typer.Exit(1)
        else:
            game = game_manager.get_active_game()
            if not game:
                console.print(
                    "[red]No active game. Specify a game ID or activate a game first.[/red]"
                )
                raise typer.Exit(1)

        # Prepare the text for editing with clear instructions
        original_text = f"""# Edit the game details below
# The description uses YAML's literal block style (|) which preserves all line breaks
# and formatting exactly as you type it.

name: {game.name}
description: |
{textwrap.indent(game.description, "  ")}
"""

        # Use the editor utility
        from sologm.cli.utils.editor import edit_text

        edited_text, was_modified = edit_text(
            original_text,
            console=console,
            message=f"Editing game {game.id}:",
            success_message="Game updated successfully.",
            cancel_message="Game unchanged.",
            error_message="Could not open editor",
        )

        if was_modified:
            try:
                # Remove comment lines before parsing
                yaml_text = "\n".join(
                    [
                        line
                        for line in edited_text.split("\n")
                        if not line.strip().startswith("#")
                    ]
                )

                # Parse the edited YAML
                edited_data = yaml.safe_load(yaml_text)

                # Validate the structure
                if not isinstance(edited_data, dict):
                    console.print(
                        "[bold red]Error:[/] Invalid YAML format. Expected a dictionary."
                    )
                    raise typer.Exit(1)

                # Extract and validate the name
                new_name = edited_data.get("name", "").strip()
                if not new_name:
                    console.print("[bold red]Error:[/] Game name cannot be empty.")
                    raise typer.Exit(1)

                # Extract the description (can be empty)
                new_description = edited_data.get("description", "")

                # Update the game
                updated_game = game_manager.update_game(
                    game_id=game.id,
                    name=new_name,
                    description=new_description,
                )

                console.print("[bold green]Game updated successfully![/]")
                display_game_info(console, updated_game)

            except yaml.YAMLError as e:
                console.print(f"[bold red]Error parsing YAML:[/] {str(e)}")
                raise typer.Exit(1) from e
        else:
            console.print("[yellow]No changes made to the game.[/yellow]")

    except GameError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("dump")
def dump_game(
    game_id: str = typer.Option(
        None, "--id", "-i", help="ID of the game to dump (defaults to active game)"
    ),
    include_metadata: bool = typer.Option(
        False, "--metadata", "-m", help="Include technical metadata in the output"
    ),
) -> None:
    """Export a game with all scenes and events as a markdown document to stdout."""
    try:
        game_manager = GameManager()
        scene_manager = SceneManager()
        event_manager = EventManager()

        # Get the game (active or specified)
        game = None
        if game_id:
            game = game_manager.get_game(game_id)
            if not game:
                console.print(f"[red]Game with ID {game_id} not found[/red]")
                raise typer.Exit(1)
        else:
            game = game_manager.get_active_game()
            if not game:
                console.print(
                    "[red]No active game. Specify a game ID or activate a game first.[/red]"
                )
                raise typer.Exit(1)

        # Generate the markdown content
        markdown_content = generate_game_markdown(
            game, scene_manager, event_manager, include_metadata
        )

        # Print to stdout (without rich formatting)
        print(markdown_content)

    except Exception as e:
        console.print(f"[red]Error exporting game: {str(e)}[/red]")
        raise typer.Exit(1)
