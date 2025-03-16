"""
Game initialization command and handler.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from sologm.commands.base import Command, CommandHandler, CommandBus, CommandContext
from sologm.commands.contexts import CLIContext, SlackContext
from sologm.commands.results import CommandResult
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.game.errors import ChannelGameExistsError
from sologm.rpg_helper.models.user import User
from sologm.rpg_helper.db.config import get_session, close_session

@dataclass
class InitGameCommand(Command):
    """Command to initialize a new game session."""
    game_system: str  # "standard" or "mythic"
    name: str
    channel_id: str
    workspace_id: str
    description: Optional[str] = None
    user_id: Optional[str] = None  # ID of the user creating the game

@dataclass
class InitGameHandler(CommandHandler[InitGameCommand]):
    """Handler for game initialization."""

    def can_handle(self, command: Command) -> bool:
        """Check if this handler can handle the given command."""
        return isinstance(command, InitGameCommand)

    def handle(self, command: InitGameCommand, context: CommandContext) -> CommandResult:
        """Handle the init game command."""
        try:
            # Map game system to GameType
            try:
                game_type = GameType(command.game_system.lower())
            except ValueError:
                return CommandResult(
                    success=False,
                    message=f"Invalid game system '{command.game_system}'. Must be one of: {', '.join(t.value for t in GameType)}",
                    data={
                        "game_system": command.game_system,
                        "valid_systems": [t.value for t in GameType]
                    }
                )
            
            # Create the game
            session = get_session()
            try:
                # Check if a game already exists for this channel
                existing_game = session.query(Game).filter_by(
                    channel_id=command.channel_id,
                    workspace_id=command.workspace_id
                ).first()
                
                if existing_game:
                    return CommandResult(
                        success=False,
                        message=f"A game already exists in this channel: {existing_game.name}",
                        data={
                            "existing_game_id": existing_game.id,
                            "existing_game_name": existing_game.name,
                            "channel_id": command.channel_id,
                            "workspace_id": command.workspace_id
                        }
                    )
                
                # Create the game
                game = Game(
                    channel_id=command.channel_id,
                    workspace_id=command.workspace_id,
                    name=command.name,
                    description=command.description,
                    game_type=game_type
                )
                session.add(game)
                
                # Add the creator as a member if user_id provided
                if command.user_id:
                    user = session.query(User).filter_by(id=command.user_id).first()
                    if user:
                        game.members.append(user)
                
                # Commit the transaction
                session.commit()
                
                # Build success message
                success_message = (
                    f"Initialized new game:\n"
                    f"Name: {game.name}\n"
                    f"System: {game.game_type.value}\n"
                )
                if game.description:
                    success_message += f"Description: {game.description}\n"
                
                return CommandResult(
                    success=True,
                    message=success_message,
                    data={
                        "game_id": game.id,
                        "name": game.name,
                        "game_type": game.game_type.value,
                        "description": game.description,
                        "channel_id": game.channel_id,
                        "workspace_id": game.workspace_id
                    }
                )
            
            finally:
                close_session(session)
                
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to initialize game: {str(e)}",
                data={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

def register_handlers(bus: CommandBus) -> None:
    """Register game command handlers with the command bus."""
    bus.register_handler(InitGameHandler()) 