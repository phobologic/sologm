"""Game management commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING

import typer

from sologm.cli.utils.markdown import generate_game_markdown
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    EditorStatus,  # Import EditorStatus
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
)
from sologm.core.game import GameManager
from sologm.database.session import get_db_context
from sologm.utils.errors import GameError

if TYPE_CHECKING:
    from rich.console import Console

    from sologm.cli.rendering.base import Renderer


logger = logging.getLogger(__name__)


# Create game subcommand
game_app = typer.Typer(help="Game management commands")


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
        raise typer.Exit(1) from e


@game_app.command("list")
def list_games(ctx: typer.Context) -> None:
    """List all games."""
    renderer: "Renderer" = ctx.obj["renderer"]

    try:
        logger.debug("Listing all games")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            games = game_manager.list_games()
            active_game = game_manager.get_active_game()
            renderer.display_games_table(games, active_game)
    except GameError as e:
        renderer.display_error(f"Error listing games: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("activate")
def activate_game(
    ctx: typer.Context,
    game_id: str = typer.Option(
        ..., "--id", help="ID or slug of the game to activate" # Updated help text
    ),
) -> None:
    """Activate a game using its ID or slug.""" # Updated docstring
    renderer: "Renderer" = ctx.obj["renderer"]

    try:
        logger.debug(f"Attempting to activate game with identifier='{game_id}'")
        with get_db_context() as session:
            game_manager = GameManager(session=session)
            # Find the game first using the identifier
            game_to_activate = game_manager.get_game_by_identifier_or_error(game_id)
            # Then pass the actual ID to the activate method
            activated_game = game_manager.activate_game(game_to_activate.id)

            renderer.display_success("Game activated successfully!")
            renderer.display_message(f"Name: {activated_game.name} ({activated_game.id})")
            renderer.display_message(f"Description: {activated_game.description}")
    except GameError as e:
        # Error message from get_game_by_identifier_or_error or activate_game
        renderer.display_error(f"Error activating game: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("info")
def game_info(ctx: typer.Context) -> None:
    """Show basic information about the active game (or latest context
    if none active)."""
    renderer: "Renderer" = ctx.obj["renderer"]

    try:
        logger.debug("Getting game info (using latest context if needed)")
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            # Use the consolidated method to get the latest context
            context_status = game_manager.get_latest_context_status()
            game = context_status["game"]

            if not game:
                renderer.display_warning(
                    "No active game. Use 'sologm game activate' to set one.",
                )
                raise typer.Exit(0)

            latest_scene = context_status["latest_scene"]
            latest_scene_id = latest_scene.id if latest_scene else "None"
            logger.debug(
                f"Displaying info for game {game.id}, latest scene: {latest_scene_id}"
            )
            renderer.display_game_info(game, latest_scene)

    except GameError as e:
        renderer.display_error(f"Error getting game info: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        logger.exception("Unexpected error during game info retrieval.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("status")
def game_status(ctx: typer.Context) -> None:
    """Show detailed status of the active game including recent events and
    dice rolls."""
    renderer: "Renderer" = ctx.obj["renderer"]

    try:
        logger.debug("Getting game status (showing most recent context)")
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            context_status = game_manager.get_latest_context_status()
            game = context_status["game"]

            if not game:
                renderer.display_warning(
                    "No active game. Use 'sologm game activate' to set one.",
                )
                raise typer.Exit(0)

            # Access managers needed for additional data
            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            oracle_manager = scene_manager.oracle_manager
            event_manager = scene_manager.event_manager
            dice_manager = scene_manager.dice_manager

            latest_act = context_status["latest_act"]
            latest_scene = context_status["latest_scene"]
            is_act_active = context_status["is_act_active"]
            is_scene_active = context_status["is_scene_active"]

            recent_events = []
            recent_rolls = []
            if latest_scene:
                scene_id = latest_scene.id
                logger.debug(
                    f"Getting recent events and dice rolls for latest scene {scene_id}"
                )
                recent_events = event_manager.list_events(scene_id=scene_id, limit=5)
                logger.debug(f"Retrieved {len(recent_events)} recent events")

                recent_rolls = dice_manager.get_recent_rolls(
                    scene=latest_scene, limit=3
                )
                logger.debug(
                    f"Retrieved {len(recent_rolls)} recent dice rolls for scene {scene_id}"
                )
                for i, roll in enumerate(recent_rolls):
                    logger.debug(
                        f"Roll {i + 1}: {roll.notation} = {roll.total} (ID: {roll.id})"
                    )
            else:
                logger.debug("No latest scene found to fetch events/rolls from.")

            logger.debug("Calling display_game_status with latest context info")
            renderer.display_game_status(
                game=game,
                latest_act=latest_act,
                latest_scene=latest_scene,
                recent_events=recent_events,
                scene_manager=scene_manager,
                oracle_manager=oracle_manager,
                recent_rolls=recent_rolls,
                is_act_active=is_act_active,
                is_scene_active=is_scene_active,
            )
    except GameError as e:
        renderer.display_error(f"Error getting game status: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        logger.exception("Unexpected error during game status retrieval.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("edit")
def edit_game(
    ctx: typer.Context,
    game_id: str = typer.Option(
        None, "--id", help="ID or slug of the game to edit (defaults to active game)" # Updated help text
    ),
) -> None:
    """Edit the name and description of a game using its ID or slug.""" # Updated docstring
    renderer: "Renderer" = ctx.obj["renderer"]
    console: "Console" = ctx.obj["console"]

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            target_game = None
            if game_id:
                # Find the game first using the identifier
                target_game = game_manager.get_game_by_identifier_or_error(game_id)
            else:
                target_game = game_manager.get_active_game()
                if not target_game:
                    renderer.display_warning(
                        "No active game. Specify a game ID/slug or activate a game first.", # Updated message
                    )
                    raise typer.Exit(1)

            game_data = {"name": target_game.name, "description": target_game.description}

            editor_config = EditorConfig(
                edit_message=f"Editing game {target_game.slug} ({target_game.id}):", # Show slug and ID
                success_message="Game updated successfully.",
                cancel_message="Game unchanged.",
                error_message="Could not open editor",
            )

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
                ],
            )

            # Pass original data for comparison in edit_structured_data
            edited_data, status = edit_structured_data(
                data=game_data,
                console=console,
                config=structured_config,
                context_info=f"Editing game: {target_game.name} ({target_game.id})\n",
                editor_config=editor_config,
                is_new=False,
                original_data_for_comments=game_data, # Pass original for comparison
            )

            # Check status from edit_structured_data
            if status == EditorStatus.SAVED_MODIFIED:
                # Pass the actual ID to the update method
                updated_game = game_manager.update_game(
                    game_id=target_game.id,
                    name=edited_data["name"],
                    description=edited_data["description"],
                )
                renderer.display_success("Game updated successfully!")
                renderer.display_game_info(updated_game)
            elif status == EditorStatus.SAVED_UNCHANGED:
                 renderer.display_message("No changes detected. Game unchanged.")
            elif status == EditorStatus.ABORTED:
                renderer.display_warning("Game edit cancelled.")
            else: # VALIDATION_ERROR or EDITOR_ERROR
                 # Error message should be displayed by edit_structured_data or caught below
                 raise typer.Exit(1)


    except GameError as e:
        renderer.display_error(f"Error editing game: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        # Catch potential errors from edit_structured_data as well
        logger.exception("Unexpected error during game edit.")
        renderer.display_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1) from e


@game_app.command("dump")
def dump_game(
    ctx: typer.Context,
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
    """Export a game with all scenes and events as a markdown document to stdout,
    identifying the game by ID or slug.""" # Updated docstring
    renderer: "Renderer" = ctx.obj["renderer"]  # Needed for error reporting

    try:
        with get_db_context() as session:
            game_manager = GameManager(session=session)

            target_game = None
            if game_id:
                # Find the game first using the identifier
                target_game = game_manager.get_game_by_identifier_or_error(game_id)
            else:
                target_game = game_manager.get_active_game()
                if not target_game:
                    renderer.display_warning(
                        "No active game. Specify a game ID/slug or activate a game first.", # Updated message
                    )
                    raise typer.Exit(1)

            # Ensure related data is loaded if needed by the markdown generator
            # Pass the found game object (target_game)
            session.refresh(target_game) # Refresh the specific game instance

            act_manager = game_manager.act_manager
            scene_manager = act_manager.scene_manager
            event_manager = scene_manager.event_manager

            markdown_content = generate_game_markdown(
                game=target_game, # Pass the found game
                scene_manager=scene_manager,
                event_manager=event_manager,
                include_metadata=include_metadata,
                include_concepts=include_concepts,
            )

            # Print directly to stdout, bypassing the renderer
            print(markdown_content)

    except GameError as e: # Catch GameError specifically
        renderer.display_error(f"Error exporting game: {str(e)}")
        raise typer.Exit(1) from e
    except Exception as e:
        logger.exception("Unexpected error during game dump.")
        renderer.display_error(f"Error exporting game: {str(e)}")
        raise typer.Exit(1) from e
