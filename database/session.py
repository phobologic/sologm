"""Database session management for SoloGM."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from sologm.models.base import Base


class DatabaseSession:
    """Manages database connections and sessions."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, db_path=None):
        """Get or create the singleton instance of DatabaseSession.
        
        Args:
            db_path: Optional path to the database file.
            
        Returns:
            The DatabaseSession instance.
        """
        if cls._instance is None:
            cls._instance = DatabaseSession(db_path)
        return cls._instance
    
    def __init__(self, db_path=None):
        """Initialize the database session.
        
        Args:
            db_path: Optional path to the database file.
                     Defaults to ~/.sologm/sologm.db
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.sologm/sologm.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def create_tables(self):
        """Create all tables defined in the models."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new session.
        
        Returns:
            A new SQLAlchemy session.
        """
        return self.Session()
    
    def close_session(self):
        """Close the current session."""
        self.Session.remove()


# Convenience functions
def initialize_database(db_path=None):
    """Initialize the database and create tables if they don't exist.
    
    Args:
        db_path: Optional path to the database file.
        
    Returns:
        The DatabaseSession instance.
    """
    db = DatabaseSession.get_instance(db_path)
    db.create_tables()
    return db


def get_session():
    """Get a database session.
    
    Returns:
        A new SQLAlchemy session.
    """
    return DatabaseSession.get_instance().get_session()
