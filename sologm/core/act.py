"""Act manager for SoloGM."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.act import Act
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
            session: Optional database session for testing or CLI command injection.
        """
        super().__init__(session=session)
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
        summary: Optional[str] = None,
        make_active: bool = True,
    ) -> Act:
        """Create a new act in a game.

        Args:
            game_id: ID of the game to create the act in
                    If not provided, uses the active game
            title: Optional title of the act (can be None for untitled acts)
            summary: Optional summary of the act
            make_active: Whether to make this act the active act in its game

        Returns:
            The newly created act

        Raises:
            GameError: If the game doesn't exist or no active game is found
        """
        logger.debug(
            f"Creating act in game_id={game_id or 'active game'}: "
            f"title='{title or 'Untitled'}', "
            f"summary='{summary[:20] + '...' if summary else 'None'}', "
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

        # Validate that we can create a new act
        if make_active:
            self.validate_can_create_act(game_id)

        def _create_act(session: Session) -> Act:
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
                summary=summary,
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

        return self._execute_db_operation("create_act", _create_act)

    def get_act(self, act_id: str) -> Optional[Act]:
        """Get an act by ID.

        Args:
            act_id: ID of the act to get

        Returns:
            The act, or None if not found
        """
        logger.debug(f"Getting act with ID {act_id}")

        acts = self.list_entities(Act, filters={"id": act_id}, limit=1)
        result = acts[0] if acts else None
        logger.debug(f"Found act: {result.id if result else 'None'}")
        return result

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

        acts = self.list_entities(
            Act, filters={"game_id": game_id}, order_by="sequence"
        )
        logger.debug(f"Found {len(acts)} acts in game {game_id}")
        return acts

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

    def edit_act(
        self,
        act_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Act:
        """Edit an act's title and/or summary.

        Args:
            act_id: ID of the act to edit
            title: New title for the act (None to leave unchanged)
            summary: New summary for the act (None to leave unchanged)

        Returns:
            The updated act

        Raises:
            GameError: If the act doesn't exist
            ValueError: If neither title nor summary is provided
        """
        logger.debug(
            f"Editing act {act_id}: "
            f"title={title or '(unchanged)'}, "
            f"summary={summary[:20] + '...' if summary else '(unchanged)'}"
        )

        # Validate input
        if title is None and summary is None:
            raise ValueError("At least one of title or summary must be provided")

        def _edit_act(session: Session) -> Optional[Act]:
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
                    f"Updated title from '{old_title or 'Untitled'}' "
                    f"to '{title or 'Untitled'}'"
                )

                # Update slug if title changes
                if title:
                    from sologm.models.utils import slugify

                    act.slug = f"act-{act.sequence}-{slugify(title)}"
                else:
                    act.slug = f"act-{act.sequence}-untitled"
                logger.debug(f"Updated slug to '{act.slug}'")

            if summary is not None:
                act.summary = summary
                logger.debug("Updated summary")

            logger.info(f"Edited act {act_id}: title='{act.title or 'Untitled'}'")
            return act

        return self._execute_db_operation("edit_act", _edit_act)

    def complete_act(
        self,
        act_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Act:
        """Mark an act as complete and optionally update its title/summary.

        Args:
            act_id: ID of the act to complete
            title: Optional new title for the act
            summary: Optional new summary for the act

        Returns:
            The completed act

        Raises:
            GameError: If the act doesn't exist
        """
        logger.debug(
            f"Completing act {act_id}: "
            f"title={title or '(unchanged)'}, "
            f"summary={summary[:20] + '...' if summary else '(unchanged)'}"
        )

        def _complete_act(session: Session) -> Act:
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

            if summary is not None:
                act.summary = summary
                logger.debug("Updated summary")

            # Mark as not active
            act.is_active = False
            logger.debug("Set is_active to False")

            logger.info(f"Completed act {act_id}: title='{act.title or 'Untitled'}'")
            return act

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
            # Use get_entity_or_error instead of manual query and check
            act = self.get_entity_or_error(
                session, Act, act_id, GameError, f"Act with ID {act_id} not found"
            )
            logger.debug(f"Found act: {act.title or 'Untitled'} in game {act.game_id}")

            # Deactivate all acts in this game
            self._deactivate_all_acts(session, act.game_id)
            logger.debug(f"Deactivated all acts in game {act.game_id}")

            # Set this act as active
            act.is_active = True
            logger.info(f"Set act {act_id} as active")
            return act

        return self._execute_db_operation("set_active", _set_active)

    def _deactivate_all_acts(self, session: Session, game_id: str) -> None:
        """Deactivate all acts in a game.

        Args:
            session: Database session
            game_id: ID of the game to deactivate acts for
        """
        logger.debug(f"Deactivating all acts in game {game_id}")
        session.query(Act).filter(Act.game_id == game_id).update({Act.is_active: False})

    def validate_can_create_act(self, game_id: str) -> None:
        """Validate that a new act can be created in the game.

        Args:
            game_id: ID of the game to validate

        Raises:
            GameError: If there is already an active act
        """
        active_act = self.get_active_act(game_id)
        if active_act:
            title_display = f"'{active_act.title}'" if active_act.title else "untitled"
            raise GameError(
                f"Cannot create a new act: Active act ({title_display}) exists. "
                "Complete the current act first with 'sologm act complete'."
            )

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

    def prepare_act_data_for_summary(
        self, act_id: str, additional_context: Optional[str] = None
    ) -> Dict:
        """Prepare act data for the summary generation prompt.

        Args:
            act_id: ID of the act to summarize
            additional_context: Optional additional context from the user

        Returns:
            Dict containing structured data about the act

        Raises:
            GameError: If the act doesn't exist
            SceneError: If there's an issue retrieving scenes
            EventError: If there's an issue retrieving events
        """
        logger.debug(f"Preparing data for act {act_id} summary")

        def _prepare_data(session: Session) -> Dict:
            # Get the act
            act = self.get_entity_or_error(
                session, Act, act_id, GameError, f"Act with ID {act_id} not found"
            )
            logger.debug(f"Found act: {act.title or 'Untitled'}")

            # Get the game
            from sologm.models.game import Game

            game = self.get_entity_or_error(
                session,
                Game,
                act.game_id,
                GameError,
                f"Game with ID {act.game_id} not found",
            )
            logger.debug(f"Found game: {game.name}")

            # Get all scenes in the act
            scenes = self.scene_manager.list_scenes(act_id)
            logger.debug(f"Found {len(scenes)} scenes")

            # Collect all events from all scenes
            events_by_scene = {}
            for scene in scenes:
                # Get events for this scene
                scene_events = self.scene_manager.event_manager.list_events(
                    scene_id=scene.id
                )
                events_by_scene[scene.id] = scene_events
                logger.debug(f"Found {len(scene_events)} events for scene {scene.id}")

            # Format the data
            act_data = {
                "game": {
                    "name": game.name,
                    "description": game.description,
                },
                "act": {
                    "sequence": act.sequence,
                    "title": act.title,
                    "summary": act.summary,
                },
                "scenes": [],
                "additional_context": additional_context,
            }

            # Add scene data
            for scene in scenes:
                scene_data = {
                    "sequence": scene.sequence,
                    "title": scene.title,
                    "description": scene.description,
                    "events": [],
                }

                # Add events for this scene
                for event in events_by_scene.get(scene.id, []):
                    scene_data["events"].append(
                        {
                            "description": event.description,
                            "source": event.source_name,
                            "created_at": event.created_at.isoformat()
                            if event.created_at
                            else None,
                        }
                    )

                act_data["scenes"].append(scene_data)

            logger.debug("Successfully prepared act data for summary")
            return act_data

        return self._execute_db_operation("prepare_act_data_for_summary", _prepare_data)

    def generate_act_summary(
        self, act_id: str, additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate a summary for an act using AI.

        Args:
            act_id: ID of the act to summarize
            additional_context: Optional additional context from the user

        Returns:
            Dict with generated title and summary

        Raises:
            GameError: If the act doesn't exist
            APIError: If there's an error with the AI API
            SceneError: If there's an issue retrieving scenes
            EventError: If there's an issue retrieving events
        """
        logger.debug(f"Generating summary for act {act_id}")

        # Prepare the data
        act_data = self.prepare_act_data_for_summary(act_id, additional_context)
        logger.debug("Act data prepared successfully")

        # Import here to avoid circular imports
        from sologm.core.prompts.act import ActPrompts
        from sologm.integrations.anthropic import AnthropicClient
        from sologm.utils.errors import APIError

        # Build the prompt
        prompt = ActPrompts.build_summary_prompt(act_data)
        logger.debug("Built summary prompt")

        # Create Anthropic client
        client = AnthropicClient()
        logger.debug("Created Anthropic client")

        try:
            # Send to Anthropic
            response = client.send_message(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
            )
            logger.debug("Received response from Anthropic")

            # Parse the response
            summary_data = ActPrompts.parse_summary_response(response)
            logger.debug(
                f"Parsed summary response: title='{summary_data['title']}', "
                f"summary='{summary_data['summary'][:50]}...'"
            )

            return summary_data
        except Exception as e:
            logger.error(f"Error generating act summary: {str(e)}", exc_info=True)
            if "anthropic" in str(e).lower() or "api" in str(e).lower():
                raise APIError(f"Failed to generate act summary: {str(e)}") from e
            raise

    def generate_and_update_act_summary(
        self, act_id: str, additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a summary for an act and update the act with it.

        Args:
            act_id: ID of the act to summarize
            additional_context: Optional additional context

        Returns:
            Dict with generated and updated title and summary and the act

        Raises:
            GameError: If the act doesn't exist
            APIError: If there's an error with the AI API
        """
        # Generate summary
        summary_data = self.generate_act_summary(act_id, additional_context)

        # Update the act
        updated_act = self.edit_act(
            act_id=act_id,
            title=summary_data.get("title"),
            summary=summary_data.get("summary"),
        )

        return {
            "title": updated_act.title,
            "summary": updated_act.summary,
            "act": updated_act,
        }
