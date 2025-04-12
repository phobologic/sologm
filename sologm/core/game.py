"""Game management functionality."""

import logging
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.game import Game
from sologm.models.utils import slugify
from sologm.utils.errors import GameError

logger = logging.getLogger(__name__)


class GameManager(BaseManager[Game, Game]):
    """Manages game operations."""

    def create_game(self, name: str, description: str, is_active: bool = True) -> Game:
        """Create a new game.

        Args:
            name: Name of the game.
            description: Description of the game.
            is_active: Whether the game should be active (defaults to True).

        Returns:
            The created Game instance.

        Raises:
            GameError: If the game cannot be created.
        """

        def _create_game(
            session: Session, name: str, description: str, is_active: bool
        ) -> Game:
            # Use the create class method from the SQLAlchemy model
            game = Game.create(name=name, description=description)

            # Set active status
            if is_active:
                self._deactivate_all_games(session)
                game.is_active = True
            else:
                game.is_active = False

            session.add(game)
            session.flush()  # Flush to get the ID

            logger.debug(f"Created game {game.id}: {name}")
            return game

        try:
            return self._execute_db_operation(
                "create game", _create_game, name, description, is_active
            )
        except IntegrityError as e:
            self._handle_integrity_error(e, "create", name)
        except Exception as e:
            logger.error(f"Failed to create game {name}: {str(e)}")
            raise GameError(f"Failed to create game: {str(e)}") from e

    def _handle_integrity_error(
        self, error: IntegrityError, operation: str, name: str
    ) -> None:
        """Handle integrity errors consistently.

        Args:
            error: The integrity error
            operation: The operation being performed (create/update)
            name: The name that caused the error

        Raises:
            GameError: With a user-friendly message
        """
        logger.error(f"Failed to {operation} game {name}: {str(error)}")
        error_msg = str(error).lower()

        if "unique constraint" in error_msg:
            if "name" in error_msg:
                raise GameError(
                    f"A game with the name '{name}' already exists"
                ) from error
            elif "slug" in error_msg:
                raise GameError(
                    f"A game with a similar name '{name}' already exists"
                ) from error
            else:
                raise GameError(
                    f"Could not {operation} game due to a uniqueness constraint"
                ) from error
        else:
            raise GameError(f"Failed to {operation} game: {str(error)}") from error

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

    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """Get a specific game by ID.

        Args:
            game_id: ID of the game to get.

        Returns:
            Game instance if found, None otherwise.

        Raises:
            GameError: If the game cannot be retrieved.
        """

        def _get_game_by_id(session: Session, game_id: str) -> Optional[Game]:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.debug(f"Game {game_id} not found")
                return None

            logger.debug(f"Retrieved game {game_id}")
            return game

        try:
            return self._execute_db_operation(
                "get game by id", _get_game_by_id, game_id
            )
        except Exception as e:
            raise GameError(f"Failed to get game {game_id}: {str(e)}") from e

    def get_game_by_slug(self, slug: str) -> Optional[Game]:
        """Get a specific game by slug.

        Args:
            slug: Slug of the game to get.

        Returns:
            Game instance if found, None otherwise.

        Raises:
            GameError: If the game cannot be retrieved.
        """

        def _get_game_by_slug(session: Session, slug: str) -> Optional[Game]:
            game = session.query(Game).filter(Game.slug == slug).first()
            if not game:
                logger.debug(f"Game with slug '{slug}' not found")
                return None

            logger.debug(f"Retrieved game with slug '{slug}'")
            return game

        try:
            return self._execute_db_operation(
                "get game by slug", _get_game_by_slug, slug
            )
        except Exception as e:
            raise GameError(f"Failed to get game with slug '{slug}': {str(e)}") from e

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

            # Always deactivate all games first
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

    def deactivate_game(self, game_id: str) -> Game:
        """Set a game as inactive.

        Args:
            game_id: ID of the game to deactivate

        Returns:
            The deactivated Game instance

        Raises:
            GameError: If the game cannot be deactivated
        """

        def _deactivate_game(session: Session, game_id: str) -> Game:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.error(f"Cannot deactivate nonexistent game: {game_id}")
                raise GameError(f"Game not found: {game_id}")

            game.is_active = False

            logger.debug(f"Deactivated game: {game_id}")
            return game

        try:
            return self._execute_db_operation(
                "deactivate game", _deactivate_game, game_id
            )
        except Exception as e:
            logger.error(f"Failed to deactivate game {game_id}: {str(e)}")
            raise GameError(f"Failed to deactivate game {game_id}: {str(e)}") from e

    def update_game(
        self,
        game_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Game:
        """Update a game's properties.

        Args:
            game_id: ID of the game to update
            name: New name for the game (if None, name won't be updated)
            description: New description for the game (if None, description won't be updated)

        Returns:
            The updated Game instance.

        Raises:
            GameError: If the game cannot be updated.
        """

        def _update_game(
            session: Session,
            game_id: str,
            name: Optional[str],
            description: Optional[str],
        ) -> Game:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.error(f"Cannot update nonexistent game: {game_id}")
                raise GameError(f"Game not found: {game_id}")

            # Update the game properties if provided
            if name is not None:
                old_name = game.name
                game.name = name

                # Only update the slug if the name changed
                if old_name != name:
                    game.slug = slugify(name)

            if description is not None:
                game.description = description

            logger.debug(f"Updated game: {game_id}")
            return game

        try:
            return self._execute_db_operation(
                "update game", _update_game, game_id, name, description
            )
        except IntegrityError as e:
            self._handle_integrity_error(e, "update", name or "")
        except Exception as e:
            logger.error(f"Failed to update game {game_id}: {str(e)}")
            raise GameError(f"Failed to update game: {str(e)}") from e

    def delete_game(self, game_id: str) -> bool:
        """Delete a game.

        Args:
            game_id: ID of the game to delete

        Returns:
            True if the game was deleted, False otherwise

        Raises:
            GameError: If there was an error during deletion
        """

        def _delete_game(session: Session, game_id: str) -> bool:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.debug(f"Cannot delete nonexistent game: {game_id}")
                return False

            session.delete(game)
            logger.debug(f"Deleted game: {game_id}")
            return True

        try:
            return self._execute_db_operation("delete game", _delete_game, game_id)
        except Exception as e:
            logger.error(f"Failed to delete game {game_id}: {str(e)}")
            raise GameError(f"Failed to delete game: {str(e)}") from e
