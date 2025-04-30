"""Database session management for SoloGM."""

import logging
from typing import Any, Dict, Optional, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from sologm.models.base import Base
from sologm.models.event_source import EventSource

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="DatabaseManager")


class DatabaseManager:
    """Manages database connections, engine configuration, and session creation.

    This class follows the singleton pattern to ensure a single database connection
    pool is used throughout the application. It's responsible for:

    1. Creating and configuring the SQLAlchemy engine with connection pooling
    2. Providing a session factory for creating database sessions
    3. Managing database-wide operations like table creation
    4. Disposing of connections when the application shuts down

    The singleton instance should be initialized once at application startup using
    the `initialize_database()` function or `get_instance()` class method.

    Attributes:
        engine: SQLAlchemy engine instance managing the connection pool
        session: SQLAlchemy scoped_session factory for creating sessions

    Example:
        # At application startup
        db_manager = initialize_database("postgresql://user:pass@localhost/dbname")

        # Getting a session directly (not recommended for application code)
        session = db_manager.get_session()
        try:
            # Use session
            session.commit()
        finally:
            session.close()

        # Preferred approach is to use SessionContext
        with get_db_context() as session:
            # Use session
            # Auto-commits on exit if no exceptions
    """

    _instance: Optional["DatabaseManager"] = None
    engine: Engine
    # Step 1.1: Change session attribute from scoped_session to sessionmaker
    session: sessionmaker

    @classmethod
    def get_instance(
        cls: Type[T], db_url: Optional[str] = None, engine: Optional[Engine] = None
    ) -> "DatabaseManager":
        """Get or create the singleton instance of DatabaseManager.

        Args:
            db_url: Database URL (e.g., 'postgresql://user:pass@localhost/dbname')
            engine: Pre-configured SQLAlchemy engine instance
        Returns:
            The DatabaseManager instance.
        """
        if cls._instance is None:
            cls._instance = DatabaseManager(db_url=db_url, engine=engine)
        return cls._instance

    def __init__(
        self,
        db_url: Optional[str] = None,
        engine: Optional[Engine] = None,
        **engine_kwargs: Dict[str, Any],
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
                **engine_kwargs,
            )
        else:
            logger.error("No engine or db_url provided")
            raise ValueError("Either db_url or engine must be provided")

        # Create session factory and scoped session directly
        logger.debug("Creating session factory")
        session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=True,  # <<< CHANGE THIS TO True
            expire_on_commit=False,  # Prevents detached instance errors
        )
        # Step 1.1: Store the sessionmaker instance directly
        self.session = session_factory

    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        logger.debug("Creating database tables")
        Base.metadata.create_all(self.engine)
        logger.debug("Database tables created")

    def dispose(self) -> None:
        """Dispose of the engine and all its connections."""
        logger.debug("Disposing engine connections")
        self.engine.dispose()


class SessionContext:
    """Context manager for database sessions and transaction management.

    This class provides a clean, Pythonic way to handle database sessions with
    proper transaction boundaries and resource cleanup. It ensures that:

    1. A new session is created when entering the context
    2. The transaction is committed automatically if no exceptions occur
    3. The transaction is rolled back if an exception occurs
    4. The session is properly closed in all cases

    This is the recommended way to use database sessions in application code,
    as it handles all the transaction management and cleanup automatically.

    Attributes:
        session: The SQLAlchemy session (available after entering the context)

    Example:
        # In application code
        from sologm.database.session import get_db_context

        with get_db_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            user.name = "New Name"
            # No need to call commit - happens automatically on exit
            # If an exception occurs, transaction is rolled back
    """

    session: Optional[Session] = None

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        """Initialize with optional database manager.

        Args:
            db_manager: Database manager to use (uses singleton if None)
        """
        self._db = db_manager or DatabaseManager.get_instance()
        self.session = None

    def __enter__(self) -> Session:
        """Enter context and get a session."""
        logger.debug("Entering session context")
        # Step 1.2: Create session using the sessionmaker
        self.session = self._db.session()
        return self.session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Exit context and close session."""
        try:
            if exc_type is not None:
                # An exception occurred, rollback
                logger.debug(f"Exception in session context: {exc_val}. Rolling back")
                self.session.rollback()
            else:
                # No exception, commit *only if the session is active and in a transaction*
                # (i.e., hasn't been rolled back explicitly within the context)
                is_in_transaction = self.session.in_transaction()
                logger.debug(
                    f"Session active: {self.session.is_active}, In transaction: {is_in_transaction}"
                )
                if self.session.is_active and is_in_transaction:
                    logger.debug("Committing session")
                    self.session.commit()
                elif self.session.is_active:
                    logger.debug(
                        "Transaction is not active (likely rolled back), skipping commit."
                    )
                else:
                    logger.debug("Session is not active, skipping commit.")

        finally:
            # Ensure session is always closed
            if self.session:
                logger.debug("Closing session")
                self.session.close()


def _seed_default_event_sources() -> None:
    """Ensure default event sources exist in the database."""
    logger.debug("Checking and seeding default event sources if necessary.")
    default_sources = ["manual", "oracle", "dice"]
    try:
        with get_db_context() as session:
            existing_sources = (
                session.query(EventSource.name)
                .filter(EventSource.name.in_(default_sources))
                .all()
            )
            existing_names = {name for (name,) in existing_sources}
            logger.debug(f"Found existing event sources: {existing_names}")

            missing_sources = [
                name for name in default_sources if name not in existing_names
            ]

            if not missing_sources:
                logger.debug("All default event sources already exist.")
                return

            logger.info(f"Creating missing default event sources: {missing_sources}")
            for source_name in missing_sources:
                source = EventSource.create(name=source_name)
                session.add(source)
                logger.debug(f"Added '{source_name}' event source to session.")

            # Commit happens automatically via SessionContext exit
            logger.info("Default event sources seeded successfully.")

    except Exception as e:
        # Log error but don't prevent application startup if seeding fails
        logger.error(f"Failed to seed default event sources: {e}", exc_info=True)


def get_db_context() -> SessionContext:
    """Get a database session context manager for safe transaction handling.

    This is the recommended way to obtain and use database sessions in application
    code. It returns a context manager that handles session creation, transaction
    boundaries, and resource cleanup automatically.

    Returns:
        A session context manager that yields a SQLAlchemy session when entered

    Example:
        with get_db_context() as session:
            # Perform database operations
            user = session.query(User).filter(User.id == user_id).first()
            user.name = "New Name"
            # Changes are committed automatically when the context exits
            # If an exception occurs, changes are rolled back
    """
    return SessionContext()
