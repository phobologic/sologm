"""Event management functionality."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.storage.file_manager import FileManager
from sologm.utils.datetime_utils import (
    format_datetime,
    get_current_time,
    parse_datetime,
)
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents a game event."""

    id: str
    scene_id: str
    game_id: str
    description: str
    source: str  # manual, oracle, dice
    created_at: datetime


class EventManager:
    """Manages event operations."""

    def __init__(self, file_manager: Optional[FileManager] = None):
        """Initialize the event manager.

        Args:
            file_manager: Optional FileManager instance to use.
                If not provided, a new one will be created.
        """
        self.file_manager = file_manager or FileManager()

    def add_event(
        self, game_id: str, scene_id: str, description: str, source: str = "manual"
    ) -> Event:
        """Add a new event to the specified scene.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.
            description: Description of the event.
            source: Source of the event (manual, oracle, dice).

        Returns:
            The created Event.

        Raises:
            EventError: If the game or scene is not found.
        """
        # Verify scene exists
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self.file_manager.read_yaml(scene_path)
        if not scene_data:
            logger.error(f"Scene {scene_id} not found in game {game_id}")
            raise EventError(f"Scene {scene_id} not found in game {game_id}")

        # Create event
        event_id = f"event-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.debug(f"Creating new event {event_id}")
        event = Event(
            id=event_id,
            scene_id=scene_id,
            game_id=game_id,
            description=description,
            source=source,
            created_at=get_current_time(),
        )

        # Load existing events
        events_path = self.file_manager.get_events_path(game_id, scene_id)
        events_data = self.file_manager.read_yaml(events_path)

        if not events_data:
            events_data = {"events": []}

        # Add new event
        events_data["events"].append(
            {
                "id": event.id,
                "scene_id": event.scene_id,
                "game_id": event.game_id,
                "description": event.description,
                "source": event.source,
                "created_at": format_datetime(event.created_at),
            }
        )

        # Save events
        logger.debug(f"Saving event {event.id} to {events_path}")
        self.file_manager.write_yaml(events_path, events_data)

        return event

    def validate_active_context(
        self, game_manager: GameManager, scene_manager: SceneManager
    ) -> tuple[str, str]:
        """Validate and return active game and scene IDs.

        Returns:
            Tuple of (game_id, scene_id)

        Raises:
            EventError: If no active game or scene is found
        """
        game = game_manager.get_active_game()
        if not game:
            raise EventError("No active game. Use 'sologm game activate' to set one.")

        scene = scene_manager.get_active_scene(game.id)
        if not scene:
            raise EventError("No current scene. Create one with 'sologm scene create'.")

        return game.id, scene.id

    def list_events(
        self, game_id: str, scene_id: str, limit: Optional[int] = None
    ) -> List[Event]:
        """List events for the specified scene.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.
            limit: Optional limit on number of events to return.
                If provided, returns the most recent events.

        Returns:
            List of Event objects.

        Raises:
            EventError: If the game or scene is not found.
        """
        # Verify scene exists
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self.file_manager.read_yaml(scene_path)
        if not scene_data:
            logger.error(f"Scene {scene_id} not found in game {game_id}")
            raise EventError(f"Scene {scene_id} not found in game {game_id}")

        # Load events
        events_path = self.file_manager.get_events_path(game_id, scene_id)
        logger.debug(f"Loading events from {events_path}")
        events_data = self.file_manager.read_yaml(events_path)

        if not events_data:
            logger.debug("No events found")
            return []

        # Convert to Event objects
        events = []
        for event_data in events_data.get("events", []):
            events.append(
                Event(
                    id=event_data["id"],
                    scene_id=event_data["scene_id"],
                    # Use game_id param as fallback
                    game_id=event_data.get("game_id", game_id),
                    description=event_data["description"],
                    source=event_data["source"],
                    created_at=parse_datetime(event_data["created_at"]),
                )
            )

        # Sort by created_at descending
        events.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit if provided
        if limit is not None:
            events = events[:limit]

        return events
