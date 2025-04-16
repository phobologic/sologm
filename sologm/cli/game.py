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
    from sologm.database.session import get_db_context

    try:
        logger.debug(f"Creating game with name='{name}', description='{description}'")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.create_game(name=name, description=description)

            console.print("[bold green]Game created successfully![/]")
            console.print(f"Name: {game.name} ({game.id})")
            console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error creating game: {str(e)}[/red]")


@game_app.command("list")
def list_games() -> None:
    """List all games."""
    from sologm.database.session import get_db_context

    try:
        logger.debug("Listing all games")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
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
    from sologm.database.session import get_db_context

    try:
        logger.debug(f"Activating game with id='{game_id}'")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.activate_game(game_id)

            console.print("[bold green]Game activated successfully![/]")
            console.print(f"Name: {game.name} ({game.id})")
            console.print(f"Description: {game.description}")
    except GameError as e:
        console.print(f"[red]Error activating game: {str(e)}[/red]")


@game_app.command("info")
def game_info() -> None:
    """Show basic information about the active game."""
    from sologm.database.session import get_db_context

    try:
        logger.debug("Getting active game info")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.get_active_game()
            if not game:
                console.print("No active game. Use 'sologm game activate' to set one.")
                return

            # Access scene_manager through the chain
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            active_scene = scene_manager.get_active_scene()

            display_game_info(console, game, active_scene)
    except GameError as e:
        console.print(f"[red]Error getting game info: {str(e)}[/red]")


@game_app.command("status")
def game_status() -> None:
    """Show detailed status of the active game including recent events and dice rolls."""
    from sologm.database.session import get_db_context

    try:
        logger.debug("Getting active game status")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.get_active_game()
            if not game:
                console.print("No active game. Use 'sologm game activate' to set one.")
                return

            # Access scene_manager through the chain
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            active_scene = scene_manager.get_active_scene()

            # Get oracle_manager through the chain
            oracle_manager = scene_manager.oracle_manager

            # Access other managers through the chain
            event_manager = scene_manager.event_manager
            dice_manager = scene_manager.dice_manager

            recent_events = []
            recent_rolls = []
            if active_scene:
                logger.debug(
                    f"Getting recent events and dice rolls for scene {active_scene.id}"
                )
                recent_events = event_manager.list_events(limit=5)[
                    :5
                ]  # Ensure we get at most 5 events
                logger.debug(f"Retrieved {len(recent_events)} recent events")

                recent_rolls = dice_manager.get_recent_rolls(active_scene, limit=3)
                logger.debug(
                    f"Retrieved {len(recent_rolls)} recent dice rolls for "
                    f"scene {active_scene.id}"
                )
                # Log details of each roll to verify data
                for i, roll in enumerate(recent_rolls):
                    logger.debug(
                        f"Roll {i + 1}: {roll.notation} = {roll.total} (ID: {roll.id})"
                    )

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
    except GameError as e:
        console.print(f"[red]Error getting game status: {str(e)}[/red]")


@game_app.command("edit")
def edit_game(
    game_id: str = typer.Option(
        None, "--id", help="ID of the game to edit (defaults to active game)"
    ),
) -> None:
    """Edit the name and description of a game."""
    from sologm.database.session import get_db_context

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

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
                        "[red]No active game. Specify a game ID or activate a "
                        "game first.[/red]"
                    )
                    raise typer.Exit(1)

            # Prepare the data for editing
            game_data = {"name": game.name, "description": game.description}

            # Use the structured editor helper
            from sologm.cli.utils.structured_editor import (
                EditorConfig,
                FieldConfig,
                StructuredEditorConfig,
                edit_structured_data,
            )

            # Create editor configurations
            editor_config = EditorConfig(
                edit_message=f"Editing game {game.id}:",
                success_message="Game updated successfully.",
                cancel_message="Game unchanged.",
                error_message="Could not open editor",
            )

            # Configure the structured editor fields
            structured_config = StructuredEditorConfig(
                fields=[
                    FieldConfig(
                        name="name",
                        display_name="Game Name",
                        help_text="The name of the game",
                        required=True,
                        multiline=False,
                    ),
                    FieldConfig(
                        name="description",
                        display_name="Game Description",
                        help_text="The detailed description of the game",
                        required=False,
                        multiline=True,
                    ),
                ]
            )

            # Use the structured editor
            edited_data, was_modified = edit_structured_data(
                data=game_data,
                console=console,
                config=structured_config,
                context_info=f"Editing game: {game.name} ({game.id})\n",
                editor_config=editor_config,
                is_new=False,  # This is an existing game
            )

            if was_modified:
                # Update the game
                updated_game = game_manager.update_game(
                    game_id=game.id,
                    name=edited_data["name"],
                    description=edited_data["description"],
                )

                console.print("[bold green]Game updated successfully![/]")
                display_game_info(console, updated_game)

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
    from sologm.database.session import get_db_context

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

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
                        "[red]No active game. Specify a game ID or activate a "
                        "game first.[/red]"
                    )
                    raise typer.Exit(1)

            # Access other managers through the chain
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            event_manager = scene_manager.event_manager

            # Generate the markdown content
            markdown_content = generate_game_markdown(
                game, scene_manager, event_manager, include_metadata
            )

            # Print to stdout (without rich formatting)
            print(markdown_content)

    except Exception as e:
        console.print(f"[red]Error exporting game: {str(e)}[/red]")
        raise typer.Exit(1) from e
