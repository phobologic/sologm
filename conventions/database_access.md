# Database Access

## Manager Pattern
- Inherit from `BaseManager[T, M]` with appropriate type parameters
- Use constructor parameter `session` (optional) for testing
- Use `self._execute_db_operation(name, func, *args, **kwargs)` for all DB operations
- Define inner functions for database operations

## Database Operations

See [examples/database_access.md](examples/database_access.md) for operation examples.

## Transaction Management
- Let `_execute_db_operation` handle session lifecycle
- Don't use `session.commit()` or `session.rollback()` directly
- Use `session.flush()` to execute SQL without committing
- Group atomic operations in single inner functions

## Query Patterns
- Single item: `session.query(Model).filter(conditions).first()`
- Multiple items: `session.query(Model).filter(conditions).all()`
- Ordered lists: `session.query(Model).filter().order_by(Model.field).all()`
- Bulk updates: `session.query(Model).update({Model.field: value})`
- Use model hybrid properties in queries when available

See [examples/database_access.md](examples/database_access.md) for query pattern examples.
