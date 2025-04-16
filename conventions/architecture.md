# Architecture

## CLI Layer

- Focus solely on user interaction (input/output)
- Delegate all business logic to manager classes
- Handle exceptions with user-friendly messages
- Use `get_db_context()` to manage database sessions
- Initialize managers with the session from context

## Manager Layer

- Handle all business logic
- Accept session in constructor
- Pass session to lazy-initialized managers
- Use `self._execute_db_operation()` for all DB operations
- Provide clear domain-specific error messages

## Session Management

- One session per CLI command
- Keep session open throughout command execution
- Use context manager pattern with `get_db_context()`
- Close session automatically when command completes
