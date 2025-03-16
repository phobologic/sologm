"""
Initialize game command and handler.
"""
from dataclasses import dataclass
import traceback
from typing import Optional, Dict, Any

from sqlalchemy.exc import IntegrityError

from sologm.commands.base import Command, CommandHandler, CommandBus, CommandResult
from sologm.commands.contexts import CommandContext
from sologm.rpg_helper.models.game.base import Game, GameType
from sologm.rpg_helper.models.game.errors import ChannelGameExistsError
from sologm.rpg_helper.db.config import get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class InitGameCommand:
    """Command to initialize a new game."""
    name: str
    game_type: str
    channel_id: str
    workspace_id: str
    description: Optional[str] = None
    context: Optional[CommandContext] = None
    
    @property
    def path(self) -> str:
        return "game.init"

class InitGameHandler(CommandHandler[InitGameCommand]):
    """Handler for initializing games."""
    
    def handle(self, command: InitGameCommand, context: CommandContext) -> CommandResult:
        """Handle the init game command."""
        session = get_session()
        try:
            # Check if game system is valid
            try:
                game_type = GameType(command.game_type)
            except ValueError as e:
                logger.error("Invalid game system specified",
                    game_system=command.game_type,
                    valid_systems=[t.value for t in GameType],
                    error=str(e)
                )
                return CommandResult(
                    success=False,
                    message=f"Invalid game system: {command.game_type}. Valid systems are: {', '.join(t.value for t in GameType)}",
                    data={}
                )
            
            # Check if game already exists for channel
            existing_game = Game.get_by_channel(command.channel_id, command.workspace_id)
            if existing_game:
                logger.warning("Game already exists in channel",
                    channel_id=command.channel_id,
                    workspace_id=command.workspace_id,
                    existing_game_id=existing_game.id,
                    existing_game_name=existing_game.name
                )
                return CommandResult(
                    success=False,
                    message=f"A game already exists in this channel: {existing_game.name}",
                    data={}
                )
            
            # Log debug info about game creation
            logger.debug("Creating new game",
                name=command.name,
                game_type=game_type.value,
                channel_id=command.channel_id,
                workspace_id=command.workspace_id,
                description=command.description
            )
            
            # Create game
            game = Game(
                name=command.name,
                game_type=game_type,
                channel_id=command.channel_id,
                workspace_id=command.workspace_id,
                description=command.description
            )
            
            # Add game to session
            session.add(game)
            
            # Add user as member if context has user
            if context and context.user_id:
                logger.debug("Adding user as game member",
                    user_id=context.user_id
                )
                # For now, we'll skip adding members since we need to implement proper User model handling
                # game.members.append(context.user_id)
            
            # Commit changes
            session.commit()
            
            # Log success at debug level since normal output will be via Click
            logger.debug("Game created successfully",
                game_id=game.id,
                name=game.name,
                game_type=game_type.value
            )
            
            # Build success message with game details
            message = [f"Created new game: {game.name}"]
            if game.description:
                message.append(f"Description: {game.description}")
            message.append(f"System: {game.game_type.value}")
            
            return CommandResult(
                success=True,
                message="\n".join(message),
                data={"game_id": game.id}
            )
            
        except IntegrityError as e:
            session.rollback()
            logger.error("Database integrity error during game creation",
                error=str(e),
                error_type="IntegrityError",
                exc_info=True,
                command_data={
                    "name": command.name,
                    "game_type": command.game_type,
                    "channel_id": command.channel_id,
                    "workspace_id": command.workspace_id
                }
            )
            return CommandResult(
                success=False,
                message="Failed to create game due to a database constraint violation",
                data={}
            )
        except Exception as e:
            session.rollback()
            logger.error("Unexpected error during game creation",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
                command_data={
                    "name": command.name,
                    "game_type": command.game_type,
                    "channel_id": command.channel_id,
                    "workspace_id": command.workspace_id
                }
            )
            return CommandResult(
                success=False,
                message=f"Failed to create game: {str(e)}",
                data={}
            )
        finally:
            close_session(session)

def register_handlers(bus: CommandBus) -> None:
    """Register init game command handlers with the command bus."""
    bus.register_handler("game.init", InitGameHandler()) 