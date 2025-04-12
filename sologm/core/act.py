"""Act manager for SoloGM."""

import logging
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.act import Act, ActStatus
from sologm.utils.errors import GameError

if TYPE_CHECKING:
    from sologm.core.game import GameManager
    from sologm.core.scene import SceneManager


logger = logging.getLogger(__name__)


class ActManager(BaseManager[Act, Act]):
    """Manages act operations."""

    def __init__(
        self,
        game_manager: Optional["GameManager"] = None,
        session: Optional[Session] = None,
    ):
        """Initialize the act manager.

        Args:
            game_manager: Optional GameManager instance.
            session: Optional database session (primarily for testing).
        """
        super().__init__(session)
        self._game_manager = game_manager

    # Parent manager access
    @property
    def game_manager(self) -> "GameManager":
        """Lazy-initialize game manager if not provided."""
        return self._lazy_init_manager("_game_manager", "sologm.core.game.GameManager")

    # Child manager access
    @property
    def scene_manager(self) -> "SceneManager":
        """Lazy-initialize scene manager."""
        return self._lazy_init_manager(
            "_scene_manager", "sologm.core.scene.SceneManager", act_manager=self
        )

    def create_act(
        self,
        game_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        make_active: bool = True,
    ) -> Act:
        """Create a new act in a game.

        Args:
            game_id: ID of the game to create the act in
                    If not provided, uses the active game
            title: Optional title of the act (can be None for untitled acts)
            description: Optional description of the act
            make_active: Whether to make this act the active act in its game

        Returns:
            The newly created act

        Raises:
            GameError: If the game doesn't exist or no active game is found
        """
        logger.debug(
            f"Creating act in game_id={game_id or 'active game'}: "
            f"title='{title or 'Untitled'}', "
            f"description='{description[:20] + '...' if description else 'None'}', "
            f"make_active={make_active}"
        )

        # Get game_id from active context if not provided
        if not game_id:
            active_game = self.game_manager.get_active_game()
            if not active_game:
                msg = "No active game. Use 'sologm game activate' to set one."
                logger.warning(msg)
                raise GameError(msg)
            game_id = active_game.id
            logger.debug(f"Using active game with ID {game_id}")

        def _create_act(session: Session) -> Act:
            try:
                # Check if game exists
                from sologm.models.game import Game

                game = self.get_entity_or_error(
                    session,
                    Game,
                    game_id,
                    GameError,
                    f"Game with ID {game_id} not found",
                )
                logger.debug(f"Found game: {game.name}")

                # Get the next sequence number for this game
                acts = self.list_entities(
                    Act,
                    filters={"game_id": game_id},
                    order_by="sequence",
                    order_direction="desc",
                    limit=1,
                )

                next_sequence = 1
                if acts:
                    next_sequence = acts[0].sequence + 1
                logger.debug(f"Using sequence number {next_sequence}")

                # Create the new act
                act = Act.create(
                    game_id=game_id,
                    title=title,
                    description=description,
                    sequence=next_sequence,
                )
                session.add(act)
                session.flush()
                logger.debug(f"Created act with ID {act.id}")

                if make_active:
                    # Deactivate all other acts in this game
                    self._deactivate_all_acts(session, game_id)
                    logger.debug(f"Deactivated all other acts in game {game_id}")

                    # Set this act as active
                    act.is_active = True
                    logger.debug(f"Set act {act.id} as active")

                logger.info(
                    f"Created act with ID {act.id} in game {game_id}: "
                    f"title='{act.title or 'Untitled'}'"
                )
                return act
            except Exception as e:
                logger.error(
                    f"Error creating act in game {game_id}: {str(e)}", exc_info=True
                )
                self._handle_operation_error(
                    f"create act in game {game_id}", e, GameError
                )

        return self._execute_db_operation("create_act", _create_act)

    def get_act(self, act_id: str) -> Optional[Act]:
        """Get an act by ID.

        Args:
            act_id: ID of the act to get

        Returns:
            The act, or None if not found
        """
        logger.debug(f"Getting act with ID {act_id}")

        try:
            acts = self.list_entities(Act, filters={"id": act_id}, limit=1)
            result = acts[0] if acts else None
            logger.debug(f"Found act: {result.id if result else 'None'}")
            return result
        except Exception as e:
            logger.error(f"Error getting act {act_id}: {str(e)}", exc_info=True)
            self._handle_operation_error(f"get act {act_id}", e, GameError)
            return None  # This will never be reached as _handle_operation_error raises

    def list_acts(self, game_id: Optional[str] = None) -> List[Act]:
        """List all acts in a game.

        Args:
            game_id: Optional ID of the game to list acts for
                    If not provided, uses the active game

        Returns:
            List of acts in the game, ordered by sequence

        Raises:
            GameError: If game_id is not provided and no active game is found
        """
        logger.debug(f"Listing acts for game_id={game_id or 'active game'}")

        if not game_id:
            active_game = self.game_manager.get_active_game()
            if not active_game:
                msg = "No active game. Use 'sologm game activate' to set one."
                logger.warning(msg)
                raise GameError(msg)
            game_id = active_game.id
            logger.debug(f"Using active game with ID {game_id}")

        try:
            acts = self.list_entities(
                Act, filters={"game_id": game_id}, order_by="sequence"
            )
            logger.debug(f"Found {len(acts)} acts in game {game_id}")
            return acts
        except Exception as e:
            logger.error(
                f"Error listing acts for game {game_id}: {str(e)}", exc_info=True
            )
            self._handle_operation_error(f"list acts for game {game_id}", e, GameError)
            return []  # This will never be reached as _handle_operation_error raises

    def get_active_act(self, game_id: Optional[str] = None) -> Optional[Act]:
        """Get the active act in a game.

        Args:
            game_id: ID of the game to get the active act for
                    If not provided, uses the active game

        Returns:
            The active act, or None if no act is active

        Raises:
            GameError: If game_id is not provided and no active game is found
        """
        logger.debug(f"Getting active act for game_id={game_id or 'active game'}")

        try:
            if not game_id:
                active_game = self.game_manager.get_active_game()
                if not active_game:
                    msg = "No active game. Use 'sologm game activate' to set one."
                    logger.warning(msg)
                    raise GameError(msg)
                game_id = active_game.id
                logger.debug(f"Using active game with ID {game_id}")

            acts = self.list_entities(
                Act, filters={"game_id": game_id, "is_active": True}, limit=1
            )

            result = acts[0] if acts else None
            logger.debug(
                f"Active act for game {game_id}: "
                f"{result.id + ' (' + (result.title or 'Untitled') + ')' if result else 'None'}"
            )
            return result
        except Exception as e:
            if not isinstance(e, GameError):
                logger.error(f"Error getting active act: {str(e)}", exc_info=True)
                self._handle_operation_error(
                    f"get active act for game {game_id}", e, GameError
                )
            raise

    def edit_act(
        self,
        act_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Act:
        """Edit an act's title and/or description.

        Args:
            act_id: ID of the act to edit
            title: New title for the act (None to leave unchanged)
            description: New description for the act (None to leave unchanged)

        Returns:
            The updated act

        Raises:
            GameError: If the act doesn't exist
        """
        logger.debug(
            f"Editing act {act_id}: "
            f"title={title or '(unchanged)'}, "
            f"description={description[:20] + '...' if description else '(unchanged)'}"
        )

        def _edit_act(session: Session) -> Act:
            try:
                # Use get_entity_or_error instead of manual query and check
                act = self.get_entity_or_error(
                    session, Act, act_id, GameError, f"Act with ID {act_id} not found"
                )
                logger.debug(f"Found act: {act.title or 'Untitled'}")

                # Update fields if provided
                if title is not None:
                    old_title = act.title
                    act.title = title
                    logger.debug(
                        f"Updated title from '{old_title or 'Untitled'}' to '{title or 'Untitled'}'"
                    )

                    # Update slug if title changes
                    if title:
                        from sologm.models.utils import slugify

                        act.slug = f"act-{act.sequence}-{slugify(title)}"
                    else:
                        act.slug = f"act-{act.sequence}-untitled"
                    logger.debug(f"Updated slug to '{act.slug}'")

                if description is not None:
                    act.description = description
                    logger.debug("Updated description")

                logger.info(f"Edited act {act_id}: title='{act.title or 'Untitled'}'")
                return act
            except Exception as e:
                logger.error(f"Error editing act {act_id}: {str(e)}", exc_info=True)
                self._handle_operation_error(f"edit act {act_id}", e, GameError)

        return self._execute_db_operation("edit_act", _edit_act)

    def complete_act(
        self,
        act_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Act:
        """Mark an act as complete and optionally update its title/description.

        Args:
            act_id: ID of the act to complete
            title: Optional new title for the act
            description: Optional new description for the act

        Returns:
            The completed act

        Raises:
            GameError: If the act doesn't exist
        """
        logger.debug(
            f"Completing act {act_id}: "
            f"title={title or '(unchanged)'}, "
            f"description={description[:20] + '...' if description else '(unchanged)'}"
        )

        def _complete_act(session: Session) -> Act:
            try:
                # Use get_entity_or_error instead of manual query and check
                act = self.get_entity_or_error(
                    session, Act, act_id, GameError, f"Act with ID {act_id} not found"
                )
                logger.debug(f"Found act: {act.title or 'Untitled'}")

                # Update fields if provided
                if title is not None:
                    old_title = act.title
                    act.title = title
                    logger.debug(
                        f"Updated title from '{old_title or 'Untitled'}' to '{title or 'Untitled'}'"
                    )

                    # Update slug if title changes
                    if title:
                        from sologm.models.utils import slugify

                        act.slug = f"act-{act.sequence}-{slugify(title)}"
                        logger.debug(f"Updated slug to '{act.slug}'")

                if description is not None:
                    act.description = description
                    logger.debug("Updated description")

                # Mark as completed
                old_status = act.status
                act.status = ActStatus.COMPLETED
                logger.debug(f"Updated status from {old_status} to {act.status}")

                logger.info(
                    f"Completed act {act_id}: title='{act.title or 'Untitled'}'"
                )
                return act
            except Exception as e:
                logger.error(f"Error completing act {act_id}: {str(e)}", exc_info=True)
                self._handle_operation_error(f"complete act {act_id}", e, GameError)

        return self._execute_db_operation("complete_act", _complete_act)

    def set_active(self, act_id: str) -> Act:
        """Set an act as the active act in its game.

        Args:
            act_id: ID of the act to set as active

        Returns:
            The activated act

        Raises:
            GameError: If the act doesn't exist
        """
        logger.debug(f"Setting act {act_id} as active")

        def _set_active(session: Session) -> Act:
            try:
                # Use get_entity_or_error instead of manual query and check
                act = self.get_entity_or_error(
                    session, Act, act_id, GameError, f"Act with ID {act_id} not found"
                )
                logger.debug(
                    f"Found act: {act.title or 'Untitled'} in game {act.game_id}"
                )

                # Deactivate all acts in this game
                self._deactivate_all_acts(session, act.game_id)
                logger.debug(f"Deactivated all acts in game {act.game_id}")

                # Set this act as active
                act.is_active = True
                logger.info(f"Set act {act_id} as active")
                return act
            except Exception as e:
                logger.error(
                    f"Error setting act {act_id} as active: {str(e)}", exc_info=True
                )
                self._handle_operation_error(
                    f"set act {act_id} as active", e, GameError
                )

        return self._execute_db_operation("set_active", _set_active)

    def _deactivate_all_acts(self, session: Session, game_id: str) -> None:
        """Deactivate all acts in a game.

        Args:
            session: Database session
            game_id: ID of the game to deactivate acts for
        """
        logger.debug(f"Deactivating all acts in game {game_id}")
        session.query(Act).filter(Act.game_id == game_id).update({Act.is_active: False})

    def validate_active_act(self, game_id: Optional[str] = None) -> Act:
        """Validate that there is an active act for the game.

        If game_id is not provided, uses the active game.

        Args:
            game_id: Optional ID of the game to validate

        Returns:
            The active act

        Raises:
            GameError: If there is no active act or no active game
        """
        logger.debug(f"Validating active act for game_id={game_id or 'active game'}")

        if not game_id:
            active_game = self.game_manager.get_active_game()
            if not active_game:
                msg = "No active game. Use 'sologm game activate' to set one."
                logger.warning(msg)
                raise GameError(msg)
            game_id = active_game.id
            logger.debug(f"Using active game with ID {game_id}")

        active_act = self.get_active_act(game_id)
        if not active_act:
            msg = (
                f"No active act in game {game_id}. Create one with 'sologm act create'."
            )
            logger.warning(msg)
            raise GameError(msg)

        logger.debug(
            f"Found active act: {active_act.id} ({active_act.title or 'Untitled'})"
        )
        return active_act
