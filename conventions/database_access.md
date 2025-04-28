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
- Let the `SessionContext` (obtained via `get_db_context()`) handle transaction boundaries (commit/rollback) automatically upon exiting the `with` block.
- Managers (and `_execute_db_operation`) **do not** handle commits or rollbacks.
- Use `session.flush()` within manager operations if you need to execute SQL and get generated IDs (like primary keys) *before* the transaction is committed by the context manager.
- Group related database modifications within a single `with get_db_context() as session:` block to ensure they are part of the same atomic transaction.

## Query Patterns
- Single item: `session.query(Model).filter(conditions).first()`
- Multiple items: `session.query(Model).filter(conditions).all()`
- Ordered lists: `session.query(Model).filter().order_by(Model.field).all()`
- Bulk updates: `session.query(Model).update({Model.field: value})`
- Use model hybrid properties in queries when available

See [examples/database_access.md](examples/database_access.md) for query pattern examples.
