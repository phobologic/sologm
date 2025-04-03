"""Oracle interpretation system for Solo RPG Helper."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sologm.integrations.anthropic import AnthropicClient
from sologm.storage.file_manager import FileManager
from sologm.utils.errors import OracleError

logger = logging.getLogger(__name__)


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

        Returns:
            InterpretationSet: Set of generated interpretations.

        Raises:
            OracleError: If interpretation generation fails.
        """
        try:
            logger.debug(f"Getting game data for game_id: {game_id}")
            # Get game and scene details
            game_data = self.file_manager.read_yaml(
                self.file_manager.get_game_path(game_id)
            )
            logger.debug("Successfully loaded game data")
            scene_data = self.file_manager.read_yaml(
                self.file_manager.get_scene_path(game_id, scene_id)
            )

            # Get recent events
            events_data = self.file_manager.read_yaml(
                self.file_manager.get_events_path(game_id, scene_id)
            )
            recent_events = [
                event["description"]
                for event in sorted(
                    events_data.get("events", []),
                    key=lambda x: x["created_at"],
                    reverse=True,
                )[:5]
            ]

            logger.debug("Building prompt for Claude API")
            # Build prompt and get response
            prompt = self._build_prompt(
                game_data["description"],
                scene_data["description"],
                recent_events,
                context,
                oracle_results,
                count,
            )

            # If this is a retry, modify the prompt to request different
            # interpretations
            if retry_attempt > 0:
                prompt = prompt.replace(
                    "Please provide",
                    f"This is retry attempt #{retry_attempt + 1}. Please "
                    "provide DIFFERENT",
                )

            logger.debug("Sending prompt to Claude API")
            response = self.anthropic_client.send_message(prompt)
            logger.debug("Parsing interpretations from response")
            parsed = self._parse_interpretations(response)
            logger.debug(f"Found {len(parsed)} interpretations")

            # Create interpretation objects
            now = datetime.now(timezone.utc)
            interpretations = [
                Interpretation(
                    id=f"interp-{i+1}",
                    title=interp["title"],
                    description=interp["description"],
                    created_at=now,
                )
                for i, interp in enumerate(parsed)
            ]

            # Create and save interpretation set
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
            game_data = self.file_manager.read_yaml(
                self.file_manager.get_game_path(game_id)
            )
            game_data["current_interpretation"] = {
                "id": interp_set.id,
                "context": context,
                "results": oracle_results,
                "retry_count": retry_attempt,
            }
            self.file_manager.write_yaml(
                self.file_manager.get_game_path(game_id), game_data
            )

            # Save interpretation set to file
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

        except Exception as e:
            logger.error(f"Failed to get interpretations: {e}")
            raise OracleError(f"Failed to get interpretations: {str(e)}")

    def select_interpretation(
        self,
        game_id: str,
        scene_id: str,
        interpretation_set_id: str,
        interpretation_id: str,
        add_event: bool = True,
    ) -> Interpretation:
        """Select an interpretation and add it as an event.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            interpretation_set_id: ID of the interpretation set.
            interpretation_id: ID of the interpretation to select.

        Returns:
            Interpretation: The selected interpretation.

        Raises:
            OracleError: If interpretation selection fails.
        """
        try:
            # Load and validate interpretation set
            interp_path = Path(
                self.file_manager.get_interpretations_dir(game_id, scene_id),
                f"{interpretation_set_id}.yaml",
            )
            interp_data = self.file_manager.read_yaml(interp_path)

            # Validate interpretation data exists
            if not interp_data:
                raise OracleError(
                    f"Interpretation set " f"{interpretation_set_id} not found"
                )

            if "interpretations" not in interp_data:
                raise OracleError(
                    "Invalid interpretation set format: " "missing interpretations"
                )

            # Find selected interpretation
            selected = None
            selected_index = None
            if not interpretation_id.startswith("interp-"):
                interpretation_id = f"interp-{interpretation_id}"
            for i, interp in enumerate(interp_data["interpretations"]):
                if interp["id"] == interpretation_id:
                    selected = Interpretation(
                        id=interp["id"],
                        title=interp["title"],
                        description=interp["description"],
                        created_at=datetime.fromisoformat(interp["created_at"]),
                    )
                    selected_index = i
                    break

            if not selected:
                raise OracleError(
                    f"Interpretation {interpretation_id} not "
                    f"found in set {interpretation_set_id}"
                )

            # Update interpretation set with selection
            interp_data["selected_interpretation"] = selected_index
            self.file_manager.write_yaml(interp_path, interp_data)

            # Only add as event if requested
            if add_event:
                self.add_interpretation_event(game_id, scene_id, selected)

            return selected

        except Exception as e:
            logger.error(f"Failed to select interpretation: {e}")
            raise OracleError(f"Failed to select interpretation: {str(e)}")

    def add_interpretation_event(
        self, game_id: str, scene_id: str, interpretation: Interpretation
    ) -> None:
        """Add an interpretation as an event.

        Args:
            game_id: ID of the current game.
            scene_id: ID of the current scene.
            interpretation: The interpretation to add as an event.
        """
        try:
            events_path = self.file_manager.get_events_path(game_id, scene_id)
            events_data = self.file_manager.read_yaml(events_path)

            if "events" not in events_data:
                events_data["events"] = []

            events_data["events"].append(
                {
                    "id": f"event-{len(events_data['events'])+1}",
                    "description": f"{interpretation.title}: "
                    f"{interpretation.description}",
                    "source": "oracle",
                    "scene_id": scene_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            self.file_manager.write_yaml(events_path, events_data)

        except Exception as e:
            logger.error(f"Failed to add interpretation event: {e}")
            raise OracleError(f"Failed to add interpretation event: {str(e)}")
