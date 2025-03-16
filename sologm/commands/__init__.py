"""
Command system package.

This package provides the command infrastructure for SoloGM,
including the command bus, contexts, and results handling.
"""

from .base import Command, CommandBus, CommandHandler
from .contexts import CLIContext, SlackContext
from .results import CommandResult
from .exceptions import (
    CommandError,
    NoHandlerFoundError,
    DuplicateHandlerError,
    HandlerExecutionError,
    CommandValidationError,
    InvalidContextError
)

__all__ = [
    'Command',
    'CommandBus',
    'CommandHandler',
    'CLIContext',
    'SlackContext',
    'CommandResult',
    'CommandError',
    'NoHandlerFoundError',
    'DuplicateHandlerError',
    'HandlerExecutionError',
    'CommandValidationError',
    'InvalidContextError'
] 