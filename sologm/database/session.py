"""Database session management for SoloGM."""

import logging
from typing import Any, Dict, Optional, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from sologm.models.base import Base

# Set up logger
logger = logging.getLogger(__name__)

T = TypeVar('T', bound='DatabaseSession')


class DatabaseSession:
    """Manages database connections and sessions."""

    _instance: Optional['DatabaseSession'] = None
    engine: Engine
    session: scoped_session

    @classmethod
    def get_instance(
        cls: Type[T],
        db_url: Optional[str] = None,
        engine: Optional[Engine] = None
    ) -> 'DatabaseSession':
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
        db_url: Optional[str] = None,
        engine: Optional[Engine] = None,
        **engine_kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the database session.

        Args:
            db_url: Database URL (defaults to SQLite in current directory)
            engine: Pre-configured SQLAlchemy engine instance
            engine_kwargs: Additional keyword arguments for engine creation
        """
        # Use provided engine or create one from URL
        if engine is not None:
            logger.debug("Using provided engine")
            self.engine = engine
        elif db_url is not None:
            logger.debug(f"Creating engine with URL: {db_url}")
            self.engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections after 30 minutes
                **engine_kwargs
            )
        else:
            logger.error("No engine or db_url provided")
            raise ValueError("Either db_url or engine must be provided")

        # Create session factory and scoped session directly
        logger.debug("Creating session factory")
        session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False  # Prevents detached instance errors
        )

        # Create scoped session
        logger.debug("Creating scoped session")
        self.session = scoped_session(session_factory)

    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        logger.debug("Creating database tables")
        Base.metadata.create_all(self.engine)
        logger.debug("Database tables created")

    def get_session(self) -> Session:
        """Get a new session.
        Returns:
            A new SQLAlchemy session.
        """
        logger.debug("Getting new session")
        return self.session()

    def close_session(self) -> None:
        """Close the current session."""
        logger.debug("Removing session")
        self.session.remove()

    def dispose(self) -> None:
        """Dispose of the engine and all its connections."""
        logger.debug("Disposing engine connections")
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
        logger.debug("Entering session context")
        self.session = self._db.get_session()
        return self.session

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                exc_val: Optional[BaseException],
                exc_tb: Optional[Any]) -> None:
        """Exit context and close session."""
        if exc_type is not None:
            # An exception occurred, rollback
            logger.debug(f"Exception in session context: {exc_val}. Rolling back")
            self.session.rollback()
        else:
            # No exception, commit
            logger.debug("Committing session")
            self.session.commit()

        # Always close the session
        logger.debug("Closing session")
        self.session.close()
        self._db.close_session()


# Convenience functions
def initialize_database(
    db_url: Optional[str] = None,
    engine: Optional[Engine] = None
) -> DatabaseSession:
    """Initialize the database and create tables if they don't exist.

    Args:
        db_url: Database URL (required if engine is not provided)
        engine: Pre-configured SQLAlchemy engine instance
                (required if db_url is not provided)
    Returns:
        The DatabaseSession instance.

    Raises:
        ValueError: If neither db_url nor engine is provided
    """
    logger.info("Initializing database")
    if db_url is None and engine is None:
        logger.error("No db_url or engine provided to initialize_database")
        raise ValueError("Either db_url or engine must be provided")

    db = DatabaseSession.get_instance(db_url=db_url, engine=engine)
    db.create_tables()
    logger.info("Database initialized successfully")
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
