"""Act manager for SoloGM."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.act import Act, ActStatus
from sologm.utils.errors import GameError

logger = logging.getLogger(__name__)


class ActManager(BaseManager[Act, Act]):
    """Manages act operations."""

    def create_act(
        self,
        game_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Act:
        """Create a new act in a game.

        Args:
            game_id: ID of the game to create the act in
            title: Optional title of the act (can be None for untitled acts)
            description: Optional description of the act

        Returns:
            The newly created act

        Raises:
            GameError: If the game doesn't exist
        """
        logger.debug(f"Creating act in game {game_id}")

        def _create_act(
            session: Session,
            game_id: str,
            title: Optional[str],
            description: Optional[str],
        ) -> Act:
            # Check if game exists
            from sologm.models.game import Game

            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                raise GameError(f"Game with ID {game_id} not found")

            # Get the next sequence number for this game
            max_sequence = (
                session.query(Act)
                .filter(Act.game_id == game_id)
                .order_by(Act.sequence.desc())
                .first()
            )
            next_sequence = 1 if max_sequence is None else max_sequence.sequence + 1

            # Create the new act
            act = Act.create(
                game_id=game_id,
                title=title,
                description=description,
                sequence=next_sequence,
            )
            session.add(act)
            session.flush()

            # Deactivate all other acts in this game
            self._deactivate_all_acts(session, game_id)

            # Set this act as active
            act.is_active = True
            return act

        return self._execute_db_operation(
            "create_act", _create_act, game_id, title, description
        )

    def list_acts(self, game_id: str) -> List[Act]:
        """List all acts in a game.

        Args:
            game_id: ID of the game to list acts for

        Returns:
            List of acts in the game, ordered by sequence
        """
        logger.debug(f"Listing acts for game {game_id}")

        def _list_acts(session: Session, game_id: str) -> List[Act]:
            return (
                session.query(Act)
                .filter(Act.game_id == game_id)
                .order_by(Act.sequence)
                .all()
            )

        return self._execute_db_operation("list_acts", _list_acts, game_id)

    def get_act(self, act_id: str) -> Optional[Act]:
        """Get an act by ID.

        Args:
            act_id: ID of the act to get

        Returns:
            The act, or None if not found
        """
        logger.debug(f"Getting act {act_id}")

        def _get_act(session: Session, act_id: str) -> Optional[Act]:
            return session.query(Act).filter(Act.id == act_id).first()

        return self._execute_db_operation("get_act", _get_act, act_id)

    def get_active_act(self, game_id: str) -> Optional[Act]:
        """Get the active act in a game.

        Args:
            game_id: ID of the game to get the active act for

        Returns:
            The active act, or None if no act is active
        """
        logger.debug(f"Getting active act for game {game_id}")

        def _get_active_act(session: Session, game_id: str) -> Optional[Act]:
            return (
                session.query(Act)
                .filter(Act.game_id == game_id, Act.is_active == True)  # noqa: E712
                .first()
            )

        return self._execute_db_operation("get_active_act", _get_active_act, game_id)

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
        logger.debug(f"Editing act {act_id}")

        def _edit_act(
            session: Session,
            act_id: str,
            title: Optional[str],
            description: Optional[str],
        ) -> Act:
            act = session.query(Act).filter(Act.id == act_id).first()
            if not act:
                raise GameError(f"Act with ID {act_id} not found")

            # Update fields if provided
            if title is not None:
                act.title = title
                # Update slug if title changes
                if title:
                    from sologm.models.utils import slugify

                    act.slug = f"act-{act.sequence}-{slugify(title)}"
                else:
                    act.slug = f"act-{act.sequence}-untitled"

            if description is not None:
                act.description = description

            return act

        return self._execute_db_operation(
            "edit_act", _edit_act, act_id, title, description
        )

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
        logger.debug(f"Completing act {act_id}")

        def _complete_act(
            session: Session,
            act_id: str,
            title: Optional[str],
            description: Optional[str],
        ) -> Act:
            act = session.query(Act).filter(Act.id == act_id).first()
            if not act:
                raise GameError(f"Act with ID {act_id} not found")

            # Update fields if provided
            if title is not None:
                act.title = title
                # Update slug if title changes
                if title:
                    from sologm.models.utils import slugify

                    act.slug = f"act-{act.sequence}-{slugify(title)}"

            if description is not None:
                act.description = description

            # Mark as completed
            act.status = ActStatus.COMPLETED

            return act

        return self._execute_db_operation(
            "complete_act", _complete_act, act_id, title, description
        )

    def set_active_act(self, game_id: str, act_id: str) -> Act:
        """Set an act as the active act in a game.

        Args:
            game_id: ID of the game
            act_id: ID of the act to set as active

        Returns:
            The activated act

        Raises:
            GameError: If the act doesn't exist or doesn't belong to the game
        """
        logger.debug(f"Setting act {act_id} as active in game {game_id}")

        def _set_active_act(session: Session, game_id: str, act_id: str) -> Act:
            act = session.query(Act).filter(Act.id == act_id).first()
            if not act:
                raise GameError(f"Act with ID {act_id} not found")

            if act.game_id != game_id:
                raise GameError(f"Act {act_id} does not belong to game {game_id}")

            # Deactivate all acts in this game
            self._deactivate_all_acts(session, game_id)

            # Set this act as active
            act.is_active = True
            return act

        return self._execute_db_operation(
            "set_active_act", _set_active_act, game_id, act_id
        )

    def _deactivate_all_acts(self, session: Session, game_id: str) -> None:
        """Deactivate all acts in a game.

        Args:
            session: Database session
            game_id: ID of the game to deactivate acts for
        """
        logger.debug(f"Deactivating all acts in game {game_id}")
        session.query(Act).filter(Act.game_id == game_id).update({Act.is_active: False})

    def validate_active_context(self, game_id: str) -> Tuple[str, Act]:
        """Validate that there is an active game and act.

        Args:
            game_id: ID of the game to validate

        Returns:
            Tuple of (game_id, active_act)

        Raises:
            GameError: If there is no active act
        """
        logger.debug(f"Validating active context for game {game_id}")
        active_act = self.get_active_act(game_id)
        if not active_act:
            raise GameError(f"No active act in game {game_id}")
        return game_id, active_act
