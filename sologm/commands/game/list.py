"""
List games command and handler.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from contextlib import contextmanager

from sologm.commands.base import Command, CommandHandler, CommandBus, CommandContext
from sologm.commands.results import CommandResult
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.db.config import get_session, close_session

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
    finally:
        close_session(session)

@dataclass
class ListGamesCommand(Command):
    """Command to list games in a channel."""
    channel_id: str
    workspace_id: str

class ListGamesHandler(CommandHandler[ListGamesCommand]):
    """Handler for listing games."""

    def can_handle(self, command: Command) -> bool:
        """Check if this handler can handle the given command."""
        return isinstance(command, ListGamesCommand)

    def _game_to_dict(self, game: Game) -> Dict[str, Any]:
        """Convert a Game object to a dictionary representation."""
        return {
            "name": game.name,
            "is_active": game.is_active,
            "game_type": game.game_type.value,
            "description": game.description,
            "created_at": game.created_at.isoformat(),
            "members": [member.username for member in game.members] if game.members else []
        }

    def handle(self, command: ListGamesCommand, context: CommandContext) -> CommandResult:
        """Handle the list games command."""
        with session_scope() as session:
            # Get games for channel and ensure they're loaded
            games = session.query(Game).filter_by(
                channel_id=command.channel_id,
                workspace_id=command.workspace_id
            ).all()

            if not games:
                return CommandResult(
                    success=True,
                    message="No games found in current directory.",
                    data={"games": []}
                )
            
            # Ensure relationships are loaded and convert to dicts before session closes
            game_dicts = [self._game_to_dict(game) for game in games]
            
            return CommandResult(
                success=True,
                message=f"Found {len(games)} game(s)",
                data={"games": game_dicts}
            )

def register_handlers(bus: CommandBus) -> None:
    """Register list games command handlers with the command bus."""
    bus.register_handler(ListGamesHandler()) 