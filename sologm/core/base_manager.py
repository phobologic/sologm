"""Base manager class for SoloGM."""

import importlib
import logging
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from sqlalchemy import asc, desc
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
    - Common utility methods for entity operations

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

    def get_entity_or_error(
        self,
        session: Session,
        model_class: Type[M],
        entity_id: str,
        error_class: Type[Exception],
        error_message: Optional[str] = None,
    ) -> M:
        """Get an entity by ID or raise an error if not found.

        Args:
            session: Database session
            model_class: Model class to query
            entity_id: ID of the entity to retrieve
            error_class: Exception class to raise if entity not found
            error_message: Optional custom error message

        Returns:
            Entity if found

        Raises:
            error_class: If entity not found
        """
        entity = session.query(model_class).filter(model_class.id == entity_id).first()
        if not entity:
            msg = (
                error_message or f"{model_class.__name__} with ID {entity_id} not found"
            )
            raise error_class(msg)
        return entity

    def list_entities(
        self,
        model_class: Type[M],
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Union[str, List[str]]] = None,
        order_direction: str = "asc",
        limit: Optional[int] = None,
    ) -> List[M]:
        """List entities with optional filtering, ordering, and limit.

        Args:
            model_class: Model class to query
            filters: Optional dictionary of attribute:value pairs to filter by
            order_by: Optional attribute(s) to order by
            order_direction: Direction to order ("asc" or "desc")
            limit: Optional maximum number of results to return

        Returns:
            List of entities matching the criteria
        """

        def _list_operation(session: Session) -> List[M]:
            query = session.query(model_class)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query = query.filter(getattr(model_class, key) == value)

            # Apply ordering
            if order_by:
                if isinstance(order_by, str):
                    order_attrs = [order_by]
                else:
                    order_attrs = order_by

                for attr in order_attrs:
                    direction_func = asc if order_direction == "asc" else desc
                    query = query.order_by(direction_func(getattr(model_class, attr)))

            # Apply limit
            if limit:
                query = query.limit(limit)

            return query.all()

        return self._execute_db_operation(
            f"list {model_class.__name__}", _list_operation
        )

    def _lazy_init_manager(
        self, attr_name: str, manager_class_path: str, **kwargs
    ) -> Any:
        """Lazily initialize a manager.

        Args:
            attr_name: Attribute name to store the manager instance
            manager_class_path: Fully qualified path to the manager class
            **kwargs: Additional arguments to pass to the manager constructor

        Returns:
            Initialized manager instance
        """
        if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
            module_path, class_name = manager_class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            manager_class = getattr(module, class_name)

            # Always pass the session
            kwargs["session"] = self._session

            setattr(self, attr_name, manager_class(**kwargs))

        return getattr(self, attr_name)

