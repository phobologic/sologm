"""Main Typer app for Solo RPG Helper."""

import logging

import typer
from rich.console import Console

logger = logging.getLogger(__name__)

# Create console for rich output
console = Console()


def cleanup_database(*args, **kwargs) -> None:
    """Clean up database resources when the application exits.

    This function is used as a Typer result callback and receives the same arguments
    as the main() function in main.py, but doesn't use them.

    Args:
        *args: Variable positional arguments from Typer (discarded).
        **kwargs: Variable keyword arguments from Typer (discarded).
    """
    from sologm.database.session import DatabaseSession

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
