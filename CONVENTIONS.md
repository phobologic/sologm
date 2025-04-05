# SoloGM Coding Conventions

This document outlines the conventions for coding in the SoloGM project.

## CLI and Database Access Architecture

### CLI Layer Responsibilities
- CLI commands should focus solely on user interaction (input/output)
- CLI commands should not handle database sessions directly
- CLI commands should delegate all business logic to manager classes
- CLI commands should handle exceptions from managers and display user-friendly error messages
- CLI code should never directly interact with database sessions

### Manager Layer Responsibilities
- Managers are responsible for all business logic
- Managers handle their own database session creation and management
- Managers should use `self._execute_db_operation()` for all database operations
- Managers should provide clear, domain-specific error messages

### Database Session Management
- Database sessions should be created and managed by the `BaseManager` class
- The `_execute_db_operation()` method handles session creation, commits, rollbacks, and cleanup
- For testing, managers can accept an optional session parameter in their constructor
- CLI code should never directly interact with database sessions

## Manager Database Access Pattern

- All managers should inherit from `BaseManager[T, M]` with appropriate type parameters
- Accept an optional `session` parameter in the constructor for testing purposes
- Use `self._execute_db_operation(operation_name, operation_func, *args, **kwargs)` for all database operations
- Define database operations as inner functions that take a session as their first parameter
- Let `_execute_db_operation` handle session creation, commits, rollbacks, and cleanup
- Use descriptive operation names for better error messages and logging

## Database Operation Structure

- Define inner functions for database operations with this signature:
  ```python
  def _operation_name(session: Session, param1: Type1, param2: Type2) -> ReturnType:
      # Database operation code
      return result
  ```
- Call these operations using:
  ```python
  result = self._execute_db_operation("operation description", _operation_name, param1, param2)
  ```
- Keep database operations focused on a single responsibility
- Perform validation before executing database operations
- Use appropriate query methods (e.g., `query().filter().first()` for single items)
- Use `session.flush()` when you need generated IDs before committing

## Error Handling

- Let `_execute_db_operation` handle database exceptions
- Catch and wrap exceptions with domain-specific error classes
- Include context in error messages for easier debugging
- Log errors at appropriate levels before raising them
- In CLI commands, catch domain-specific exceptions and display user-friendly messages
- Use `typer.Exit(code)` to terminate CLI commands with appropriate exit codes

## Testing Strategy
- Mock manager classes when testing CLI commands
- Test CLI commands by verifying they call the correct manager methods with the right parameters
- Test CLI output formatting and error handling
- Test managers separately with database session mocks or test databases

## Transaction Management

- Never mix manual and automatic transaction management
- Don't use `session.commit()` or `session.rollback()` in manager methods
- For operations that need to be atomic, group them in a single inner function
- Use `session.flush()` to execute SQL without committing the transaction

## Query Patterns

- Use `session.query(Model).filter(conditions).first()` for single item retrieval
- Use `session.query(Model).filter(conditions).all()` for multiple items
- Use `session.query(Model).filter(conditions).order_by(Model.field).all()` for ordered lists
- Use `session.query(Model).update({Model.field: value})` for bulk updates
- Use appropriate joins for related data retrieval

## Session Lifecycle

- Let `_execute_db_operation` handle session lifecycle in manager methods
- For testing, inject sessions and manage their lifecycle in test fixtures
- Never leave sessions open after operations complete
- Use scoped sessions to ensure thread safety

## Model Design

- All database models should inherit from `Base` and `TimestampMixin`
- Use UUIDs (as strings) for primary keys
- Include a `slug` field for human-readable identifiers where appropriate
- Define validation logic using SQLAlchemy's `@validates` decorator
- Implement static `create()` class methods on models for standardized instantiation
- All columns should use the SQLAlchemy 2.0 ORM Declaritive Models: https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#orm-declarative-models

## Relationship Management

- Use a hybrid approach for defining relationships between models:
  - Define "owning" relationships directly in model classes
  - Define "non-owning" relationships in `relationships.py`
  - A relationship is "owned" by the model that contains the foreign key
  - For many-to-many relationships, choose the more logical owner

- In model classes:
  - Use proper type annotations with `Mapped[Type]` or `Mapped[List[Type]]`
  - Use `TYPE_CHECKING` to avoid circular imports
  - Include docstrings for relationships
  - Define cascade behavior explicitly

- In `relationships.py`:
  - Only define the non-owning side of relationships
  - Import all model classes directly (no TYPE_CHECKING needed)
  - Keep alphabetical ordering of models for easier navigation

- Example of proper relationship definition in a model:
  ```python
  from typing import List, TYPE_CHECKING

  if TYPE_CHECKING:
      from sologm.models.other_model import OtherModel

  class MyModel(Base, TimestampMixin):
      # Foreign key column
      other_id: Mapped[str] = mapped_column(ForeignKey("other_models.id"))

      # Owning relationship
      other_items: Mapped[List["OtherModel"]] = relationship(
          "OtherModel", back_populates="my_model", cascade="all, delete-orphan"
      )
  ```

