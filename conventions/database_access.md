# Database Access

## Session Management
- Use a single session per CLI command with `get_db_context()`
- Keep session open throughout command execution
- Don't explicitly close sessions in managers

## Manager Pattern
- Inherit from `BaseManager[T, M]` with appropriate type parameters
- Accept `session` parameter in constructor
- Pass session to lazy-initialized managers
- Use `self._execute_db_operation(name, func, *args, **kwargs)` for all DB operations
- Define inner functions for database operations

## CLI Command Pattern
```python
@app.command("command_name")
def command_name():
    """Command description."""
    from sologm.database.session import get_db_context
    
    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        manager = Manager(session=session)
        
        # Use manager methods
        result = manager.do_something()
        
        # Display results - session still open for lazy loading
        display_result(console, result)
```

## Database Operations
See [examples/database_access.md](examples/database_access.md) for operation examples.

## Transaction Management
- Let `_execute_db_operation` handle transaction boundaries
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
