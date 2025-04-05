# SoloGM Database Conventions

This document outlines the conventions for database usage in the SoloGM project, focusing on how we interact with the database from CLI commands and Manager classes.

## CLI Database Access Pattern

- Always use the `@with_db_session` decorator for CLI commands that need database access
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
- Define relationships in the central `relationships.py` file, not in individual model files

## Relationships

- Define one-to-many relationships with appropriate cascade behavior
- Use `back_populates` instead of `backref` for explicit bidirectional relationships
- Set `cascade="all, delete-orphan"` for parent-child relationships where appropriate
- Define foreign keys in the child model, not in the relationship definition
