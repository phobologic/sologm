"""Main CLI entry point for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm import __version__
from sologm.cli.act import act_app
from sologm.cli.dice import dice_app
from sologm.cli.event import event_app
from sologm.cli.game import game_app
from sologm.cli.oracle import oracle_app

# --- Added Placeholder Import ---
from sologm.cli.rendering.base import Renderer  # Placeholder imports below
from sologm.cli.scene import scene_app

# --- End Added Placeholder Import ---
from sologm.utils.logger import setup_root_logger

logger = logging.getLogger(__name__)

# Create console for rich output
console = Console()

# Create Typer app with cleanup callback
app = typer.Typer(
    name="sologm",
    help="Solo RPG Helper command-line application",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
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
app.add_typer(act_app, name="act", no_args_is_help=True)


@app.callback()
def main(
    # --- Added ctx parameter ---
    ctx: typer.Context,
    # --- End Added ctx parameter ---
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug mode with verbose output."
    ),
    version: Optional[bool] = typer.Option(  # noqa
        None, "--version", callback=version_callback, help="Show version and exit."
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to configuration file."
    ),
    # --- Added no_ui option ---
    no_ui: bool = typer.Option(
        False, "--no-ui", help="Disable rich UI elements and use Markdown output."
    ),
    # --- End Added no_ui option ---
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

    # --- Added Renderer Selection Logic ---
    # Import renderers here to avoid potential circular imports if they import main
    from sologm.cli.rendering.markdown_renderer import MarkdownRenderer
    from sologm.cli.rendering.rich_renderer import RichRenderer

    selected_renderer: Renderer  # Define type hint
    if no_ui:
        selected_renderer = MarkdownRenderer(console=console)
        logger.debug("MarkdownRenderer selected and instantiated")
    else:
        selected_renderer = RichRenderer(console=console)
        logger.debug("RichRenderer selected and instantiated")

    # Store renderer and console on context object
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["renderer"] = selected_renderer  # Store the instantiated renderer
    ctx.obj["console"] = console  # Store the console instance
    logger.debug("Renderer and console stored in Typer context.")
    # --- End Added Renderer Selection Logic ---

    # Initialize database (now uses the renderer for errors)
    try:
        from sologm.database import init_db

        # Initialize the database - this will use the singleton pattern internally
        _ = init_db()  # Returns a session, but not needed here.

    except Exception as e:
        # Use the selected renderer to display the error
        error_message = f"Database initialization failed: {e}"
        logger.error(error_message)
        # Access renderer from ctx.obj which should be populated by now
        renderer: Renderer = ctx.obj["renderer"]
        renderer.display_error(error_message)
        # Optionally add more guidance using the renderer
        renderer.display_message(
            "\nPlease configure a database URL using one of these methods:\n"
            "1. Set the SOLOGM_DATABASE_URL environment variable\n"
            "2. Add 'database_url' to your config file"
        )
        raise typer.Exit(code=1) from e

    logger.debug("Exiting main without errors.")


if __name__ == "__main__":
    app()
