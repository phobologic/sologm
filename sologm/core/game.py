"""Game management functionality."""

import logging
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.game import Game
from sologm.models.utils import slugify
from sologm.utils.errors import GameError

if TYPE_CHECKING:
    from sologm.core.act import ActManager


logger = logging.getLogger(__name__)


class GameManager(BaseManager[Game, Game]):
    """Manages game operations."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize the game manager.

        Args:
            session: Optional session for testing or CLI command injection
        """
        super().__init__(session=session)
        self._act_manager: Optional["ActManager"] = None

    # Child manager access
    @property
    def act_manager(self) -> "ActManager":
        """Lazy-initialize act manager."""
        return self._lazy_init_manager(
            "_act_manager", "sologm.core.act.ActManager", game_manager=self
        )

    def create_game(self, name: str, description: str, is_active: bool = True) -> Game:
        """Create a new game.

        Args:
            name: Name of the game.
            description: Description of the game.
            is_active: Whether the game should be active (defaults to True).

        Returns:
            The created Game instance.

        Raises:
            GameError: If the game cannot be created or a game with the same name exists.
        """
        logger.debug(f"Creating game: name='{name}', is_active={is_active}")

        def _create_game(session: Session) -> Game:
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

            return game

        try:
            game = self._execute_db_operation("create game", _create_game)
            logger.debug(f"Created game: {game.id}, name='{game.name}'")
            return game
        except IntegrityError as e:
            self._handle_integrity_error(e, "create", name)

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
        logger.debug("Deactivating all games")
        session.query(Game).update({Game.is_active: False})

    def list_games(self) -> List[Game]:
        """List all games in the system.

        Returns:
            List of Game instances.
        """
        logger.debug("Listing all games")
        games = self.list_entities(Game, order_by="created_at")
        logger.debug(f"Listed {len(games)} games")
        return games

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID.

        Args:
            game_id: ID of the game to get.

        Returns:
            Game instance if found, None otherwise.

        Raises:
            GameError: If the game cannot be retrieved.
        """
        logger.debug(f"Getting game: {game_id}")
        return self.get_game_by_id(game_id)

    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """Get a specific game by ID.

        Args:
            game_id: ID of the game to get.

        Returns:
            Game instance if found, None otherwise.
        """
        logger.debug(f"Getting game by ID: {game_id}")

        def _get_game(session: Session) -> Optional[Game]:
            return session.query(Game).filter(Game.id == game_id).first()

        game = self._execute_db_operation(f"get game {game_id}", _get_game)
        logger.debug(f"Retrieved game: {game.id if game else 'None'}")
        return game

    def get_game_by_slug(self, slug: str) -> Optional[Game]:
        """Get a specific game by slug.

        Args:
            slug: Slug of the game to get.

        Returns:
            Game instance if found, None otherwise.
        """
        logger.debug(f"Getting game by slug: {slug}")

        def _get_game(session: Session) -> Optional[Game]:
            return session.query(Game).filter(Game.slug == slug).first()

        game = self._execute_db_operation(f"get game by slug {slug}", _get_game)
        logger.debug(f"Retrieved game by slug: {game.id if game else 'None'}")
        return game

    def get_active_game(self) -> Optional[Game]:
        """Get the currently active game.

        Returns:
            Active Game instance if one exists, None otherwise.
        """
        logger.debug("Getting active game")
        games = self.list_entities(Game, filters={"is_active": True}, limit=1)
        game = games[0] if games else None

        if not game:
            logger.debug("No active game found")
        else:
            logger.debug(f"Found active game: {game.id}")

        return game

    def activate_game(self, game_id: str) -> Game:
        """Set a game as active.

        Args:
            game_id: ID of the game to activate.

        Returns:
            The activated Game instance.

        Raises:
            GameError: If the game doesn't exist
        """
        logger.debug(f"Activating game: {game_id}")

        def _activate_game(session: Session) -> Game:
            # Use get_entity_or_error instead of manual query and check
            game = self.get_entity_or_error(
                session, Game, game_id, GameError, f"Game not found: {game_id}"
            )

            # Always deactivate all games first
            self._deactivate_all_games(session)

            # Activate the requested game
            game.is_active = True

            return game

        game = self._execute_db_operation("activate game", _activate_game)
        logger.debug(f"Activated game: {game.id}")
        return game

    def deactivate_game(self, game_id: str) -> Game:
        """Set a game as inactive.

        Args:
            game_id: ID of the game to deactivate

        Returns:
            The deactivated Game instance

        Raises:
            GameError: If the game doesn't exist
        """
        logger.debug(f"Deactivating game: {game_id}")

        def _deactivate_game(session: Session) -> Game:
            # Use get_entity_or_error instead of manual query and check
            game = self.get_entity_or_error(
                session, Game, game_id, GameError, f"Game not found: {game_id}"
            )

            game.is_active = False

            return game

        game = self._execute_db_operation("deactivate game", _deactivate_game)
        logger.debug(f"Deactivated game: {game.id}")
        return game

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
            description: New description for the game (if None, description
                         won't be updated)

        Returns:
            The updated Game instance.

        Raises:
            GameError: If the game doesn't exist or a game with the same name exists
            ValueError: If neither name nor description is provided
        """
        logger.debug(
            f"Updating game: {game_id}, name={name}, description={description is not None}"
        )

        # Validate input
        if name is None and description is None:
            raise ValueError("At least one of name or description must be provided")

        def _update_game(session: Session) -> Game:
            # Use get_entity_or_error instead of manual query and check
            game = self.get_entity_or_error(
                session, Game, game_id, GameError, f"Game not found: {game_id}"
            )

            # Update the game properties if provided
            if name is not None:
                old_name = game.name
                game.name = name

                # Only update the slug if the name changed
                if old_name != name:
                    game.slug = slugify(name)

            if description is not None:
                game.description = description

            return game

        try:
            game = self._execute_db_operation("update game", _update_game)
            logger.debug(f"Updated game: {game.id}")
            return game
        except IntegrityError as e:
            self._handle_integrity_error(e, "update", name or "")

    def delete_game(self, game_id: str) -> bool:
        """Delete a game.

        Args:
            game_id: ID of the game to delete

        Returns:
            True if the game was deleted, False otherwise
        """
        logger.debug(f"Deleting game: {game_id}")

        def _delete_game(session: Session) -> bool:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.debug(f"Cannot delete nonexistent game: {game_id}")
                return False

            session.delete(game)
            return True

        result = self._execute_db_operation("delete game", _delete_game)
        if result:
            logger.debug(f"Deleted game: {game_id}")
        else:
            logger.debug(f"Game not found for deletion: {game_id}")
        return result
