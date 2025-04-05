"""Base manager class for SoloGM."""

import logging
from typing import Any, Generic, Optional, Type, TypeVar, Tuple

from sqlalchemy.orm import Session

from sologm.database.session import get_db_context
from sologm.utils.errors import SoloGMError

# Type variables for domain and database models
T = TypeVar('T')  # Domain model type
M = TypeVar('M')  # Database model type

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
            self.logger.debug("Using provided session")
            return self._session, False
        else:
            self.logger.debug("Creating new session context")
            context = get_db_context()
            return context.__enter__(), True
    
    def _convert_to_domain(self, db_model: M) -> T:
        """Convert database model to domain model.
        
        Args:
            db_model: Database model instance
            
        Returns:
            Domain model instance
            
        Raises:
            NotImplementedError: If not implemented in subclass
        """
        raise NotImplementedError("Subclasses must implement _convert_to_domain")
    
    def _convert_to_db_model(self, domain_model: T, db_model: Optional[M] = None) -> M:
        """Convert domain model to database model.
        
        Args:
            domain_model: Domain model instance
            db_model: Optional existing database model to update
            
        Returns:
            Database model instance
            
        Raises:
            NotImplementedError: If not implemented in subclass
        """
        raise NotImplementedError("Subclasses must implement _convert_to_db_model")
    
    def _execute_db_operation(self, operation_name: str, operation: callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a database operation with proper session handling and error handling.
        
        Args:
            operation_name: Name of the operation (for logging)
            operation: Callable that performs the database operation
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            SoloGMError: If the operation fails
        """
        self.logger.debug(f"Executing database operation: {operation_name}")
        session, should_close = self._get_session()
        try:
            result = operation(session, *args, **kwargs)
            if should_close:
                self.logger.debug(f"Committing transaction for {operation_name}")
                session.commit()
            return result
        except Exception as e:
            if should_close:
                self.logger.debug(f"Rolling back transaction for {operation_name}")
                session.rollback()
            self.logger.error(f"Error in {operation_name}: {str(e)}")
            raise SoloGMError(f"Failed to {operation_name}: {str(e)}") from e
        finally:
            if should_close:
                self.logger.debug(f"Closing session for {operation_name}")
                session.close()
