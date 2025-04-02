"""Main CLI entry point for Solo RPG Helper."""

import sys
from typing import Optional

import typer
from rich.console import Console

from sologm import __version__
from sologm.utils.config import config
from sologm.utils.errors import SoloGMError
from sologm.utils.logger import setup_root_logger

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

    # Update config path if provided
    if config_path:
        from pathlib import Path
        from sologm.utils.config import Config

        global config
        config = Config(Path(config_path))


def handle_errors(func):
    """Decorator to handle errors in CLI commands.

    Args:
        func: Function to decorate.

    Returns:
        Decorated function.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SoloGMError as e:
            if config.get("debug", False):
                console.print(f"[bold red]Error:[/] {str(e)}")
                import traceback

                console.print(traceback.format_exc())
                sys.exit(1)
            else:
                console.print(f"[bold red]Error:[/] {str(e)}")
                console.print("Run with --debug for more information.")
                sys.exit(1)
        except Exception as e:
            if config.get("debug", False):
                console.print(f"[bold red]Unexpected error:[/] {str(e)}")
                import traceback

                console.print(traceback.format_exc())
                sys.exit(1)
            else:
                console.print("[bold red]An unexpected error occurred.[/]")
                console.print("Run with --debug for more information.")
                sys.exit(1)

    return wrapper


# Import subcommands
from sologm.cli.game import game_app
import sologm.cli.scene  # noqa
import sologm.cli.event  # noqa
import sologm.cli.oracle  # noqa
import sologm.cli.dice  # noqa

# Register command groups
app.add_typer(game_app, name="game", help="Game management commands")


if __name__ == "__main__":
    app()
