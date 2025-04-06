"""Base manager class for SoloGM."""

import logging
from typing import Any, Callable, Generic, Optional, Tuple, TypeVar

from sqlalchemy.orm import Session

# Type variables for domain and database models
T = TypeVar("T")  # Domain model type
M = TypeVar("M")  # Database model type


class BaseManager(Generic[T, M]):
    """Base manager class with database support.

    This class provides common functionality for all managers, including:
    - Database session management
    - Error handling
    - Model conversion

    Attributes:
        logger: Logger instance for this manager
        _session: Optional database session (primarily for testing)
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize with optional session for testing.

        Args:
            session: Optional database session (primarily for testing)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._session = session

    def _get_session(self) -> Tuple[Session, bool]:
        """Get a database session.

        Returns:
            Tuple of (session, should_close)
            - session: The database session to use
            - should_close: Whether the caller should close the session
        """
        if self._session:
            self.logger.debug("Using existing session")
        else:
            self.logger.debug("Getting session from singleton")
            from sologm.database.session import DatabaseSession

            # Store the session for future use
            self._session = DatabaseSession.get_instance().get_session()
        # Always return should_close=False since cleanup is handled at
        # application exit

        return self._session, False

    def _convert_to_domain(self, db_model: M) -> T:
        """Convert database model to domain model.

        Default implementation assumes the database model is the domain model.
        Override this method if your domain model differs from your database model.

        Args:
            db_model: Database model instance

        Returns:
            Domain model instance
        """
        return db_model  # type: ignore

    def _convert_to_db_model(self, domain_model: T, db_model: Optional[M] = None) -> M:
        """Convert domain model to database model.

        Default implementation assumes the domain model is the database model.
        Override this method if your domain model differs from your database model.

        Args:
            domain_model: Domain model instance
            db_model: Optional existing database model to update

        Returns:
            Database model instance
        """
        return domain_model  # type: ignore

    def _execute_db_operation(
        self, operation_name: str, operation: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a database operation with proper session handling.

        This method ensures proper transaction management but preserves
        original exceptions.

        Args:
            operation_name: Name of the operation (for logging)
            operation: Callable that performs the database operation
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Result of the operation
        """
        self.logger.debug(f"Executing database operation: {operation_name}")
        session, _ = self._get_session()
        try:
            result = operation(session, *args, **kwargs)
            self.logger.debug(f"Committing transaction for {operation_name}")
            session.commit()
            return result
        except Exception as e:
            # Only handle the transaction rollback, but re-raise the original exception
            self.logger.debug(f"Rolling back transaction for {operation_name}")
            session.rollback()
            self.logger.error(f"Error in {operation_name}: {str(e)}")
            raise  # Re-raise the original exception
