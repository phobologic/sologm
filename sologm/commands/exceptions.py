"""
Exceptions for the command system.
"""

class CommandError(Exception):
    """Base exception for all command-related errors."""
    pass

class NoHandlerFoundError(CommandError):
    """Raised when no handler is found for a command."""
    pass

class CommandValidationError(CommandError):
    """Raised when command validation fails."""
    pass

class HandlerExecutionError(CommandError):
    """Raised when a handler fails to execute a command."""
    pass

class DuplicateHandlerError(CommandError):
    """Raised when attempting to register a duplicate handler."""
    pass

class InvalidContextError(CommandError):
    """Raised when a command context is invalid or missing required data."""
    pass 