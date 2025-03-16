"""
Main CLI entry point.
"""
import os
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.commands.base import CommandBus
from sologm.commands.contexts import CLIContext
from sologm.commands.game import register_handlers as register_game_handlers
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.db.config import set_session_factory

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

@click.group()
def cli():
    """SoloGM - A solo roleplaying game manager."""
    init_db()

# Import subcommands
from sologm.interfaces.cli.game import game
cli.add_command(game) 