"""Game management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer

# Console import removed
# Display function imports removed
from sologm.cli.utils.markdown import generate_game_markdown
from sologm.core.game import GameManager
from sologm.utils.errors import GameError

if TYPE_CHECKING:
    from rich.console import Console

    from sologm.cli.rendering.base import Renderer


logger = logging.getLogger(__name__)

# Create game subcommand
game_app = typer.Typer(help="Game management commands")

# console instance removed


@game_app.command("create")
def create_game(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", "-n", help="Name of the game"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the game"
    ),
) -> None:
    """Create a new game."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    try:
        logger.debug(f"Creating game with name='{name}', description='{description}'")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.create_game(name=name, description=description)

            renderer.display_success("Game created successfully!")
            renderer.display_message(f"Name: {game.name} ({game.id})")
            renderer.display_message(f"Description: {game.description}")
    except GameError as e:
        renderer.display_error(f"Error creating game: {str(e)}")
        # Consider adding raise typer.Exit(1) from e


@game_app.command("list")
def list_games(ctx: typer.Context) -> None:
    """List all games."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    try:
        logger.debug("Listing all games")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            games = game_manager.list_games()
            active_game = game_manager.get_active_game()
            renderer.display_games_table(games, active_game)
    except GameError as e:
        renderer.display_error(f"Error listing games: {str(e)}")
        # Consider adding raise typer.Exit(1) from e


@game_app.command("activate")
def activate_game(
    ctx: typer.Context,
    game_id: str = typer.Option(..., "--id", help="ID of the game to activate"),
) -> None:
    """Activate a game."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    try:
        logger.debug(f"Activating game with id='{game_id}'")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            game = game_manager.activate_game(game_id)

            renderer.display_success("Game activated successfully!")
            renderer.display_message(f"Name: {game.name} ({game.id})")
            renderer.display_message(f"Description: {game.description}")
    except GameError as e:
        renderer.display_error(f"Error activating game: {str(e)}")
        # Consider adding raise typer.Exit(1) from e


