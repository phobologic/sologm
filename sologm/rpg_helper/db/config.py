"""
Database configuration.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

# Create a base class for all models
Base = declarative_base()

# Global session factory
_session_factory = None

def set_session_factory(factory):
    """Set the global session factory."""
    global _session_factory
    _session_factory = factory

def get_session() -> Session:
    """Get a session from the global session factory."""
    if _session_factory is None:
        raise RuntimeError("Session factory not set. Call set_session_factory first.")
    return _session_factory()

def close_session(session: Session):
    """Close a session."""
    if session:
        session.close()

def init_db(db_path: str = None):
    """
    Initialize the database.
    
    Args:
        db_path: Path to the database file. If None, uses the default path.
        
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
    if db_path == ":memory:":
        engine = create_engine("sqlite:///:memory:", echo=False)
    else:
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Create a session factory
    Session = sessionmaker(bind=engine)
    
    # Set the session factory for the models
    set_session_factory(Session)
    
    # Create all tables
    from sologm.rpg_helper.models import BaseModel
    BaseModel.metadata.create_all(engine)
    
    logger.info(
        "Database initialized",
        db_path=db_path
    )
    
    return engine, Session 