# Database Access

## Manager Pattern
- Inherit from `BaseManager[T, M]` with appropriate type parameters
- Use constructor parameter `session` (optional) for testing
- Use `self._execute_db_operation(name, func, *args, **kwargs)` for all DB operations
- Define inner functions for database operations

## Database Operations
```python
# Define operation as inner function
def _operation_name(session: Session, param1: Type1) -> ReturnType:
    # Operation code
    return result

# Execute operation
result = self._execute_db_operation("operation description", _operation_name, param1)
```

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
