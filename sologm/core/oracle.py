"""Oracle interpretation system for Solo RPG Helper."""

import logging
import re
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.prompts.oracle import OraclePrompts
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.event import Event
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.utils.errors import OracleError

logger = logging.getLogger(__name__)


class OracleManager(BaseManager[InterpretationSet, InterpretationSet]):
    """Manages oracle interpretation operations."""

    def __init__(
        self,
        anthropic_client: Optional[AnthropicClient] = None,
        event_manager: Optional[EventManager] = None,
        session: Optional[Session] = None,
    ):
        """Initialize the oracle manager.

        Args:
            anthropic_client: Optional Anthropic client instance.
            event_manager: Optional event manager instance.
            session: Optional database session (primarily for testing).
        """
        super().__init__(session)

        # If no anthropic_client is provided, create one using the config
        if not anthropic_client:
            from sologm.utils.config import get_config

            config = get_config()
            api_key = config.get("anthropic_api_key")
            self.anthropic_client = AnthropicClient(api_key=api_key)
        else:
            self.anthropic_client = anthropic_client

        self.event_manager = event_manager or EventManager(session=session)

    def validate_active_context(
        self, game_manager: GameManager, scene_manager: SceneManager
    ) -> Tuple[str, str]:
        """Validate active game and scene exist.

        Args:
            game_manager: GameManager instance
            scene_manager: SceneManager instance

        Returns:
            tuple[str, str]: game_id, scene_id

        Raises:
            OracleError: If game or scene not active
        """
        active_game = game_manager.get_active_game()
        if not active_game:
            raise OracleError("No active game found")

        active_scene = scene_manager.get_active_scene(active_game.id)
        if not active_scene:
            raise OracleError("No active scene found")

        return active_game.id, active_scene.id

    def get_interpretation_set(self, set_id: str) -> InterpretationSet:
        """Get an interpretation set by ID.

        Args:
            set_id: ID of the interpretation set

        Returns:
            InterpretationSet: The requested interpretation set

        Raises:
            OracleError: If set not found
        """

        def _get_interpretation_set(session: Session, set_id: str) -> InterpretationSet:
            interp_set = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.id == set_id)
                .first()
            )
            if not interp_set:
                raise OracleError(f"Interpretation set {set_id} not found")
            return interp_set

        return self._execute_db_operation(
            f"get interpretation set {set_id}", _get_interpretation_set, set_id
        )

    def get_current_interpretation_set(
        self, scene_id: str
    ) -> Optional[InterpretationSet]:
        """Get current interpretation set for a scene if it exists.

        Args:
            scene_id: ID of the scene to check

        Returns:
            Optional[InterpretationSet]: Current interpretation set or None
        """

        def _get_current_interpretation_set(
            session: Session, scene_id: str
        ) -> Optional[InterpretationSet]:
            return (
                session.query(InterpretationSet)
                .filter(
                    InterpretationSet.scene_id == scene_id,
                    InterpretationSet.is_current == True,  # noqa: E712
                )
                .first()
            )

        return self._execute_db_operation(
            f"get current interpretation set for scene {scene_id}",
            _get_current_interpretation_set,
            scene_id,
        )

    def get_most_recent_interpretation(
        self, scene_id: str
    ) -> Optional[Tuple[InterpretationSet, Interpretation]]:
        """Get the most recently resolved interpretation for a game/scene.

        Args:
            scene_id: ID of the scene

        Returns:
            Optional tuple of (InterpretationSet, selected Interpretation) or None if
            none found
        """

        def _get_most_recent_interpretation(
            session: Session, scene_id: str
        ) -> Optional[Tuple[InterpretationSet, Interpretation]]:
            # Find interpretation sets for this scene with selected interpretations
            interp_set = (
                session.query(InterpretationSet)
                .join(Interpretation, InterpretationSet.id == Interpretation.set_id)
                .filter(
                    InterpretationSet.scene_id == scene_id,
                    Interpretation.is_selected == True,  # noqa: E712
                )
                .order_by(InterpretationSet.created_at.desc())
                .first()
            )

            if not interp_set:
                return None

            # Get the selected interpretation
            selected_interp = (
                session.query(Interpretation)
                .filter(
                    Interpretation.set_id == interp_set.id,
                    Interpretation.is_selected == True,  # noqa: E712
                )
                .first()
            )

            if not selected_interp:
                return None

            return (interp_set, selected_interp)

        return self._execute_db_operation(
            "get most recent interpretation",
            _get_most_recent_interpretation,
            scene_id,
        )

    def _build_prompt(
        self,
        game_description: str,
        scene_description: str,
        recent_events: List[str],
        context: str,
        oracle_results: str,
        count: int,
        previous_interpretations: Optional[List[dict]] = None,
        retry_attempt: int = 0,
    ) -> str:
        """Build the prompt for Claude API.

        Args:
            game_description: Description of the current game.
            scene_description: Description of the current scene.
            recent_events: List of recent events in the scene.
            context: User's question or context.
            oracle_results: Oracle results to interpret.
            count: Number of interpretations to generate.
            previous_interpretations: Optional list of previous interpretations to avoid.
            retry_attempt: Number of retry attempts made.

        Returns:
            str: The formatted prompt.
        """
        return OraclePrompts.build_interpretation_prompt(
            game_description,
            scene_description,
            recent_events,
            context,
            oracle_results,
            count,
            previous_interpretations,
            retry_attempt,
        )

    def build_interpretation_prompt_for_active_context(
        self,
        game_manager: GameManager,
        scene_manager: SceneManager,
        context: str,
        oracle_results: str,
        count: int,
    ) -> str:
        """Build an interpretation prompt for the active game and scene.

        Args:
            game_manager: GameManager instance
            scene_manager: SceneManager instance
            context: User's question or context
            oracle_results: Oracle results to interpret
            count: Number of interpretations to generate

        Returns:
            str: The formatted prompt

        Raises:
            OracleError: If no active game or scene
        """
        # Validate active context
        game_id, scene_id = self.validate_active_context(game_manager, scene_manager)

        # Get game and scene details
        game = game_manager.get_game(game_id)
        scene = scene_manager.get_scene(game_id, scene_id)

        # Get recent events
        from sologm.core.event import EventManager

        event_manager = EventManager(session=self._session)
        recent_events = event_manager.list_events(game_id, scene_id, limit=5)
        recent_event_descriptions = [event.description for event in recent_events]

        # Build and return the prompt
        return self._build_prompt(
            game.description,
            scene.description,
            recent_event_descriptions,
            context,
            oracle_results,
            count,
        )

    def _get_context_data(
        self,
        game_id: str,
        scene_id: str,
        retry_attempt: int,
        previous_set_id: Optional[str],
    ) -> Tuple[object, object, List[object], Optional[List[dict]]]:
        """Get all context data needed for interpretation.

        Args:
            game_id: ID of the current game
            scene_id: ID of the current scene
            retry_attempt: Current retry attempt number
            previous_set_id: ID of the previous interpretation set

        Returns:
            Tuple containing game, scene, recent events, and previous interpretations

        Raises:
            OracleError: If game or scene not found
        """

        def _get_data(session: Session) -> Tuple:
            # Get game and scene
            from sologm.models.game import Game
            from sologm.models.scene import Scene

            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                raise OracleError(f"Game {game_id} not found")

            scene = (
                session.query(Scene)
                .filter(Scene.id == scene_id, Scene.game_id == game_id)
                .first()
            )
            if not scene:
                raise OracleError(f"Scene {scene_id} not found in game {game_id}")

            # Get recent events
            recent_events = (
                session.query(Event)
                .filter(Event.scene_id == scene_id, Event.game_id == game_id)
                .order_by(Event.created_at.desc())
                .limit(5)
                .all()
            )

            # Get previous interpretations if this is a retry
            previous_interpretations = None
            if retry_attempt > 0 and previous_set_id:
                previous_interps = (
                    session.query(Interpretation)
                    .filter(Interpretation.set_id == previous_set_id)
                    .all()
                )
                if previous_interps:
                    previous_interpretations = [
                        {"title": interp.title, "description": interp.description}
                        for interp in previous_interps
                    ]

            return game, scene, recent_events, previous_interpretations

        return self._execute_db_operation("get context data", _get_data)

    def _create_interpretation_set(
        self,
        scene_id: str,
        context: str,
        oracle_results: str,
        parsed_interpretations: List[dict],
        retry_attempt: int,
    ) -> InterpretationSet:
        """Create interpretation set and interpretations in database.

        Args:
            scene_id: ID of the scene
            context: User's question or context
            oracle_results: Oracle results to interpret
            parsed_interpretations: List of parsed interpretations
            retry_attempt: Current retry attempt number

        Returns:
            InterpretationSet: The created interpretation set
        """

        def _create(session: Session) -> InterpretationSet:
            # First, clear any current interpretation sets for this scene
            current_sets = (
                session.query(InterpretationSet)
                .filter(
                    InterpretationSet.scene_id == scene_id,
                    InterpretationSet.is_current == True,  # noqa: E712
                )
                .all()
            )

            for current_set in current_sets:
                current_set.is_current = False

            # Create interpretation set
            interp_set = InterpretationSet.create(
                scene_id=scene_id,
                context=context,
                oracle_results=oracle_results,
                retry_attempt=retry_attempt,
                is_current=True,
            )
            session.add(interp_set)
            session.flush()  # Flush to get the ID

            # Create interpretations
            for interp_data in parsed_interpretations:
                interpretation = Interpretation.create(
                    set_id=interp_set.id,
                    title=interp_data["title"],
                    description=interp_data["description"],
                    is_selected=False,
                )
                session.add(interpretation)

            return interp_set

        return self._execute_db_operation("create interpretation set", _create)

    def _parse_interpretations(self, response_text: str) -> List[dict]:
        """Parse interpretations from Claude's response using Markdown format.

        Args:
            response_text: Raw response from Claude API.

        Returns:
            List[dict]: List of parsed interpretations.
        """
        # Clean up the response to handle potential formatting issues
        # Remove any markdown code block markers if present
        cleaned_text = re.sub(r"```markdown|```", "", response_text)

        # Parse the interpretations using regex
        # This pattern matches a level 2 header (##) followed by text until
        # the next level 2 header or end of string
        pattern = r"## (.*?)\n(.*?)(?=\n## |$)"
        matches = re.findall(pattern, cleaned_text, re.DOTALL)

        interpretations = []
        for title, description in matches:
            interpretations.append(
                {"title": title.strip(), "description": description.strip()}
            )

        return interpretations

    def get_interpretations(
        self,
        game_id: str,
        scene_id: str,
        context: str,
        oracle_results: str,
        count: int = 5,
        retry_attempt: int = 0,
        max_retries: Optional[int] = None,
        previous_set_id: Optional[str] = None,
    ) -> InterpretationSet:
        """Get interpretations for oracle results.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            context: User's question or context.
            oracle_results: Oracle results to interpret.
            count: Number of interpretations to generate.
            retry_attempt: Number of retry attempts made.
            max_retries: Maximum number of automatic retries if parsing fails.
                If None, uses the value from config.
            previous_set_id: ID of the previous interpretation set to avoid duplicating.

        Returns:
            InterpretationSet: Set of generated interpretations.

        Raises:
            OracleError: If interpretations cannot be generated after max retries.
        """
        # If this is a retry but no previous_set_id was provided,
        # try to find the current interpretation set for this scene
        if retry_attempt > 0 and previous_set_id is None:
            current_set = self.get_current_interpretation_set(scene_id)
            if current_set:
                previous_set_id = current_set.id

        # Get max_retries from config if not provided
        if max_retries is None:
            from sologm.utils.config import get_config

            config = get_config()
            max_retries = int(config.get("oracle_retries", 2))

        # Try to get interpretations with automatic retry
        for attempt in range(retry_attempt, retry_attempt + max_retries + 1):
            try:
                # Get game and scene details, recent events, etc.
                game, scene, recent_events, previous_interpretations = (
                    self._get_context_data(game_id, scene_id, attempt, previous_set_id)
                )

                # Build prompt and get response
                prompt = self._build_prompt(
                    game.description,
                    scene.description,
                    [event.description for event in recent_events],
                    context,
                    oracle_results,
                    count,
                    previous_interpretations,
                    attempt,
                )

                # Get response from AI
                try:
                    logger.debug("Sending prompt to Claude API")
                    response = self.anthropic_client.send_message(prompt)
                except Exception as e:
                    logger.error(f"Error from AI service: {str(e)}")
                    raise OracleError(f"Failed to get interpretations from AI service: {str(e)}") from e

                # Parse interpretations
                parsed = self._parse_interpretations(response)
                logger.debug(f"Found {len(parsed)} interpretations")

                # If parsing succeeded, create and return interpretation set
                if parsed:
                    return self._create_interpretation_set(
                        scene_id, context, oracle_results, parsed, attempt
                    )

                # If we're on the last attempt and parsing failed, raise error
                if attempt >= retry_attempt + max_retries:
                    logger.warning("Failed to parse any interpretations from response")
                    logger.debug(f"Raw response: {response}")
                    raise OracleError(
                        f"Failed to parse interpretations from AI response after "
                        f"{attempt + 1} attempts"
                    )

                # Otherwise, continue to next attempt
                logger.warning(
                    f"Failed to parse interpretations (attempt "
                    f"{attempt + 1}/{retry_attempt + max_retries + 1}). "
                    f"Retrying automatically."
                )

            except OracleError:
                # Re-raise OracleErrors without wrapping them
                raise

        # This should never be reached due to the error in the loop
        raise OracleError("Failed to get interpretations after maximum retries")

    def select_interpretation(
        self,
        interpretation_set_id: str,
        interpretation_id: str,
        add_event: bool = True,
    ) -> Interpretation:
        """Select an interpretation and optionally add it as an event.

        Args:
            interpretation_set_id: ID of the interpretation set.
            interpretation_id: ID of the interpretation to select.
            add_event: Whether to add the interpretation as an event.

        Returns:
            Interpretation: The selected interpretation.
        """

        def _select_interpretation(
            session: Session,
            interpretation_set_id: str,
            interpretation_id: str,
            add_event: bool,
        ) -> Interpretation:
            # Get the interpretation set
            interp_set = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.id == interpretation_set_id)
                .first()
            )

            if not interp_set:
                raise OracleError(
                    f"Interpretation set {interpretation_set_id} not found"
                )

            # Get the interpretation
            interpretation = (
                session.query(Interpretation)
                .filter(
                    Interpretation.id == interpretation_id,
                    Interpretation.set_id == interpretation_set_id,
                )
                .first()
            )

            if not interpretation:
                raise OracleError(
                    f"Interpretation {interpretation_id} not found in set "
                    f"{interpretation_set_id}"
                )

            # Clear any previously selected interpretations in this set
            for interp in (
                session.query(Interpretation)
                .filter(Interpretation.set_id == interpretation_set_id)
                .all()
            ):
                interp.is_selected = False

            # Mark this interpretation as selected
            interpretation.is_selected = True

            # Add as event if requested
            if add_event:
                self.add_interpretation_event(interp_set.scene_id, interpretation)

            return interpretation

        return self._execute_db_operation(
            "select interpretation",
            _select_interpretation,
            interpretation_set_id,
            interpretation_id,
            add_event,
        )

    def add_interpretation_event(
        self, scene_id: str, interpretation: Interpretation
    ) -> None:
        """Add an interpretation as an event.

        Args:
            scene_id: ID of the current scene.
            interpretation: The interpretation to add as an event.
        """

        def _add_interpretation_event(
            session: Session, scene_id: str, interpretation: Interpretation
        ) -> None:
            # Access the interpretation_set relationship directly
            interp_set = interpretation.interpretation_set

            # Access the scene relationship from the interpretation set
            scene = interp_set.scene

            description = f"{interpretation.title}: {interpretation.description}"

            # Create the event
            event = Event.create(
                game_id=scene.game_id,
                scene_id=scene_id,
                description=description,
                source="oracle",
                interpretation_id=interpretation.id,
            )
            session.add(event)

        self._execute_db_operation(
            "add interpretation event",
            _add_interpretation_event,
            scene_id,
            interpretation,
        )