@game_app.command("info")
def game_info(ctx: typer.Context) -> None:
    """Show basic information about the active game (or latest context
    if none active)."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context

    try:
        logger.debug("Getting game info (using latest context if needed)")
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            # Use the consolidated method to get the latest context
            context_status = game_manager.get_latest_context_status()
            game = context_status["game"]

            if not game:
                renderer.display_warning(
                    "No active game. Use 'sologm game activate' to set one."
                )
                raise typer.Exit(0)  # Exit cleanly if no game context

            # Extract the latest scene (might be None if no acts/scenes exist)
            latest_scene = context_status["latest_scene"]

            logger.debug(
                f"Displaying info for game {game.id}, "
                f"latest scene: {latest_scene.id if latest_scene else 'None'}"
            )
            # Pass the potentially None latest_scene to the display function
            renderer.display_game_info(game, latest_scene)

    except GameError as e:
        # Keep the specific GameError catch
        renderer.display_error(f"Error getting game info: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        # Add a general exception catch like in game_status for robustness
        logger.exception("An unexpected error occurred during game info retrieval.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("status")
def game_status(ctx: typer.Context) -> None:
    """Show detailed status of the active game including recent events and
    dice rolls."""
    renderer: "Renderer" = ctx.obj["renderer"]
    from sologm.database.session import get_db_context
    # SceneError import likely not needed here anymore

    try:
        logger.debug("Getting game status (showing most recent context)")
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            # Use the new consolidated method
            context_status = game_manager.get_latest_context_status()
            game = context_status["game"]

            if not game:  # Check if game retrieval failed within the method
                renderer.display_warning(
                    "No active game. Use 'sologm game activate' to set one."
                )
                raise typer.Exit(0)  # Exit cleanly if no game context

            # Access managers through the chain (still needed for events/rolls/oracle)
            # Note: These managers are initialized within
            # get_latest_context_status if needed,
            # but we might need them directly here too.
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            oracle_manager = scene_manager.oracle_manager
            event_manager = scene_manager.event_manager
            dice_manager = scene_manager.dice_manager

            # Extract context from the dictionary
            latest_act = context_status["latest_act"]
            latest_scene = context_status["latest_scene"]
            is_act_active = context_status["is_act_active"]
            is_scene_active = context_status["is_scene_active"]

            # Fetch recent events and rolls based on the determined scene
            # (active or most recent)
            recent_events = []
            recent_rolls = []
            if latest_scene:
                logger.debug(
                    f"Getting recent events and dice rolls for latest "
                    f"scene {latest_scene.id}"
                )
                recent_events = event_manager.list_events(
                    scene_id=latest_scene.id, limit=5
                )
                logger.debug(f"Retrieved {len(recent_events)} recent events")

                recent_rolls = dice_manager.get_recent_rolls(
                    scene=latest_scene, limit=3
                )
                logger.debug(
                    f"Retrieved {len(recent_rolls)} recent dice rolls for "
                    f"scene {latest_scene.id}"
                )
                for i, roll in enumerate(recent_rolls):
                    logger.debug(
                        f"Roll {i + 1}: {roll.notation} = {roll.total} (ID: {roll.id})"
                    )
            else:
                logger.debug("No latest scene found to fetch events/rolls from.")

            logger.debug("Calling display_game_status with latest context info")
            renderer.display_game_status(
                game,
                latest_act,  # Pass latest act
                latest_scene,  # Pass latest scene
                recent_events,
                scene_manager=scene_manager,
                oracle_manager=oracle_manager,
                recent_rolls=recent_rolls,
                is_act_active=is_act_active,  # Pass act active status
                is_scene_active=is_scene_active,  # Pass scene active status
            )
    # Keep the original GameError catch block
    except GameError as e:
        renderer.display_error(f"Error getting game status: {str(e)}")
        raise typer.Exit(1) from e
    # Add a catch block for other potential errors during fallback
    except Exception as e:
        logger.exception("An unexpected error occurred during game status retrieval.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("edit")
def edit_game(
    ctx: typer.Context,
    game_id: str = typer.Option(
        None, "--id", help="ID of the game to edit (defaults to active game)"
    ),
) -> None:
    """Edit the name and description of a game."""
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]  # Needed for editor
    from sologm.database.session import get_db_context

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            # Get the game (active or specified)
            game = None
            if game_id:
                game = game_manager.get_game(game_id)
                if not game:
                    renderer.display_error(f"Game with ID {game_id} not found")
                    raise typer.Exit(1)
            else:
                game = game_manager.get_active_game()
                if not game:
                    renderer.display_warning(
                        "No active game. Specify a game ID or activate a game first."
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

                renderer.display_success("Game updated successfully!")
                renderer.display_game_info(updated_game)
            else:
                # User cancelled the editor
                renderer.display_warning("Game edit cancelled.")

    except GameError as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("dump")
def dump_game(
    ctx: typer.Context,  # Add context for consistency, though renderer isn't used
    game_id: str = typer.Option(
        None, "--id", "-i", help="ID of the game to dump (defaults to active game)"
    ),
    include_metadata: bool = typer.Option(
        False, "--metadata", "-m", help="Include technical metadata in the output"
    ),
    include_concepts: bool = typer.Option(
        False,
        "--include-concepts",
        "-c",
        help="Include a header explaining game concepts",
    ),
) -> None:
    """Export a game with all scenes and events as a markdown document to stdout."""
    renderer: "Renderer" = ctx.obj["renderer"]  # Get renderer for potential errors
    from sologm.database.session import get_db_context

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            # Get the game (active or specified)
            game = None
            if game_id:
                game = game_manager.get_game(game_id)
                if not game:
                    renderer.display_error(f"Game with ID {game_id} not found")
                    raise typer.Exit(1)
            else:
                game = game_manager.get_active_game()
                if not game:
                    renderer.display_warning(
                        "No active game. Specify a game ID or activate a game first."
                    )
                    raise typer.Exit(1)

            # Access other managers through the chain
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            event_manager = scene_manager.event_manager

            # Make sure the game has its acts loaded
            session.refresh(game)

            # Generate the markdown content
            markdown_content = generate_game_markdown(
                game, scene_manager, event_manager, include_metadata, include_concepts
            )

            # Print to stdout (without rich formatting)
            print(markdown_content)

    except Exception as e:
        renderer.display_error(f"Error exporting game: {str(e)}")
        raise typer.Exit(1) from e
