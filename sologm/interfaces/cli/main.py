"""
Main CLI entry point.
"""
import os
import sys
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.commands.base import CommandBus
from sologm.commands.contexts import CLIContext
from sologm.commands.game import register_handlers as register_game_handlers
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.db.config import set_session_factory
from sologm.rpg_helper.utils.logging import (
    initialize_logging,
    get_level_from_string,
    LogLevel
)

def configure_logging(debug_mode: bool):
    """Configure logging for the CLI.
    
    Args:
        debug_mode: If True, enable debug logging regardless of environment variable.
                   If False, use environment variable or default to WARNING.
    """
    if debug_mode:
        level = LogLevel.DEBUG
    else:
        # Use environment variable if set, otherwise default to WARNING
        level_str = os.getenv("SOLOGM_LOG_LEVEL")
        level = get_level_from_string(level_str) if level_str else LogLevel.WARNING
    
    # Use simple format for CLI output
    initialize_logging(
        format_type="simple",
        level=level,
        datefmt="%H:%M:%S"  # Short time format for CLI
    )

# Create the command bus
command_bus = CommandBus()

# Register command handlers
register_game_handlers(command_bus)

def init_db():
    """Initialize the database."""
    # Create data directory if it doesn't exist
    data_dir = os.path.expanduser("~/.sologm")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create database file
    db_path = os.path.join(data_dir, "sologm.db")
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}")
    BaseModel.metadata.create_all(engine)
    
    # Set up session factory
    factory = sessionmaker(bind=engine)
    set_session_factory(factory)

def get_command_bus() -> CommandBus:
    """Get the global command bus instance."""
    return command_bus

def get_workspace_info() -> tuple[str, str]:
    """Get workspace and channel info for CLI.
    
    Returns:
        Tuple of (workspace_id, channel_id) where:
        - workspace_id is the CLI workspace identifier
        - channel_id is the current directory path
    """
    channel_id = os.getcwd()
    workspace_id = f"cli:{channel_id}"
    return workspace_id, channel_id

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug output')
def cli(debug):
    """SoloGM - A solo roleplaying game manager."""
    configure_logging(debug)
    init_db()

# Import subcommands
from sologm.interfaces.cli.game import game
cli.add_command(game) 