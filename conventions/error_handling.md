# Error Handling

- Let original exceptions propagate rather than wrapping unnecessarily
- Catch exceptions only when adding context or handling meaningfully
- Use specific exception types in `except` clauses
- Add context: `raise ExceptionType("Context") from original_exception`
- In CLI commands, catch expected exceptions with user-friendly messages
- Document raisable exceptions in docstrings
