"""
List games command and handler.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from sologm.commands.base import Command, CommandHandler, CommandBus, CommandResult
from sologm.commands.contexts import CommandContext
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.db.config import get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger(__name__)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
    finally:
        close_session(session)

@dataclass
class ListGamesCommand:
    """Command to list games in a channel."""
    channel_id: str
    workspace_id: str
    context: Optional[CommandContext] = None
    
    @property
    def path(self) -> str:
        return "game.list"

class ListGamesHandler(CommandHandler[ListGamesCommand]):
    """Handler for listing games."""
    
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
        try:
            with session_scope() as session:
                logger.debug("Querying games",
                    channel_id=command.channel_id,
                    workspace_id=command.workspace_id
                )
                
                # Get games for channel
                games = session.query(Game).filter_by(
                    channel_id=command.channel_id,
                    workspace_id=command.workspace_id
                ).all()
                
                # Convert to dicts before session closes
                game_dicts = [self._game_to_dict(game) for game in games]
                
                logger.debug("Found games",
                    count=len(games),
                    game_names=[g.name for g in games]
                )
                
                if not games:
                    return CommandResult(
                        success=True,
                        message="No games found in current directory.",
                        data={"games": []}
                    )
                
                return CommandResult(
                    success=True,
                    message="Games found in current directory.",
                    data={"games": game_dicts}
                )
                
        except Exception as e:
            logger.error("Error listing games",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
                channel_id=command.channel_id,
                workspace_id=command.workspace_id
            )
            return CommandResult(
                success=False,
                message=f"Failed to list games: {str(e)}"
            )

def register_handlers(bus: CommandBus) -> None:
    """Register list games command handlers with the command bus."""
    bus.register_handler("game.list", ListGamesHandler()) 