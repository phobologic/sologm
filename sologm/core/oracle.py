"""Oracle interpretation system for Solo RPG Helper."""

import logging
import re
from typing import TYPE_CHECKING, List, Optional, Tuple

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.prompts.oracle import OraclePrompts
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.utils.errors import OracleError

if TYPE_CHECKING:
    from sologm.core.act import ActManager


logger = logging.getLogger(__name__)


class OracleManager(BaseManager[InterpretationSet, InterpretationSet]):
    """Manages oracle interpretation operations."""

    def __init__(
        self,
        anthropic_client: Optional[AnthropicClient] = None,
        scene_manager: Optional[SceneManager] = None,
        event_manager: Optional[EventManager] = None,
        session: Optional[Session] = None,
    ):
        """Initialize the oracle manager.

        Args:
            anthropic_client: Optional Anthropic client instance.
            scene_manager: Optional SceneManager instance.
            event_manager: Optional event manager instance.
            session: Optional database session (primarily for testing).
        """
        super().__init__(session)

        # Store references to managers
        self._scene_manager = scene_manager
        self._event_manager = event_manager

        # If no anthropic_client is provided, create one using the config
        if not anthropic_client:
            from sologm.utils.config import get_config

            config = get_config()
            api_key = config.get("anthropic_api_key")
            self.anthropic_client = AnthropicClient(api_key=api_key)
        else:
            self.anthropic_client = anthropic_client

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager if not provided."""
        if self._scene_manager is None:
            from sologm.core.scene import SceneManager

            self._scene_manager = SceneManager(session=self._session)
        return self._scene_manager

    @property
    def act_manager(self) -> "ActManager":
        """Access act manager through scene manager."""
        return self.scene_manager.act_manager

    @property
    def game_manager(self) -> GameManager:
        """Access game manager through act manager."""
        return self.act_manager.game_manager

    @property
    def event_manager(self) -> EventManager:
        """Lazy-initialize event manager if not provided."""
        if self._event_manager is None:
            self._event_manager = EventManager(session=self._session)
        return self._event_manager

    def get_active_context(self) -> Tuple[str, str, str]:
        """Get active game, act, and scene IDs.

        Returns:
            tuple[str, str, str]: game_id, act_id, scene_id

        Raises:
            OracleError: If game, act, or scene not active
        """
        active_game = self.game_manager.get_active_game()
        if not active_game:
            raise OracleError("No active game found")

        logger.debug(f"Validating active act for game {active_game.id}")
        active_act = self.act_manager.get_active_act(active_game.id)
        if not active_act:
            logger.debug("No active act found")
            raise OracleError("No active act found")

        logger.debug(f"Found active act: {active_act.id}")
        logger.debug(f"Checking for active scene in act {active_act.id}")
        active_scene = self.scene_manager.get_active_scene(active_act.id)
        if not active_scene:
            logger.debug("No active scene found in the active act")
            raise OracleError("No active scene found")

        logger.debug(f"Found active scene: {active_scene.id}")
        return active_game.id, active_act.id, active_scene.id

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
            previous_interpretations: Optional list of previous
                                      interpretations to avoid.
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
        context: str = "",
        oracle_results: str = "",
        count: int = 5,
    ) -> str:
        """Build an interpretation prompt for the active game and scene.

        Args:
            context: User's question or context
            oracle_results: Oracle results to interpret
            count: Number of interpretations to generate

        Returns:
            str: The formatted prompt

        Raises:
            OracleError: If no active game, act, or scene
        """
        # Get active context
        game_id, act_id, scene_id = self.get_active_context()

        # Get game and scene details
        game = self.game_manager.get_game(game_id)
        scene = self.scene_manager.get_scene(scene_id)

        game_description = ""
        if game and game.description:
            game_description = game.description

        scene_description = ""
        if scene and scene.description:
            scene_description = scene.description

        # Get recent events
        recent_events = self.event_manager.list_events(scene_id, limit=5)
        recent_event_descriptions = [event.description for event in recent_events]

        # Build and return the prompt
        return self._build_prompt(
            game_description or "",
            scene_description or "",
            recent_event_descriptions,
            context,
            oracle_results,
            count,
        )

    def _get_context_data(
        self,
        scene_id: str,
        retry_attempt: int = 0,
        previous_set_id: Optional[str] = None,
    ) -> Tuple[object, object, object, List[object], Optional[List[dict]]]:
        """Get all context data needed for interpretation.

        Args:
            scene_id: ID of the scene
            retry_attempt: Current retry attempt number
            previous_set_id: ID of the previous interpretation set

        Returns:
            Tuple containing game, act, scene, recent events, and previous
            interpretations

        Raises:
            OracleError: If scene not found
        """

        def _get_data(session: Session) -> Tuple:
            # Get scene (and through relationships, act and game)
            from sologm.models.scene import Scene

            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise OracleError(f"Scene {scene_id} not found")

            # Access act and game through relationships
            act = scene.act
            game = act.game

            # Get recent events
            recent_events = (
                session.query(Event)
                .filter(Event.scene_id == scene_id)
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

            return game, act, scene, recent_events, previous_interpretations

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
        act_id: str,
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
            act_id: ID of the current act.
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
                # Get game, act, scene details, recent events, etc.
                game, act, scene, recent_events, previous_interpretations = (
                    self._get_context_data(scene_id, attempt, previous_set_id)
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
                    raise OracleError(
                        f"Failed to get interpretations from AI service: {str(e)}"
                    ) from e

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

    def find_interpretation(
        self, interpretation_set_id: str, identifier: str
    ) -> Interpretation:
        """Find an interpretation by sequence number, slug, or UUID.

        Args:
            interpretation_set_id: ID of the interpretation set
            identifier: Sequence number (1, 2, 3...), slug, or UUID

        Returns:
            The found interpretation

        Raises:
            OracleError: If interpretation not found
        """

        def _find_interpretation(
            session: Session, set_id: str, identifier: str
        ) -> Interpretation:
            # Get all interpretations in the set
            interpretations = (
                session.query(Interpretation)
                .filter(Interpretation.set_id == set_id)
                .all()
            )

            if not interpretations:
                raise OracleError(f"No interpretations found in set {set_id}")

            # Try to parse as sequence number
            try:
                seq_num = int(identifier)
                if 1 <= seq_num <= len(interpretations):
                    return interpretations[seq_num - 1]  # Convert to 0-based index
            except ValueError:
                pass  # Not a number, continue

            # Try as slug
            for interp in interpretations:
                if interp.slug == identifier:
                    return interp

            # Try as UUID
            interp = (
                session.query(Interpretation)
                .filter(
                    Interpretation.set_id == set_id, Interpretation.id == identifier
                )
                .first()
            )

            if interp:
                return interp

            raise OracleError(
                f"Interpretation '{identifier}' not found in set {set_id}. "
                f"Please use a sequence number (1-{len(interpretations)}), "
                f"a slug, or a valid UUID."
            )

        return self._execute_db_operation(
            f"find interpretation {identifier} in set {interpretation_set_id}",
            _find_interpretation,
            interpretation_set_id,
            identifier,
        )

    def select_interpretation(
        self,
        interpretation_set_id: str,
        interpretation_identifier: str,
    ) -> Interpretation:
        """Select an interpretation.

        Args:
            interpretation_set_id: ID of the interpretation set.
            interpretation_identifier: Identifier of the interpretation
                                       (sequence number, slug, or UUID).

        Returns:
            Interpretation: The selected interpretation.
        """
        # Find the interpretation using the flexible identifier
        interpretation = self.find_interpretation(
            interpretation_set_id, interpretation_identifier
        )

        def _select_interpretation(
            session: Session,
            interpretation_set_id: str,
            interpretation: Interpretation,
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

            # Clear any previously selected interpretations in this set
            for interp in (
                session.query(Interpretation)
                .filter(Interpretation.set_id == interpretation_set_id)
                .all()
            ):
                interp.is_selected = False

            # Mark this interpretation as selected
            interpretation.is_selected = True

            return interpretation

        return self._execute_db_operation(
            "select interpretation",
            _select_interpretation,
            interpretation_set_id,
            interpretation.id,
        )

    def add_interpretation_event(
        self,
        interpretation: Interpretation,
        custom_description: Optional[str] = None,
    ) -> Event:
        """Add an interpretation as an event.

        Args:
            interpretation: The interpretation to add as an event.
            custom_description: Optional custom description for the event.
                If not provided, uses "{title}: {description}".

        Returns:
            Event: The created event.
        """

        def _add_interpretation_event(
            session: Session,
            interpretation: Interpretation,
            custom_description: Optional[str],
        ) -> Event:
            # Access the interpretation_set relationship directly
            interp_set = interpretation.interpretation_set

            # Access the scene relationship from the interpretation set
            scene = interp_set.scene

            # Use custom description if provided, otherwise generate from interpretation
            description = (
                custom_description
                if custom_description is not None
                else f"{interpretation.title}: {interpretation.description}"
            )

            # Get the source for "oracle"
            oracle_source = (
                session.query(EventSource).filter(EventSource.name == "oracle").first()
            )
            if not oracle_source:
                raise OracleError("Oracle event source not found")

            event = self.event_manager.add_event(
                scene_id=scene.id,
                source="oracle",
                description=description,
                interpretation_id=interpretation.id,
            )
            return event

        return self._execute_db_operation(
            "add interpretation event",
            _add_interpretation_event,
            interpretation,
            custom_description,
        )
