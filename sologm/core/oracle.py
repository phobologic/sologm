"""Oracle interpretation system for Solo RPG Helper."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar

from sologm.integrations.anthropic import AnthropicClient
from sologm.storage.file_manager import FileManager
from sologm.utils.errors import OracleError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def oracle_operation(operation_name: str) -> Callable:
    """Decorator for oracle operations with error handling.

    Args:
        operation_name: Name of the operation for error messages.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                logger.debug(f"Starting oracle operation: {operation_name}")
                result = func(*args, **kwargs)
                logger.debug(f"Completed oracle operation: {operation_name}")
                return result
            except Exception as e:
                logger.error(f"Failed to {operation_name}: {e}")
                raise OracleError(f"Failed to {operation_name}: {str(e)}") from e

        return wrapper

    return decorator


@dataclass
class Interpretation:
    """Represents a single oracle interpretation."""

    id: str
    title: str
    description: str
    created_at: datetime


@dataclass
class InterpretationSet:
    """Represents a set of oracle interpretations."""

    id: str
    scene_id: str
    context: str
    oracle_results: str
    interpretations: List[Interpretation]
    selected_interpretation: Optional[int]
    created_at: datetime


class OracleManager:
    """Manages oracle interpretation operations."""

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        anthropic_client: Optional[AnthropicClient] = None,
    ):
        """Initialize the oracle manager.

        Args:
            file_manager: Optional file manager instance.
            anthropic_client: Optional Anthropic client instance.
        """
        self.file_manager = file_manager or FileManager()
        self.anthropic_client = anthropic_client or AnthropicClient()

    def validate_active_context(self) -> tuple[str, str]:
        """Validate active game and scene exist.

        Returns:
            tuple[str, str]: game_id, scene_id

        Raises:
            OracleError: If game or scene not active
        """
        game_id = self.file_manager.get_active_game_id()
        if not game_id:
            raise OracleError("No active game found")

        scene_id = self.file_manager.get_active_scene_id(game_id)
        if not scene_id:
            raise OracleError("No active scene found")

        return game_id, scene_id

    def get_current_interpretation(self, game_id: str) -> Optional[dict]:
        """Get current interpretation data if it exists.

        Args:
            game_id: ID of the game to check

        Returns:
            Optional[dict]: Current interpretation data or None
        """
        game_data = self._read_game_data(game_id)
        return game_data.get("current_interpretation")

    def get_interpretation_set(
        self, game_id: str, scene_id: str, set_id: str
    ) -> InterpretationSet:
        """Get an interpretation set by ID.

        Args:
            game_id: ID of the game
            scene_id: ID of the scene
            set_id: ID of the interpretation set

        Returns:
            InterpretationSet: The requested interpretation set

        Raises:
            OracleError: If set not found
        """
        interp_path = Path(
            self.file_manager.get_interpretations_dir(game_id, scene_id),
            f"{set_id}.yaml",
        )
        try:
            data = self.file_manager.read_yaml(interp_path)
            return InterpretationSet(
                id=data["id"],
                scene_id=data["scene_id"],
                context=data["context"],
                oracle_results=data["oracle_results"],
                interpretations=[
                    self._create_interpretation(
                        interpretation_id=i["id"],
                        title=i["title"],
                        description=i["description"],
                        created_at=datetime.fromisoformat(i["created_at"]),
                    )
                    for i in data["interpretations"]
                ],
                selected_interpretation=data["selected_interpretation"],
                created_at=datetime.fromisoformat(data["created_at"]),
            )
        except Exception as e:
            raise OracleError(f"Failed to load interpretation set: {e}")

    def _read_game_data(self, game_id: str) -> dict:
        """Read and return game data.

        Args:
            game_id: ID of the game to read.

        Returns:
            dict: The game data.
        """
        logger.debug(f"Reading game data for game_id: {game_id}")
        return self.file_manager.read_yaml(self.file_manager.get_game_path(game_id))

    def _read_scene_data(self, game_id: str, scene_id: str) -> dict:
        """Read and return scene data.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene to read.

        Returns:
            dict: The scene data.
        """
        logger.debug(f"Reading scene data for scene_id: {scene_id}")
        return self.file_manager.read_yaml(
            self.file_manager.get_scene_path(game_id, scene_id)
        )

    def _read_events_data(self, game_id: str, scene_id: str) -> dict:
        """Read and return events data.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.

        Returns:
            dict: The events data.
        """
        logger.debug(f"Reading events data for scene_id: {scene_id}")
        return self.file_manager.read_yaml(
            self.file_manager.get_events_path(game_id, scene_id)
        )

    def _create_interpretation(
        self, interpretation_id: str, title: str, description: str, created_at: datetime
    ) -> Interpretation:
        """Create an Interpretation object.

        Args:
            id: Interpretation ID.
            title: Interpretation title.
            description: Interpretation description.
            created_at: Creation timestamp.

        Returns:
            Interpretation: The created interpretation object.
        """
        logger.debug(f"Creating interpretation object with id: {id}")
        return Interpretation(
            id=interpretation_id, title=title, description=description,
            created_at=created_at
        )

    def _validate_interpretation_set(self, interp_data: dict, set_id: str) -> None:
        """Validate interpretation set data.

        Args:
            interp_data: The interpretation set data to validate.
            set_id: ID of the interpretation set.

        Raises:
            OracleError: If validation fails.
        """
        logger.debug(f"Validating interpretation set: {set_id}")
        if not interp_data:
            raise OracleError(f"Interpretation set {set_id} not found")
        if "interpretations" not in interp_data:
            raise OracleError(
                "Invalid interpretation set format: missing interpretations"
            )

    def _create_event_data(
        self, events_data: dict, interpretation: Interpretation, scene_id: str
    ) -> dict:
        """Create event data from interpretation.

        Args:
            events_data: Existing events data.
            interpretation: The interpretation to create event from.
            scene_id: ID of the scene.

        Returns:
            dict: The created event data.
        """
        logger.debug("Creating event data from interpretation")
        return {
            "id": f"event-{len(events_data['events'])+1}",
            "description": f"{interpretation.title}: {interpretation.description}",
            "source": "oracle",
            "scene_id": scene_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_prompt(
        self,
        game_description: str,
        scene_description: str,
        recent_events: List[str],
        context: str,
        oracle_results: str,
        count: int,
    ) -> str:
        """Build the prompt for Claude API.

        Args:
            game_description: Description of the current game.
            scene_description: Description of the current scene.
            recent_events: List of recent events in the scene.
            context: User's question or context.
            oracle_results: Oracle results to interpret.
            count: Number of interpretations to generate.

        Returns:
            str: The formatted prompt.
        """
        events_text = "No recent events"
        if recent_events:
            events_text = "\n".join([f"- {event}" for event in recent_events])

        return f"""You are interpreting oracle results for a solo RPG player.

Game: {game_description}
Current Scene: {scene_description}
Recent Events:
{events_text}

Player's Question/Context: {context}
Oracle Results: {oracle_results}

Please provide {count} different interpretations of these oracle results.
Each interpretation should make sense in the context of the game and scene.
Be creative but consistent with the established narrative.

Format your response exactly as follows:

=== BEGIN INTERPRETATIONS ===

--- INTERPRETATION 1 ---
TITLE: Short title for the interpretation
DESCRIPTION: Detailed description of interpretation idea
--- END INTERPRETATION 1 ---

[and so on for each interpretation]

=== END INTERPRETATIONS ===
"""

    def _parse_interpretations(self, response_text: str) -> List[dict]:
        """Parse interpretations from Claude's response.

        Args:
            response_text: Raw response from Claude API.

        Returns:
            List[dict]: List of parsed interpretations.
        """
        import re

        pattern = (
            r"--- INTERPRETATION (\d+) ---\nTITLE: (.*?)\n"
            r"DESCRIPTION: (.*?)\n--- END INTERPRETATION \1 ---"
        )
        matches = re.findall(pattern, response_text, re.DOTALL)

        interpretations = []
        for _, title, description in matches:
            interpretations.append(
                {"title": title.strip(), "description": description.strip()}
            )

        return interpretations

    @oracle_operation("get interpretations")
    def get_interpretations(
        self,
        game_id: str,
        scene_id: str,
        context: str,
        oracle_results: str,
        count: int = 3,
        retry_attempt: int = 0,
    ) -> InterpretationSet:
        """Get interpretations for oracle results.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            context: User's question or context.
            oracle_results: Oracle results to interpret.
            count: Number of interpretations to generate.
            retry_attempt: Number of retry attempts made.

        Returns:
            InterpretationSet: Set of generated interpretations.
        """
        # Get game and scene details
        game_data = self._read_game_data(game_id)
        scene_data = self._read_scene_data(game_id, scene_id)
        events_data = self._read_events_data(game_id, scene_id)

        # Get recent events
        recent_events = [
            event["description"]
            for event in sorted(
                events_data.get("events", []),
                key=lambda x: x["created_at"],
                reverse=True,
            )[:5]
        ]

        # Build prompt and get response
        prompt = self._build_prompt(
            game_data["description"],
            scene_data["description"],
            recent_events,
            context,
            oracle_results,
            count,
        )

        # If this is a retry, modify the prompt
        if retry_attempt > 0:
            prompt = prompt.replace(
                "Please provide",
                f"This is retry attempt #{retry_attempt + 1}. Please provide DIFFERENT",
            )

        # Get and parse response
        logger.debug("Sending prompt to Claude API")
        response = self.anthropic_client.send_message(prompt)
        parsed = self._parse_interpretations(response)
        logger.debug(f"Found {len(parsed)} interpretations")

        # Create interpretation objects
        now = datetime.now(timezone.utc)
        interpretations = [
            self._create_interpretation(
                interpretation_id=f"interp-{i+1}",
                title=interp["title"],
                description=interp["description"],
                created_at=now,
            )
            for i, interp in enumerate(parsed)
        ]

        # Create interpretation set
        interp_set = InterpretationSet(
            id=self.file_manager.create_timestamp_filename("interp", "")[:-5],
            scene_id=scene_id,
            context=context,
            oracle_results=oracle_results,
            interpretations=interpretations,
            selected_interpretation=None,
            created_at=now,
        )

        # Update game's current interpretation
        game_data["current_interpretation"] = {
            "id": interp_set.id,
            "context": context,
            "results": oracle_results,
            "retry_count": retry_attempt,
        }
        self.file_manager.write_yaml(
            self.file_manager.get_game_path(game_id), game_data
        )

        # Save interpretation set
        interp_path = Path(
            self.file_manager.get_interpretations_dir(game_id, scene_id),
            f"{interp_set.id}.yaml",
        )
        self.file_manager.write_yaml(
            interp_path,
            {
                "id": interp_set.id,
                "scene_id": scene_id,
                "context": context,
                "oracle_results": oracle_results,
                "created_at": interp_set.created_at.isoformat(),
                "selected_interpretation": None,
                "retry_attempt": retry_attempt,
                "interpretations": [
                    {
                        "id": i.id,
                        "title": i.title,
                        "description": i.description,
                        "created_at": i.created_at.isoformat(),
                    }
                    for i in interpretations
                ],
            },
        )

        return interp_set

    @oracle_operation("select interpretation")
    def select_interpretation(
        self,
        game_id: str,
        scene_id: str,
        interpretation_set_id: str,
        interpretation_id: str,
        add_event: bool = True,
    ) -> Interpretation:
        """Select an interpretation and optionally add it as an event.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            interpretation_set_id: ID of the interpretation set.
            interpretation_id: ID of the interpretation to select.
            add_event: Whether to add the interpretation as an event.

        Returns:
            Interpretation: The selected interpretation.
        """
        # Load and validate interpretation set
        interp_path = Path(
            self.file_manager.get_interpretations_dir(game_id, scene_id),
            f"{interpretation_set_id}.yaml",
        )
        interp_data = self.file_manager.read_yaml(interp_path)

        # Validate interpretation data
        self._validate_interpretation_set(interp_data, interpretation_set_id)

        # Normalize interpretation ID
        if not interpretation_id.startswith("interp-"):
            interpretation_id = f"interp-{interpretation_id}"

        # Find selected interpretation
        selected = None
        selected_index = None
        for i, interp in enumerate(interp_data["interpretations"]):
            if interp["id"] == interpretation_id:
                selected = self._create_interpretation(
                    interpretation_id=interp["id"],
                    title=interp["title"],
                    description=interp["description"],
                    created_at=datetime.fromisoformat(interp["created_at"]),
                )
                selected_index = i
                break

        if not selected:
            raise OracleError(
                f"Interpretation {interpretation_id} not found in set "
                f"{interpretation_set_id}"
            )

        # Update interpretation set with selection
        interp_data["selected_interpretation"] = selected_index
        self.file_manager.write_yaml(interp_path, interp_data)

        # Only add as event if requested
        if add_event:
            self.add_interpretation_event(game_id, scene_id, selected)

        return selected

    @oracle_operation("add interpretation event")
    def add_interpretation_event(
        self, game_id: str, scene_id: str, interpretation: Interpretation
    ) -> None:
        """Add an interpretation as an event.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            interpretation: The interpretation to add as an event.
        """
        events_path = self.file_manager.get_events_path(game_id, scene_id)
        events_data = self._read_events_data(game_id, scene_id)

        if "events" not in events_data:
            events_data["events"] = []

        event_data = self._create_event_data(events_data, interpretation, scene_id)
        events_data["events"].append(event_data)

        self.file_manager.write_yaml(events_path, events_data)
