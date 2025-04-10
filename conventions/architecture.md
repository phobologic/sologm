# Architecture

## CLI Layer
- Focus solely on user interaction (input/output)
- Delegate all business logic to manager classes
- Handle exceptions with user-friendly messages
- Never interact directly with database sessions

## Manager Layer
- Handle all business logic
- Manage database sessions using `BaseManager`
- Use `self._execute_db_operation()` for all DB operations
- Provide clear domain-specific error messages
