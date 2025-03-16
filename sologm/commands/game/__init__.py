"""
Game-related commands package.
"""
from sologm.commands.base import CommandBus
from sologm.commands.game.init import register_handlers as register_init_handlers
from sologm.commands.game.list import register_handlers as register_list_handlers

def register_handlers(bus: CommandBus) -> None:
    """Register all game command handlers with the command bus."""
    register_init_handlers(bus)
    register_list_handlers(bus) 