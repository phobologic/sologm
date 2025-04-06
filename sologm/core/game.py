"""Game management functionality."""

import logging
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.game import Game
from sologm.utils.errors import GameError

logger = logging.getLogger(__name__)


class GameManager(BaseManager[Game, Game]):
    """Manages game operations."""

    def create_game(self, name: str, description: str) -> Game:
        """Create a new game.

        Args:
            name: Name of the game.
            description: Description of the game.

        Returns:
            The created Game instance.

        Raises:
            GameError: If the game cannot be created.
        """

        def _create_game(session: Session, name: str, description: str) -> Game:
            # Use the create class method from the SQLAlchemy model
            game = Game.create(name=name, description=description)

            # Set this as the only active game
            self._deactivate_all_games(session)
            game.is_active = True

            session.add(game)
            session.flush()  # Flush to get the ID

            logger.debug(f"Created game {game.id}: {name}")
            return game

        try:
            return self._execute_db_operation(
                "create game", _create_game, name, description
            )
        except IntegrityError as e:
            logger.error(f"Failed to create game {name}: {str(e)}")

            error_msg = str(e).lower()

            if "unique constraint" in error_msg:
                if "name" in error_msg:
                    raise GameError(
                        f"A game with the name '{name}' already exists"
                    ) from e
                elif "slug" in error_msg:
                    raise GameError(f"A game with a similar name '{name}'"
                                    f"already exists") from e
                else:
                    raise GameError(
                        "Could not create game due to a uniqueness constraint"
                    ) from e
            else:
                raise GameError(f"Failed to create game: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to create game {name}: {str(e)}")
            raise GameError(f"Failed to create game: {str(e)}") from e

    def _deactivate_all_games(self, session: Session) -> None:
        """Deactivate all games in the database.

        Args:
            session: SQLAlchemy session
        """
        session.query(Game).update({Game.is_active: False})

    def list_games(self) -> List[Game]:
        """List all games in the system.

        Returns:
            List of Game instances.

        Raises:
            GameError: If games cannot be listed.
        """

        def _list_games(session: Session) -> List[Game]:
            games = session.query(Game).order_by(Game.created_at).all()
            logger.debug(f"Listed {len(games)} games")
            return games

        try:
            return self._execute_db_operation("list games", _list_games)
        except Exception as e:
            logger.error(f"Failed to list games: {str(e)}")
            raise GameError(f"Failed to list games: {str(e)}") from e

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a specific game by ID.

        Args:
            game_id: ID of the game to get.

        Returns:
            Game instance if found, None otherwise.

        Raises:
            GameError: If the game cannot be retrieved.
        """

        def _get_game(session: Session, game_id: str) -> Optional[Game]:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.debug(f"Game {game_id} not found")
                return None

            # Ensure relationships are loaded
            if hasattr(game, "scenes"):
                # Access the relationship to ensure it's loaded
                _ = len(game.scenes)

            logger.debug(f"Retrieved game {game_id}")
            return game

        try:
            return self._execute_db_operation("get game", _get_game, game_id)
        except Exception as e:
            raise GameError(f"Failed to get game {game_id}: {str(e)}") from e

    def get_active_game(self) -> Optional[Game]:
        """Get the currently active game.

        Returns:
            Active Game instance if one exists, None otherwise.

        Raises:
            GameError: If the active game cannot be retrieved.
        """

        def _get_active_game(session: Session) -> Optional[Game]:
            game = session.query(Game).filter(Game.is_active == True).first()  # noqa: E712
            if not game:
                logger.debug("No active game set")
                return None

            logger.debug(f"Getting active game: {game.id}")
            return game

        try:
            return self._execute_db_operation("get active game", _get_active_game)
        except Exception as e:
            logger.error(f"Failed to get active game: {str(e)}")
            raise GameError(f"Failed to get active game: {str(e)}") from e

    def activate_game(self, game_id: str) -> Game:
        """Set a game as active.

        Args:
            game_id: ID of the game to activate.

        Returns:
            The activated Game instance.

        Raises:
            GameError: If the game cannot be activated.
        """

        def _activate_game(session: Session, game_id: str) -> Game:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.error(f"Cannot activate nonexistent game: {game_id}")
                raise GameError(f"Game not found: {game_id}")

            # Deactivate all games first
            self._deactivate_all_games(session)

            # Activate the requested game
            game.is_active = True

            logger.debug(f"Activated game: {game_id}")
            return game

        try:
            return self._execute_db_operation("activate game", _activate_game, game_id)
        except Exception as e:
            logger.error(f"Failed to activate game {game_id}: {str(e)}")
            raise GameError(f"Failed to activate game {game_id}: {str(e)}") from e
