# SoloGM Coding Conventions

This document outlines the conventions for coding in the SoloGM project.

## CLI Database Access Pattern

- Always use the `@with_db_session` (from `sologm.cli.db_helpers`)decorator for CLI commands that need database access
- Never create database sessions directly in CLI functions
- Access the session via the injected `session` parameter
- Delegate all database operations to manager classes
- Handle exceptions from managers and display user-friendly error messages
- Don't commit or rollback transactions in CLI code; let the decorator handle it

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

- Let `with_db_session` decorator handle session lifecycle in CLI commands
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
