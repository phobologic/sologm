"""
Game command package.
"""
from sologm.commands.base import CommandBus
from sologm.commands.game.init import register_handlers as register_game_init_handlers
from sologm.commands.game.list import register_handlers as register_game_list_handlers

def register_handlers(bus: CommandBus) -> None:
    """Register all game-related command handlers."""
    register_game_init_handlers(bus)
    register_game_list_handlers(bus) 