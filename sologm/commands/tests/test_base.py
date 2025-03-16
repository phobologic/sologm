"""
Tests for the base command infrastructure.
"""
import pytest

from sologm.commands.base import CommandBus
from sologm.commands.exceptions import (
    NoHandlerFoundError,
    DuplicateHandlerError,
    HandlerExecutionError,
    CommandValidationError
)
from sologm.commands.tests.conftest import (
    MockCommand,
    MockFailingCommand,
    MockHandler,
    MockFailingHandler
)

def test_command_bus_registration(command_bus, test_handler):
    """Test registering a handler with the command bus."""
    command_bus.register_handler(test_handler)
    assert len(command_bus._handlers) == 1

def test_duplicate_handler_registration(command_bus, test_handler):
    """Test that registering duplicate handlers raises an error."""
    command_bus.register_handler(test_handler)
    with pytest.raises(DuplicateHandlerError):
        command_bus.register_handler(MockHandler())

def test_command_execution(command_bus, test_handler, context):
    """Test executing a command through the bus."""
    command_bus.register_handler(test_handler)
    command = MockCommand(value="test")
    command.context = context
    result = command_bus.execute(command)
    assert result == "Handled test"

def test_no_handler_found(command_bus, context):
    """Test that executing a command with no handler raises an error."""
    command = MockCommand(value="test")
    command.context = context
    with pytest.raises(NoHandlerFoundError):
        command_bus.execute(command)

def test_handler_execution_error(command_bus, context):
    """Test that handler execution errors are properly wrapped."""
    command_bus.register_handler(MockFailingHandler())
    command = MockCommand(value="test")
    command.context = context
    with pytest.raises(HandlerExecutionError):
        command_bus.execute(command)

def test_command_validation(command_bus, test_handler, context):
    """Test that command validation is performed."""
    command_bus.register_handler(test_handler)
    command = MockCommand(value="")
    command.context = context
    with pytest.raises(CommandValidationError):
        command_bus.execute(command)

def test_command_validation_success(command_bus, test_handler, context):
    """Test that valid commands pass validation."""
    command_bus.register_handler(test_handler)
    command = MockCommand(value="valid")
    command.context = context
    result = command_bus.execute(command)
    assert result == "Handled valid"

def test_failing_command_validation(command_bus, test_handler, context):
    """Test that commands that always fail validation raise an error."""
    command_bus.register_handler(test_handler)
    command = MockFailingCommand()
    command.context = context
    with pytest.raises(CommandValidationError):
        command_bus.execute(command) 