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
    """Base manager class providing common database operations.

    This class provides common functionality for all managers that interact
    with the database. It requires an active SQLAlchemy session to be passed
    during initialization and uses that session for all database operations.
    It does NOT manage the session lifecycle (commit, rollback, close); that
    is the responsibility of the caller (typically using SessionContext).

    Subclasses should implement domain-specific logic using the provided
    session and helper methods.

    Attributes:
        logger: Logger instance specific to the subclass.
        _session: The SQLAlchemy session provided during initialization.
    """

    def __init__(self, session: Session):
        """Initialize the BaseManager with an active database session.

        Args:
            session: The SQLAlchemy Session instance to use for all database
                     operations performed by this manager instance.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._session = session
        self.logger.debug(
            f"Initialized {self.__class__.__name__} with session ID: {id(self._session)}"
        )

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
        """Execute a database operation using the manager's session.

        This method wraps the actual database logic function (`operation`)
        with logging and basic error handling. It uses the session (`self._session`)
        that was provided when the manager was initialized.

        IMPORTANT: This method does NOT handle transactions (commit/rollback).
        Transaction management should be handled externally, typically by the
        `SessionContext` that created the session.

        Args:
            operation_name: A descriptive name for the operation (for logging).
            operation: The function to execute. It MUST accept the SQLAlchemy
                       session as its first argument.
            *args: Positional arguments to pass to the `operation` function
                   (after the session).
            **kwargs: Keyword arguments to pass to the `operation` function.

        Returns:
            The result returned by the `operation` function.

        Raises:
            Exception: Re-raises any exception caught during the `operation`.
        """
        self.logger.debug(f"Executing DB operation: {operation_name}")
        try:
            # Pass the manager's session to the operation function
            result = operation(self._session, *args, **kwargs)
            self.logger.debug(f"DB operation '{operation_name}' successful")
            return result
        except Exception as e:
            # Log the error but let the SessionContext handle rollback
            self.logger.error(f"Error during DB operation '{operation_name}': {e}")
            raise

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
            entity_id: ID of the entity to retrieve (assumed to be the primary key ID)
            error_class: Exception class to raise if entity not found
            error_message: Optional custom error message

        Returns:
            Entity if found

        Raises:
            error_class: If entity not found
        """
        # Assuming model_class.id refers to the primary key column
        entity = session.query(model_class).filter(model_class.id == entity_id).first()
        if not entity:
            msg = (
                error_message or f"{model_class.__name__} with ID {entity_id} not found"
            )
            raise error_class(msg)
        return entity

    def get_entity_by_identifier(
        self, session: Session, model_class: Type[M], identifier: str
    ) -> Optional[M]:
        """Find an entity by its ID (UUID) or slug.

        Tries to find the entity by ID first, then by slug if the model
        has a 'slug' attribute.

        Args:
            session: The SQLAlchemy session to use.
            model_class: The SQLAlchemy model class to query.
            identifier: The ID (UUID) or slug to search for.

        Returns:
            The entity instance if found, None otherwise.
        """
        # Try finding by ID first (usually primary key)
        entity = session.query(model_class).filter(model_class.id == identifier).first()
        if entity:
            self.logger.debug(f"Found {model_class.__name__} by ID: {identifier}")
            return entity

        # If not found by ID and the model has a 'slug' attribute, try by slug
        if hasattr(model_class, "slug"):
            entity = (
                session.query(model_class)
                .filter(model_class.slug == identifier)
                .first()
            )
            if entity:
                self.logger.debug(f"Found {model_class.__name__} by slug: {identifier}")
                return entity

        # Not found by either
        self.logger.debug(
            f"{model_class.__name__} not found by identifier: {identifier}"
        )
        return None

    def get_entity_by_identifier_or_error(
        self,
        session: Session,
        model_class: Type[M],
        identifier: str,
        error_class: Type[Exception],
        error_message: Optional[str] = None,
    ) -> M:
        """Find an entity by its ID (UUID) or slug, raising an error if not found.

        Args:
            session: The SQLAlchemy session to use.
            model_class: The SQLAlchemy model class to query.
            identifier: The ID (UUID) or slug to search for.
            error_class: The exception class to raise if not found.
            error_message: Custom error message. If None, a default is used.

        Returns:
            The entity instance.

        Raises:
            error_class: If the entity is not found by ID or slug.
        """
        entity = self.get_entity_by_identifier(session, model_class, identifier)
        if not entity:
            if error_message is None:
                error_message = (
                    f"{model_class.__name__} not found with identifier '{identifier}'"
                )
            self.logger.warning(f"Raising error: {error_message}")
            raise error_class(error_message)
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
        """Lazily initialize a manager with the same session.

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

            # Ensure the current manager's session is passed to the new manager
            kwargs["session"] = self._session
            self.logger.debug(
                f"Lazy initializing {class_name} with session ID: {id(kwargs['session'])}"
            )

            setattr(self, attr_name, manager_class(**kwargs))

            # Log the session of the newly created manager to verify propagation
            new_manager = getattr(self, attr_name)
            if hasattr(new_manager, "_session"):
                self.logger.debug(
                    f"Newly created {class_name} has session ID: {id(new_manager._session)}"
                )
            else:
                self.logger.warning(
                    f"Newly created {class_name} does not have a _session attribute."
                )

        return getattr(self, attr_name)
