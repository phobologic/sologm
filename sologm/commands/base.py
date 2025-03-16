"""
Base command and handler classes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Dict, Optional, Any

from sologm.commands.contexts import CommandContext
from sologm.commands.results import CommandResult

@dataclass
class Command:
    """Base class for all commands."""
    
    @property
    @abstractmethod
    def path(self) -> str:
        """Return the command path for registry lookup."""
        raise NotImplementedError("Command must implement path property")
    
    # Context is optional and should be at the end since it has a default value
    context: Optional[CommandContext] = None

T = TypeVar('T', bound=Command)

class CommandHandler(Generic[T], ABC):
    """Base class for all command handlers."""
    
    @abstractmethod
    def handle(self, command: T, context: CommandContext) -> CommandResult:
        """Handle the command."""
        raise NotImplementedError("Handler must implement handle method")

class HandlerNotFoundError(Exception):
    """Raised when no handler is found for a command."""
    pass

class CommandRegistry:
    """Registry for command handlers."""
    
    def __init__(self):
        self._handlers: Dict[str, Dict[str, Any]] = {}
    
    def register(self, command_path: str, handler: CommandHandler) -> None:
        """Register a handler for a specific command path.
        
        Args:
            command_path: Dot-separated path (e.g., "game.init")
            handler: Handler instance for the command
        """
        parts = command_path.split('.')
        current = self._handlers
        
        # Navigate/create nested dictionaries for each path part
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Register the handler at the final path
        current[parts[-1]] = handler
    
    def get_handler(self, command_path: str) -> Optional[CommandHandler]:
        """Get handler for a command path.
        
        Args:
            command_path: Dot-separated path (e.g., "game.init")
            
        Returns:
            Handler for the command or None if not found
        """
        parts = command_path.split('.')
        current = self._handlers
        
        # Navigate through the path
        for part in parts:
            if part not in current:
                return None
            current = current[part]
        
        # Return handler if we found one, None otherwise
        return current if isinstance(current, CommandHandler) else None

class CommandBus:
    """Command bus for executing commands."""
    
    def __init__(self):
        self._registry = CommandRegistry()
    
    def register_handler(self, command_path: str, handler: CommandHandler) -> None:
        """Register a handler for a command path."""
        self._registry.register(command_path, handler)
    
    def execute(self, command: Command) -> CommandResult:
        """Execute a command using its registered handler.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of command execution
            
        Raises:
            HandlerNotFoundError: If no handler is found for the command
        """
        handler = self._registry.get_handler(command.path)
        if handler is None:
            raise HandlerNotFoundError(f"No handler found for command: {command.path}")
        
        return handler.handle(command, command.context) 