"""Database helpers for CLI commands."""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

import typer

from sologm.database.session import get_db_context
from sologm.utils.errors import SoloGMError

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def with_db_session(f: F) -> F:
    """Decorator to provide a database session to a CLI command.

    This decorator wraps a CLI command function to provide a database session
    and handle transaction management automatically.

    Args:
        f: The CLI command function to wrap

    Returns:
        Wrapped function that handles database session
    """
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            with get_db_context() as session:
                # Add session to kwargs
                kwargs['session'] = session
                return f(*args, **kwargs)
        except SoloGMError as e:
            logger.error(f"Error in database operation: {e}")
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from e
        except Exception as e:
            logger.exception(f"Unexpected error in database operation: {e}")
            typer.echo(f"Unexpected error: {e}", err=True)
            raise typer.Exit(code=1) from e

    return wrapper  # type: ignore
