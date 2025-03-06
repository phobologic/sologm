"""
Database initialization script.
"""
import os
import logging
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.db.config import set_session_factory
from sologm.rpg_helper.models.indexes import create_indexes
from sologm.rpg_helper.db.config import init_db as _init_db

logger = get_logger()

def init_db(db_path: str = None, apply_migrations: bool = True) -> tuple:
    """
    Initialize the database.
    
    Args:
        db_path: Path to the database file. If None, uses the default path.
        apply_migrations: Whether to apply Alembic migrations.
        
    Returns:
        Tuple of (engine, Session)
    """
    # Get the database path
    if db_path is None:
        # Default to a file in the user's home directory
        home_dir = os.path.expanduser("~")
        db_dir = os.path.join(home_dir, ".sologm")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        db_path = os.path.join(db_dir, "rpg_helper.db")
    
    logger.info(
        "Initializing database",
        db_path=db_path
    )
    
    # Create the engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create a session factory
    Session = sessionmaker(bind=engine)
    
    # Set the session factory for the models
    set_session_factory(Session)
    
    # Create indexes
    create_indexes()
    
    # Apply migrations if requested
    if apply_migrations and db_path != ":memory:":
        try:
            # Get the migrations directory
            migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
            
            # Change to the migrations directory
            os.chdir(migrations_dir)
            
            # Apply the migrations
            logger.info(
                "Applying migrations",
                db_path=db_path
            )
            
            subprocess.run(["alembic", "upgrade", "head", "-x", f"db_path={db_path}"], check=True)
            
            logger.info(
                "Migrations applied",
                db_path=db_path
            )
        except Exception as e:
            logger.error(
                "Error applying migrations",
                db_path=db_path,
                error=str(e)
            )
            
            # Fall back to creating all tables
            logger.info(
                "Falling back to creating all tables",
                db_path=db_path
            )
            
            BaseModel.metadata.create_all(engine)
    else:
        # Create all tables
        BaseModel.metadata.create_all(engine)
    
    logger.info(
        "Database initialized",
        db_path=db_path
    )
    
    return engine, Session


if __name__ == "__main__":
    # Initialize the database when run as a script
    init_db()
    print("Database initialized successfully.")

def init_db(db_path=None):
    """
    Initialize the database.
    
    Args:
        db_path: Path to the database file. If None, uses the default path.
        
    Returns:
        Tuple of (engine, Session)
    """
    return _init_db(db_path) 