## Exception Handling Conventions
- Let original exceptions propagate rather than wrapping them in custom exceptions
- Only catch exceptions when you can handle them meaningfully or need to add context
- Use specific exception types in except clauses rather than catching all exceptions
- When creating custom exceptions, inherit from the most specific built-in exception type
- Log exceptions at the appropriate level before re-raising them
- Use context managers (with statements) for resource cleanup rather than try/finally
  where possible
- In manager methods, catch and handle only domain-specific exceptions; let system
  exceptions propagate
- Add contextual information to exceptions using raise ExceptionType("Context: {}".format(details)) from original_exception
- Document which exceptions a function might raise in its docstring
- In CLI commands, catch all expected exceptions and display user-friendly error messages

## Docstring Conventions

- All modules, classes, methods, and functions must have docstrings
- Use Google-style docstring format consistently throughout the codebase
- Module-level docstrings should explain the purpose of the module and any important concepts
- Class docstrings should describe the class purpose, attributes, and usage patterns
- Method/function docstrings must document:
  - Purpose and behavior of the function
  - All parameters with types and descriptions
  - Return values with types and descriptions
  - Exceptions that may be raised with conditions
  - Usage examples for complex functions

- Example of proper method docstring:
  ```python
  def get_active_scene(self, game_id: str) -> Optional[Scene]:
      """Get the active scene for the specified game.

      Args:
          game_id: ID of the game to get the active scene for.

      Returns:
          Scene: Active Scene object if found, None otherwise.

      Raises:
          SceneError: If there's an error retrieving the active scene.
          
      Example:
          ```
          scene_manager = SceneManager()
          active_scene = scene_manager.get_active_scene("game_123")
          ```
      """
  ```

- Keep docstrings focused and concise while providing complete information
- For overridden methods, use `"""See base class."""` if behavior is unchanged
- Document any side effects or state changes in method docstrings

## Logging Conventions

- Use the standard Python `logging` module for all logging
- Create a module-level logger in each file using:
  ```python
  logger = logging.getLogger(__name__)
  ```
- Never use `print()` statements for debugging or information output
- Follow these logging level guidelines:
  - `DEBUG`: Detailed information for debugging and development
  - `INFO`: Confirmation that things are working as expected
  - `WARNING`: Indication that something unexpected happened but the application can continue
  - `ERROR`: Error conditions that prevent a function from working correctly
  - `CRITICAL`: Critical errors that may lead to application failure

- Log the start and completion of significant operations at `INFO` level
- Log all exceptions at `ERROR` level with context information
- Include relevant context in log messages (IDs, operation names)
- Structure log messages consistently:
  - For operations: `"Starting operation_name for resource_type resource_id"`
  - For errors: `"Error in operation_name for resource_type resource_id: error_details"`

- Log sensitive information only at `DEBUG` level and never log credentials
- In database operations, log the operation name before execution at `DEBUG` level
- For manager methods, log entry and exit points at `DEBUG` level
- At application startup, log configuration information at `INFO` level

## Type Annotation Conventions

- Use type annotations for all function definitions, including internal functions
- Import required types from `typing` module at the top of each file
- Use `TypeVar` for generic type parameters in base classes
- For container types, always specify contained type (e.g., `List[str]`, not just `List`)
- Use `Optional[Type]` for parameters and return values that may be `None`
- Use `Union[Type1, Type2]` for values that could be multiple types
- Define custom type aliases for complex types at the module level

- For database models, use SQLAlchemy 2.0 style annotations:
  ```python
  class MyModel(Base, TimestampMixin):
      id: Mapped[str] = mapped_column(primary_key=True)
      name: Mapped[str] = mapped_column(String(255))
      created_at: Mapped[datetime] = mapped_column(default=func.now())
      relation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("other.id"))
  ```

- For callback functions, use `Callable[[ParamType1, ParamType2], ReturnType]`
- For protocol/structural typing, use `Protocol` classes for interface definitions
- Use `Any` sparingly and only when absolutely necessary
- When importing types only for type annotations, use:
  ```python
  from typing import TYPE_CHECKING
  
  if TYPE_CHECKING:
      from other_module import ComplexType
  ```

- For collections with type constraints, use:
  - `Dict[KeyType, ValueType]` for dictionaries
  - `List[ItemType]` for lists
  - `Set[ItemType]` for sets
  - `Tuple[Type1, Type2]` for fixed-size tuples
  - `Tuple[ItemType, ...]` for variable-size tuples

- Use `cast()` when type checkers need help understanding type narrowing
- Document complex type annotations with comments when necessary
