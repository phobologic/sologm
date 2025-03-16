"""
Base classes for the command system.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Optional, Type, TypeVar

from .exceptions import (
    NoHandlerFoundError,
    DuplicateHandlerError,
    HandlerExecutionError
)

class CommandContext(Protocol):
    """Protocol defining what every context must provide."""
    
    @property
    @abstractmethod
    def workspace_id(self) -> str:
        """Get unique identifier for this workspace/channel."""
        ...
    
    @property
    @abstractmethod
    def user_id(self) -> str:
        """Get the user initiating the command."""
        ...
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Get any interface-specific metadata."""
        ...

@dataclass
class Command:
    """Base class for all commands."""
    _context: Optional[CommandContext] = field(default=None, init=False)

    @property
    def context(self) -> Optional[CommandContext]:
        """Get the command context."""
        return self._context

    @context.setter
    def context(self, value: Optional[CommandContext]) -> None:
        """Set the command context."""
        self._context = value

    def validate(self) -> None:
        """
        Validate the command parameters.
        
        Raises:
            CommandValidationError: If validation fails
        """
        pass

TCommand = TypeVar('TCommand', bound=Command)

class CommandHandler(Protocol[TCommand]):
    """Protocol for command handlers."""
    
    @abstractmethod
    def can_handle(self, command: Command) -> bool:
        """
        Check if this handler can handle the command.
        
        Args:
            command: The command to check
            
        Returns:
            bool: True if this handler can handle the command
        """
        ...

    @abstractmethod
    def handle(self, command: TCommand, context: CommandContext) -> Any:
        """
        Execute the command.
        
        Args:
            command: The command to execute
            context: The context in which to execute the command
            
        Returns:
            Any: The result of the command execution
            
        Raises:
            HandlerExecutionError: If execution fails
        """
        ...

class CommandBus:
    """
    Command bus that routes commands to their handlers.
    """
    
    def __init__(self):
        """Initialize an empty command bus."""
        self._handlers: List[CommandHandler] = []

    def register_handler(self, handler: CommandHandler) -> None:
        """
        Register a new command handler.
        
        Args:
            handler: The handler to register
            
        Raises:
            DuplicateHandlerError: If an equivalent handler is already registered
        """
        # Check for duplicate handlers
        for existing in self._handlers:
            if type(existing) == type(handler):
                raise DuplicateHandlerError(
                    f"Handler of type {type(handler).__name__} is already registered"
                )
        self._handlers.append(handler)

    def execute(self, command: Command) -> Any:
        """
        Execute a command using the appropriate handler.
        
        Args:
            command: The command to execute
            
        Returns:
            Any: The result of the command execution
            
        Raises:
            NoHandlerFoundError: If no handler is found for the command
            HandlerExecutionError: If the handler fails to execute the command
        """
        # Validate command
        command.validate()
        
        # Find handler
        handler = None
        for h in self._handlers:
            if h.can_handle(command):
                handler = h
                break
                
        if not handler:
            raise NoHandlerFoundError(
                f"No handler found for command type {type(command).__name__}"
            )
            
        # Execute command
        try:
            if command.context is None:
                raise HandlerExecutionError("Command context is required")
            return handler.handle(command, command.context)
        except Exception as e:
            raise HandlerExecutionError(
                f"Handler {type(handler).__name__} failed to execute command: {str(e)}"
            ) from e 