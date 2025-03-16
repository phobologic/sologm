"""
Shared test fixtures and helper classes for command tests.
"""
from dataclasses import dataclass
from typing import Any, Dict

import pytest

from sologm.commands.base import Command, CommandHandler, CommandContext
from sologm.commands.exceptions import CommandValidationError

class MockContext:
    """Mock command context for testing."""
    @property
    def workspace_id(self) -> str:
        return "test:workspace"
    
    @property
    def user_id(self) -> str:
        return "test:user"
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return {}

@dataclass
class MockCommand(Command):
    """Mock command implementation for testing."""
    value: str

    def validate(self) -> None:
        if not self.value:
            raise CommandValidationError("Value cannot be empty")

@dataclass
class MockFailingCommand(Command):
    """Command that always fails validation for testing."""
    def validate(self) -> None:
        raise CommandValidationError("Always fails")

class MockHandler(CommandHandler[MockCommand]):
    """Mock command handler implementation for testing."""
    def can_handle(self, command: Command) -> bool:
        return isinstance(command, MockCommand)
    
    def handle(self, command: MockCommand, context: CommandContext) -> str:
        return f"Handled {command.value}"

class MockFailingHandler(CommandHandler[MockCommand]):
    """Handler that raises an exception for testing."""
    def can_handle(self, command: Command) -> bool:
        return isinstance(command, MockCommand)
    
    def handle(self, command: MockCommand, context: CommandContext) -> str:
        raise RuntimeError("Handler failed")

@pytest.fixture
def context():
    """Fixture providing a mock context."""
    return MockContext()

@pytest.fixture
def command_bus():
    """Fixture providing a command bus."""
    from sologm.commands.base import CommandBus
    return CommandBus()

@pytest.fixture
def test_handler():
    """Fixture providing a test handler."""
    return MockHandler() 