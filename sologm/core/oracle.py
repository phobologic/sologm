"""Oracle interpretation system for Solo RPG Helper."""

import logging
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.prompts.oracle import OraclePrompts
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene
from sologm.utils.errors import OracleError

if TYPE_CHECKING:
    from sologm.core.act import ActManager


logger = logging.getLogger(__name__)


class OracleManager(BaseManager[InterpretationSet, InterpretationSet]):
    """Manages oracle interpretation operations."""

    def __init__(
        self,
        session: Optional[Session] = None,
        anthropic_client: Optional[AnthropicClient] = None,
        scene_manager: Optional[SceneManager] = None,
        event_manager: Optional[EventManager] = None,
    ):
        """Initialize the oracle manager.

        Args:
            session: Optional database session.
            anthropic_client: Optional Anthropic client instance.
            scene_manager: Optional SceneManager instance.
            event_manager: Optional event manager instance.
        """
        super().__init__(session=session)

        # Store references to managers
        self._scene_manager = scene_manager
        self._event_manager = event_manager

        # If no anthropic_client is provided, create one
        if not anthropic_client:
            self.anthropic_client = AnthropicClient()
        else:
            self.anthropic_client = anthropic_client

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager if not provided."""
        return self._lazy_init_manager(
            "_scene_manager", "sologm.core.scene.SceneManager"
        )

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
        return self._lazy_init_manager(
            "_event_manager",
            "sologm.core.event.EventManager",
            scene_manager=self.scene_manager,
        )

    def get_active_context(self) -> Tuple[Scene, Act, Game]:
        """Get active scene, act, and game objects.

        Returns:
            Tuple containing (scene, act, game)

        Raises:
            OracleError: If no active scene, act, or game is found
        """
        self.logger.debug("Getting active context (scene, act, game)")

        try:
            # Get active game first
            game = self.game_manager.get_active_game()
            if not game:
                self.logger.error("No active game found")
                raise OracleError("No active game found")

            # Get active act from game
            if not game.has_active_act:
                self.logger.error(f"No active act found in game '{game.name}'")
                raise OracleError(f"No active act found in game '{game.name}'")

            act = game.active_act

            # Get active scene from act
            if not act.has_active_scene:
                self.logger.error(f"No active scene found in act '{act.title}'")
                raise OracleError(f"No active scene found in act '{act.title}'")

            scene = act.active_scene

            self.logger.debug(
                f"Found active context: game='{game.name}' (ID: {game.id}), "
                f"act='{act.title}' (ID: {act.id}), "
                f"scene='{scene.title}' (ID: {scene.id})"
            )

            return scene, act, game
        except OracleError:
            # Re-raise OracleError directly
            raise
        except Exception as e:
            self.logger.error(f"Error getting active context: {str(e)}")
            raise OracleError(f"Failed to get active context: {str(e)}") from e

    def get_interpretation_set(self, set_id: str) -> InterpretationSet:
        """Get an interpretation set by ID.

        Args:
            set_id: ID of the interpretation set

        Returns:
            InterpretationSet: The requested interpretation set

        Raises:
            OracleError: If set not found
        """
        self.logger.debug(f"Getting interpretation set by ID: {set_id}")

        def _get_interpretation_set(session: Session, set_id: str) -> InterpretationSet:
            interp_set = self.get_entity_or_error(
                session,
                InterpretationSet,
                set_id,
                OracleError,
                f"Interpretation set {set_id} not found",
            )
            self.logger.debug(
                f"Found interpretation set for scene ID: {interp_set.scene_id}"
            )
            return interp_set

        try:
            return self._execute_db_operation(
                f"get interpretation set {set_id}", _get_interpretation_set, set_id
            )
        except Exception as e:
            self.logger.error(f"Failed to get interpretation set {set_id}: {str(e)}")
            raise OracleError(f"Failed to get interpretation set: {str(e)}") from e

    def get_current_interpretation_set(
        self, scene_id: str
    ) -> Optional[InterpretationSet]:
        """Get current interpretation set for a scene if it exists.

        Args:
            scene_id: ID of the scene to check

        Returns:
            Optional[InterpretationSet]: Current interpretation set or None
        """
        self.logger.debug(
            f"Getting current interpretation set for scene ID: {scene_id}"
        )

        try:

            def _get_scene_with_current_set(
                session: Session,
            ) -> Optional[InterpretationSet]:
                scene = self.get_entity_or_error(
                    session, Scene, scene_id, OracleError, f"Scene {scene_id} not found"
                )

                # Explicitly refresh the scene with its interpretation_sets relationship
                session.refresh(scene, ["interpretation_sets"])

                # Use the scene's current_interpretation_set property
                current_set = scene.current_interpretation_set

                if current_set:
                    self.logger.debug(
                        f"Found current interpretation set ID: {current_set.id}"
                    )
                else:
                    self.logger.debug(
                        f"No current interpretation set found for scene: {scene.title}"
                    )

                return current_set

            return self._execute_db_operation(
                f"get current interpretation set for scene {scene_id}",
                _get_scene_with_current_set,
            )
        except OracleError:
            # If scene not found, just return None
            self.logger.debug(f"Scene {scene_id} not found, returning None")
            return None
        except Exception as e:
            self.logger.error(f"Error getting current interpretation set: {str(e)}")
            # For this method, we'll return None on error rather than raising
            return None

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
        self.logger.debug(
            f"Getting most recent interpretation for scene ID: {scene_id}"
        )

        def _get_most_recent_interpretation(
            session: Session, scene_id: str
        ) -> Optional[Tuple[InterpretationSet, Interpretation]]:
            try:
                # Get the scene first
                scene = self.get_entity_or_error(
                    session, Scene, scene_id, OracleError, f"Scene {scene_id} not found"
                )

                # Explicitly refresh the scene with its relationships
                session.refresh(scene, ["interpretation_sets"])

                # Use scene's selected_interpretations property
                selected_interpretations = scene.selected_interpretations

                if not selected_interpretations:
                    self.logger.debug(
                        f"No selected interpretations found for scene: {scene.title}"
                    )
                    return None

                # Get the most recent one
                most_recent = selected_interpretations[
                    0
                ]  # Assuming they're ordered by created_at desc
                interp_set = most_recent.interpretation_set

                self.logger.debug(
                    f"Found most recent interpretation: '{most_recent.title}' "
                    f"(ID: {most_recent.id}) in set ID: {interp_set.id}"
                )

                return (interp_set, most_recent)
            except OracleError:
                # If scene not found, return None
                self.logger.debug(f"Scene {scene_id} not found, returning None")
                return None

        try:
            result = self._execute_db_operation(
                "get most recent interpretation",
                _get_most_recent_interpretation,
                scene_id,
            )

            if result:
                interp_set, interp = result
                self.logger.debug(
                    f"Returning interpretation set ID: {interp_set.id} and "
                    f"interpretation ID: {interp.id}"
                )
            else:
                self.logger.debug("No interpretation found, returning None")

            return result
        except Exception as e:
            self.logger.error(f"Error getting most recent interpretation: {str(e)}")
            return None

    def _build_prompt(
        self,
        scene: Scene,
        context: str,
        oracle_results: str,
        count: int,
        previous_interpretations: Optional[List[dict]] = None,
        retry_attempt: int = 0,
    ) -> str:
        """Build the prompt for Claude API.

        Args:
            scene: Scene object with loaded relationships
            context: User's question or context
            oracle_results: Oracle results to interpret
            count: Number of interpretations to generate
            previous_interpretations: Optional list of previous interpretations to avoid
            retry_attempt: Number of retry attempts made

        Returns:
            str: The formatted prompt
        """
        return OraclePrompts.build_interpretation_prompt(
            scene,
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
        # Get active scene, act, and game
        scene, _, _ = self.get_active_context()

        # Build and return the prompt
        return self._build_prompt(
            scene,
            context,
            oracle_results,
            count,
        )

    # Method removed as it's now integrated into get_interpretations

    def _get_max_retries(self) -> int:
        """Get the maximum number of retries from configuration.

        Returns:
            int: Maximum number of retries
        """
        from sologm.utils.config import get_config

        config = get_config()
        return int(config.get("oracle_retries", 2))

    def _get_previous_interpretations(
        self, session: Session, previous_set_id: str
    ) -> Optional[List[Dict[str, str]]]:
        """Get previous interpretations for a set.

        Args:
            session: Database session
            previous_set_id: ID of the previous interpretation set

        Returns:
            Optional list of interpretation dictionaries
        """
        self.logger.debug(
            f"Getting previous interpretations for set ID: {previous_set_id}"
        )

        try:
            # Get the interpretation set
            interp_set = self.get_entity_or_error(
                session,
                InterpretationSet,
                previous_set_id,
                OracleError,
                f"Interpretation set {previous_set_id} not found",
            )

            # Use the relationship to get interpretations
            if not interp_set.interpretations:
                self.logger.debug(f"No interpretations found in set {previous_set_id}")
                return None

            # Convert to dictionaries
            previous_interpretations = [
                {
                    "title": interp.title,
                    "description": interp.description,
                }
                for interp in interp_set.interpretations
            ]

            self.logger.debug(
                f"Found {len(previous_interpretations)} previous interpretations"
            )
            return previous_interpretations
        except OracleError:
            # Re-raise OracleError
            raise
        except Exception as e:
            self.logger.error(f"Error getting previous interpretations: {str(e)}")
            return None

    def _clear_current_interpretation_sets(
        self, session: Session, scene_id: str
    ) -> None:
        """Clear any current interpretation sets for a scene.

        Args:
            session: Database session
            scene_id: ID of the scene
        """
        self.logger.debug(
            f"Clearing current interpretation sets for scene ID: {scene_id}"
        )

        # Get the scene
        scene = self.get_entity_or_error(
            session, Scene, scene_id, OracleError, f"Scene {scene_id} not found"
        )

        # Refresh the scene with specific relationship
        session.refresh(scene, ["interpretation_sets"])

        # Get current interpretation set using the scene relationship
        current_set = scene.current_interpretation_set

        if current_set:
            self.logger.debug(
                f"Clearing current flag on interpretation set ID: {current_set.id}"
            )
            current_set.is_current = False
        else:
            self.logger.debug("No current interpretation sets found")

    def _parse_interpretations(self, response_text: str) -> List[dict]:
        """Parse interpretations from Claude's response using Markdown format.

        Args:
            response_text: Raw response from Claude API.

        Returns:
            List[dict]: List of parsed interpretations.
        """
        self.logger.debug(
            f"Parsing interpretations from response of length {len(response_text)}"
        )

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

        self.logger.debug(f"Parsed {len(interpretations)} interpretations")
        return interpretations

    def get_interpretations(
        self,
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
        self.logger.debug(
            f"Getting interpretations: scene_id={scene_id}, context='{context}', "
            f"oracle_results='{oracle_results}', count={count}, "
            f"retry_attempt={retry_attempt}, max_retries={max_retries or 'from config'}, "
            f"previous_set_id={previous_set_id or 'None'}"
        )

        # If this is a retry but no previous_set_id was provided,
        # try to find the current interpretation set for this scene
        if retry_attempt > 0 and previous_set_id is None:
            current_set = self.get_current_interpretation_set(scene_id)
            if current_set:
                previous_set_id = current_set.id
                self.logger.debug(
                    f"Using current set ID as previous set: {previous_set_id}"
                )

        # Get max_retries from config if not provided
        if max_retries is None:
            max_retries = self._get_max_retries()
            self.logger.debug(f"Using max_retries from config: {max_retries}")

        def _get_interpretations(session: Session) -> InterpretationSet:
            # Get scene using BaseManager helper
            scene = self.get_entity_or_error(
                session, Scene, scene_id, OracleError, f"Scene {scene_id} not found"
            )
            self.logger.debug(f"Found scene: {scene.title} (ID: {scene.id})")

            # Try to get interpretations with automatic retry
            for attempt in range(retry_attempt, retry_attempt + max_retries + 1):
                self.logger.debug(
                    f"Attempt {attempt + 1}/{retry_attempt + max_retries + 1}"
                )

                try:
                    # Get previous interpretations if this is a retry
                    previous_interpretations = None
                    if attempt > 0 and previous_set_id:
                        previous_interpretations = self._get_previous_interpretations(
                            session, previous_set_id
                        )

                    # Build prompt and get response
                    prompt = self._build_prompt(
                        scene,
                        context,
                        oracle_results,
                        count,
                        previous_interpretations,
                        attempt,
                    )
                    self.logger.debug(f"Built prompt with {len(prompt)} characters")

                    # Get response from AI
                    try:
                        self.logger.debug("Sending prompt to Claude API")
                        response = self.anthropic_client.send_message(prompt)
                        self.logger.debug(
                            f"Received response with {len(response)} characters"
                        )
                    except Exception as e:
                        self.logger.error(f"Error from AI service: {str(e)}")
                        raise OracleError(
                            f"Failed to get interpretations from AI service: {str(e)}"
                        ) from e

                    # Parse interpretations
                    parsed = self._parse_interpretations(response)
                    self.logger.debug(f"Parsed {len(parsed)} interpretations")

                    # If parsing succeeded, create and return interpretation set
                    if parsed:
                        # Clear any current interpretation sets for this scene
                        self._clear_current_interpretation_sets(session, scene_id)

                        # Create interpretation set
                        interp_set = InterpretationSet.create(
                            scene_id=scene_id,
                            context=context,
                            oracle_results=oracle_results,
                            retry_attempt=attempt,
                            is_current=True,
                        )
                        session.add(interp_set)
                        session.flush()  # Flush to get the ID
                        self.logger.debug(
                            f"Created interpretation set with ID: {interp_set.id}"
                        )

                        # Create interpretations
                        for i, interp_data in enumerate(parsed):
                            interpretation = Interpretation.create(
                                set_id=interp_set.id,
                                title=interp_data["title"],
                                description=interp_data["description"],
                                is_selected=False,
                            )
                            session.add(interpretation)
                            self.logger.debug(
                                f"Created interpretation {i + 1}/{len(parsed)}: "
                                f"'{interp_data['title']}' (ID: {interpretation.id})"
                            )

                        self.logger.info(
                            f"Successfully created interpretation set with {len(parsed)} "
                            f"interpretations for scene '{scene.title}'"
                        )
                        return interp_set

                    # If we're on the last attempt and parsing failed, raise error
                    if attempt >= retry_attempt + max_retries:
                        self.logger.warning(
                            "Failed to parse any interpretations from response"
                        )
                        self.logger.debug(f"Raw response: {response}")
                        raise OracleError(
                            f"Failed to parse interpretations from AI response after "
                            f"{attempt + 1} attempts"
                        )

                    # Otherwise, continue to next attempt
                    self.logger.warning(
                        f"Failed to parse interpretations (attempt "
                        f"{attempt + 1}/{retry_attempt + max_retries + 1}). "
                        f"Retrying automatically."
                    )

                except OracleError:
                    # Re-raise OracleErrors without wrapping them
                    raise

            # This should never be reached due to the error in the loop
            raise OracleError("Failed to get interpretations after maximum retries")

        try:
            return self._execute_db_operation(
                "get interpretations", _get_interpretations
            )
        except Exception as e:
            self.logger.error(f"Failed to get interpretations: {str(e)}")
            raise OracleError(f"Failed to get interpretations: {str(e)}") from e

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
        self.logger.debug(
            f"Finding interpretation with identifier '{identifier}' "
            f"in set ID: {interpretation_set_id}"
        )

        def _find_interpretation(
            session: Session, set_id: str, identifier: str
        ) -> Interpretation:
            # First get the interpretation set
            interp_set = self.get_entity_or_error(
                session,
                InterpretationSet,
                set_id,
                OracleError,
                f"Interpretation set {set_id} not found",
            )
            self.logger.debug(
                f"Found interpretation set for scene ID: {interp_set.scene_id}"
            )

            # Get all interpretations in the set
            interpretations = interp_set.interpretations

            if not interpretations:
                self.logger.error(f"No interpretations found in set {set_id}")
                raise OracleError(f"No interpretations found in set {set_id}")

            # Try to parse as sequence number
            try:
                seq_num = int(identifier)
                if 1 <= seq_num <= len(interpretations):
                    interp = interpretations[seq_num - 1]  # Convert to 0-based index
                    self.logger.debug(
                        f"Found interpretation by sequence number {seq_num}: "
                        f"'{interp.title}' (ID: {interp.id})"
                    )
                    return interp
            except ValueError:
                self.logger.debug(f"Identifier '{identifier}' is not a sequence number")
                pass  # Not a number, continue

            # Try as slug
            for interp in interpretations:
                if interp.slug == identifier:
                    self.logger.debug(
                        f"Found interpretation by slug '{identifier}': "
                        f"'{interp.title}' (ID: {interp.id})"
                    )
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
                self.logger.debug(
                    f"Found interpretation by UUID '{identifier}': "
                    f"'{interp.title}' (ID: {interp.id})"
                )
                return interp

            self.logger.error(
                f"Interpretation '{identifier}' not found in set {set_id}"
            )
            raise OracleError(
                f"Interpretation '{identifier}' not found in set {set_id}. "
                f"Please use a sequence number (1-{len(interpretations)}), "
                f"a slug, or a valid UUID."
            )

        try:
            return self._execute_db_operation(
                f"find interpretation {identifier} in set {interpretation_set_id}",
                _find_interpretation,
                interpretation_set_id,
                identifier,
            )
        except Exception as e:
            self.logger.error(f"Failed to find interpretation: {str(e)}")
            raise OracleError(f"Failed to find interpretation: {str(e)}") from e

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
        self.logger.debug(
            f"Selecting interpretation with identifier '{interpretation_identifier}' "
            f"in set ID: {interpretation_set_id}"
        )

        # Find the interpretation using the flexible identifier
        interpretation = self.find_interpretation(
            interpretation_set_id, interpretation_identifier
        )
        self.logger.debug(
            f"Found interpretation to select: '{interpretation.title}' "
            f"(ID: {interpretation.id})"
        )

        def _select_interpretation(
            session: Session,
            interpretation_id: str,
        ) -> Interpretation:
            # Get the interpretation
            interp = self.get_entity_or_error(
                session,
                Interpretation,
                interpretation_id,
                OracleError,
                f"Interpretation {interpretation_id} not found",
            )
            self.logger.debug(
                f"Retrieved interpretation: '{interp.title}' (ID: {interp.id})"
            )

            # Get the set
            interp_set = self.get_entity_or_error(
                session,
                InterpretationSet,
                interp.set_id,
                OracleError,
                f"Interpretation set {interp.set_id} not found",
            )
            self.logger.debug(f"Retrieved interpretation set ID: {interp_set.id}")

            # Clear any previously selected interpretations in this set
            for other_interp in interp_set.interpretations:
                if other_interp.is_selected:
                    self.logger.debug(
                        f"Clearing selection from interpretation: '{other_interp.title}' "
                        f"(ID: {other_interp.id})"
                    )
                    other_interp.is_selected = False

            # Mark this interpretation as selected
            interp.is_selected = True
            self.logger.debug(f"Marked interpretation '{interp.title}' as selected")

            return interp

        try:
            selected_interp = self._execute_db_operation(
                "select interpretation",
                _select_interpretation,
                interpretation.id,
            )
            self.logger.info(
                f"Successfully selected interpretation: '{selected_interp.title}' "
                f"(ID: {selected_interp.id})"
            )
            return selected_interp
        except Exception as e:
            self.logger.error(f"Failed to select interpretation: {str(e)}")
            raise OracleError(f"Failed to select interpretation: {str(e)}") from e

    def list_interpretation_sets(
        self,
        scene_id: Optional[str] = None,
        act_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[InterpretationSet]:
        """List interpretation sets for a scene or act.

        Args:
            scene_id: Optional ID of the scene to list interpretations from
            act_id: Optional ID of the act to list interpretations from
            limit: Maximum number of interpretation sets to return

        Returns:
            List of interpretation sets

        Raises:
            OracleError: If neither scene_id nor act_id is provided
        """
        self.logger.debug(
            f"Listing interpretation sets: scene_id={scene_id}, act_id={act_id}, limit={limit}"
        )

        if not scene_id and not act_id:
            self.logger.error("Neither scene_id nor act_id provided")
            raise OracleError("Either scene_id or act_id must be provided")

        def _list_interpretation_sets(
            session: Session,
            scene_id: Optional[str],
            act_id: Optional[str],
            limit: int,
        ) -> List[InterpretationSet]:
            query = session.query(InterpretationSet)

            if scene_id:
                # If scene_id is provided, filter by scene_id
                self.logger.debug(
                    f"Filtering interpretation sets by scene_id: {scene_id}"
                )
                query = query.filter(InterpretationSet.scene_id == scene_id)
            elif act_id:
                # If act_id is provided, filter by scenes in the act
                self.logger.debug(f"Filtering interpretation sets by act_id: {act_id}")
                query = query.join(Scene).filter(Scene.act_id == act_id)

            # Order by created_at descending to get most recent first
            query = query.order_by(InterpretationSet.created_at.desc())

            # Apply limit
            if limit:
                query = query.limit(limit)

            # Execute query
            interp_sets = query.all()
            self.logger.debug(f"Found {len(interp_sets)} interpretation sets")

            return interp_sets

        try:
            return self._execute_db_operation(
                "list interpretation sets",
                _list_interpretation_sets,
                scene_id,
                act_id,
                limit,
            )
        except Exception as e:
            self.logger.error(f"Failed to list interpretation sets: {str(e)}")
            raise OracleError(f"Failed to list interpretation sets: {str(e)}") from e

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
        self.logger.debug(
            f"Adding interpretation as event: interpretation_id={interpretation.id}, "
            f"custom_description={custom_description is not None}"
        )

        def _add_interpretation_event(
            session: Session,
            interpretation_id: str,
            custom_description: Optional[str],
        ) -> Event:
            # Get the interpretation
            interpretation = self.get_entity_or_error(
                session,
                Interpretation,
                interpretation_id,
                OracleError,
                f"Interpretation {interpretation_id} not found",
            )
            self.logger.debug(
                f"Found interpretation: '{interpretation.title}' (ID: {interpretation.id})"
            )

            # Use model relationships to get scene_id
            scene_id = interpretation.scene_id
            self.logger.debug(f"Using scene ID from interpretation: {scene_id}")

            # Use custom description if provided, otherwise generate from interpretation
            description = (
                custom_description
                if custom_description is not None
                else f"{interpretation.title}: {interpretation.description}"
            )
            self.logger.debug(f"Using description: '{description[:50]}...'")

            # Add event using event_manager
            event = self.event_manager.add_event(
                scene_id=scene_id,
                source="oracle",
                description=description,
                interpretation_id=interpretation.id,
            )
            self.logger.debug(f"Event created with ID: {event.id}")
            self.logger.info(
                f"Added interpretation as event: event_id={event.id}, "
                f"interpretation_id={interpretation.id}"
            )
            return event

        try:
            return self._execute_db_operation(
                "add interpretation event",
                _add_interpretation_event,
                interpretation.id,
                custom_description,
            )
        except Exception as e:
            self.logger.error(f"Failed to add interpretation as event: {str(e)}")
            raise OracleError(f"Failed to add interpretation as event: {str(e)}") from e
