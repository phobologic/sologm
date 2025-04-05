"""Database session management for SoloGM."""

from typing import Any, Dict, Optional, Type, TypeVar, Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from sologm.models.base import Base

T = TypeVar('T', bound='DatabaseSession')


class DatabaseSession:
    """Manages database connections and sessions."""

    _instance: Optional['DatabaseSession'] = None
    engine: Engine
    session_factory: Callable[..., Session]
    Session: scoped_session

    @classmethod
    def get_instance(
        cls: Type[T],
        db_url: Optional[str] = None,
        engine: Optional[Engine] = None
    ) -> T:
        """Get or create the singleton instance of DatabaseSession.

        Args:
            db_url: Database URL (e.g., 'postgresql://user:pass@localhost/dbname')
            engine: Pre-configured SQLAlchemy engine instance
        Returns:
            The DatabaseSession instance.
        """
        if cls._instance is None:
            cls._instance = DatabaseSession(db_url=db_url, engine=engine)
        return cls._instance

    def __init__(
        self,
        db_url: str = "sqlite:///sologm.db",
        engine: Optional[Engine] = None,
        **engine_kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the database session.
        
        Args:
            db_url: Database URL (defaults to SQLite in current directory)
            engine: Pre-configured SQLAlchemy engine instance
        """
        # Use provided engine or create one from URL
        self.engine = engine if engine is not None else create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections after 30 minutes
            **engine_kwargs
        )

        # Create session factory with reasonable defaults
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False  # Prevents detached instance errors
        )

        # Create scoped session
        self.Session = scoped_session(self.session_factory)

    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new session.
        Returns:
            A new SQLAlchemy session.
        """
        return self.Session()

    def close_session(self) -> None:
        """Close the current session."""
        self.Session.remove()

    def dispose(self) -> None:
        """Dispose of the engine and all its connections."""
        self.engine.dispose()


# Context manager for session handling
class SessionContext:
    """Context manager for database sessions."""

    session: Optional[Session] = None

    def __init__(self, db_session: Optional[DatabaseSession] = None) -> None:
        """Initialize with optional database session.

        Args:
            db_session: Database session to use (uses singleton if None)
        """
        self._db = db_session or DatabaseSession.get_instance()
        self.session = None

    def __enter__(self) -> Session:
        """Enter context and get a session."""
        self.session = self._db.get_session()
        return self.session

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                exc_val: Optional[BaseException],
                exc_tb: Optional[Any]) -> None:
        """Exit context and close session."""
        if exc_type is not None:
            # An exception occurred, rollback
            self.session.rollback()
        else:
            # No exception, commit
            self.session.commit()

        # Always close the session
        self.session.close()
        self._db.close_session()


# Convenience functions
def initialize_database(
    db_url: Optional[str] = None,
    engine: Optional[Engine] = None
) -> DatabaseSession:
    """Initialize the database and create tables if they don't exist.

    Args:
        db_url: Database URL
        engine: Pre-configured SQLAlchemy engine instance
    Returns:
        The DatabaseSession instance.
    """
    db = DatabaseSession.get_instance(db_url=db_url, engine=engine)
    db.create_tables()
    return db


def get_session() -> Session:
    """Get a database session.
    Returns:
        A new SQLAlchemy session.
    """
    return DatabaseSession.get_instance().get_session()


def get_db_context() -> SessionContext:
    """Get a database session context manager.
    
    Returns:
        A session context manager.
    
    Example:
        with get_db_context() as session:
            user = session.query(User).first()
    """
    return SessionContext()
