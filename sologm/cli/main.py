"""Main CLI entry point for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm import __version__
from sologm.utils.logger import setup_root_logger

logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="sologm",
    help="Solo RPG Helper command-line application",
    add_completion=True,
)

# Create console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Print version information and exit.

    Args:
        value: Whether the option was provided.
    """
    if value:
        console.print(f"Solo RPG Helper v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug mode with verbose output."
    ),
    version: Optional[bool] = typer.Option(
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
    if config_path:
        from pathlib import Path

        from sologm.utils.config import Config, config

        logger.debug("Loading config from %s", config_path)
        config = Config(Path(config_path))


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typer import Typer

    game_app: Typer
else:
    from sologm.cli.game import game_app  # type: ignore # noqa: F401

from sologm.cli.dice import dice_app  # noqa
from sologm.cli.event import event_app  # noqa
from sologm.cli.oracle import oracle_app  # noqa
from sologm.cli.scene import scene_app  # noqa

# Add subcommands
app.add_typer(game_app, name="game")
app.add_typer(scene_app, name="scene")
app.add_typer(event_app, name="event")
app.add_typer(dice_app, name="dice")
app.add_typer(oracle_app, name="oracle")

if __name__ == "__main__":
    app()
