"""Main CLI entry point for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm import __version__
from sologm.cli.dice import dice_app
from sologm.cli.event import event_app
from sologm.cli.game import game_app
from sologm.cli.oracle import oracle_app
from sologm.cli.scene import scene_app
from sologm.utils.logger import setup_root_logger

logger = logging.getLogger(__name__)

# Create console for rich output
console = Console()


def cleanup_database(*args: Optional[list], **kwargs: Optional[dict]) -> None:
    """Clean up database resources when the application exits.

    This function is used as a Typer result callback and receives the same arguments
    as the main() function in main.py, but doesn't use them.

    Args:
        *args: Variable positional arguments from Typer (discarded).
        **kwargs: Variable keyword arguments from Typer (discarded).
    """
    from sologm.database.session import DatabaseSession
    _ = [args, kwargs]

    logger.debug("Cleaning up database resources")
    try:
        db_session = DatabaseSession.get_instance()
        db_session.close_session()
        db_session.dispose()
        logger.debug("Database resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up database resources: {e}")


# Create Typer app with cleanup callback
app = typer.Typer(
    name="sologm",
    help="Solo RPG Helper command-line application",
    add_completion=True,
    no_args_is_help=True,
    result_callback=cleanup_database,
)


def version_callback(value: bool) -> None:
    """Print version information and exit.

    Args:
        value: Whether the option was provided.
    """
    if value:
        console.print(f"Solo RPG Helper v{__version__}")
        raise typer.Exit()


# Register all CLI subcommands
app.add_typer(game_app, name="game", no_args_is_help=True)
app.add_typer(scene_app, name="scene", no_args_is_help=True)
app.add_typer(event_app, name="event", no_args_is_help=True)
app.add_typer(dice_app, name="dice", no_args_is_help=True)
app.add_typer(oracle_app, name="oracle", no_args_is_help=True)


@app.callback()
def main(
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug mode with verbose output."
    ),
    version: Optional[bool] = typer.Option(  # noqa
        None, "--version", callback=version_callback, help="Show version and exit."
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to configuration file."
    ),
) -> None:
    """Solo RPG Helper - A command-line tool for solo roleplaying games.

    Manage games, scenes, and events. Roll dice and interpret oracle results.
    """
    # Set up root logger with debug flag
    setup_root_logger(debug)
    logger.debug("CLI startup with debug=%s", debug)

    # Update config path if provided
    # Initialize config first if custom path provided
    if config_path:
        from pathlib import Path

        from sologm.utils.config import Config

        logger.debug("Loading config from %s", config_path)
        Config.get_instance(Path(config_path))

    # Initialize database
    try:
        from sologm.database import init_db

        # Initialize the database - this will use the singleton pattern internally
        _ = init_db()  # Returns a session, but not needed here.

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        console.print("[bold red]Database initialization failed.[/bold red]")
        console.print(f"Error: {e}")
        console.print("\nPlease configure a database URL using one of these methods:")
        console.print("1. Set the SOLOGM_DATABASE_URL environment variable")
        console.print("2. Add 'database_url' to your config file")
        raise typer.Exit(code=1) from e

    logger.debug("Exiting main without errors.")


if __name__ == "__main__":
    app()
