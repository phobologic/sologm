"""Event management functionality."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.models.event import Event
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)


class EventManager(BaseManager[Event, Event]):
    """Manages event operations."""

    def add_event(
        self,
        game_id: str,
        scene_id: str,
        description: str,
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        """Add a new event to the specified scene.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.
            description: Description of the event.
            source: Source of the event (manual, oracle, dice).
            interpretation_id: Optional ID of the interpretation that created
                               this event.

        Returns:
            The created Event.

        Raises:
            EventError: If the game or scene is not found.
        """

        def _add_event(
            session: Session,
            game_id: str,
            scene_id: str,
            description: str,
            source: str,
            interpretation_id: Optional[str],
        ) -> Event:
            # Verify scene exists and belongs to the game
            from sologm.models.scene import Scene

            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise EventError(f"Scene {scene_id} not found in game {game_id}")

            # Verify game exists and scene belongs to game
            if scene.game_id != game_id:
                raise EventError(f"Scene {scene_id} does not belong to game {game_id}")

            # Create event
            event = Event.create(
                game_id=game_id,
                scene_id=scene_id,
                description=description,
                source=source,
                interpretation_id=interpretation_id,
            )

            session.add(event)
            session.flush()  # Generate ID before returning

            return event

        try:
            return self._execute_db_operation(
                "add event",
                _add_event,
                game_id,
                scene_id,
                description,
                source,
                interpretation_id,
            )
        except Exception as e:
            self.logger.error(f"Failed to add event: {str(e)}")
            raise EventError(f"Failed to add event: {str(e)}") from e

    def validate_active_context(
        self, game_manager: GameManager, scene_manager: SceneManager
    ) -> Tuple[str, str]:
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

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID.
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            The event if found, None otherwise
        """
        return self._execute_db_operation(
            "get event",
            lambda session: session.query(Event).filter(Event.id == event_id).first(),
        )

    def update_event(self, event_id: str, description: str) -> Event:
        """Update an event's description.
        
        Args:
            event_id: ID of the event to update
            description: New description for the event
            
        Returns:
            The updated event
            
        Raises:
            EventError: If the event is not found
        """
        def _update_event(session: Session) -> Event:
            event = session.query(Event).filter(Event.id == event_id).first()
            if not event:
                raise EventError(f"Event with ID '{event_id}' not found")
            
            event.description = description
            session.add(event)
            return event
            
        try:
            return self._execute_db_operation("update event", _update_event)
        except Exception as e:
            self.logger.error(f"Failed to update event: {str(e)}")
            raise EventError(f"Failed to update event: {str(e)}") from e

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

        def _list_events(
            session: Session, game_id: str, scene_id: str, limit: Optional[int]
        ) -> List[Event]:
            # Verify scene exists and belongs to the game
            from sologm.models.scene import Scene

            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise EventError(f"Scene {scene_id} not found in game {game_id}")

            # Verify game exists and scene belongs to game
            if scene.game_id != game_id:
                raise EventError(f"Scene {scene_id} does not belong to game {game_id}")

            # Query events
            query = (
                session.query(Event)
                .filter(Event.scene_id == scene_id, Event.game_id == game_id)
                .order_by(Event.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            return query.all()

        try:
            return self._execute_db_operation(
                "list events", _list_events, game_id, scene_id, limit
            )
        except Exception as e:
            self.logger.error(f"Failed to list events: {str(e)}")
            raise EventError(f"Failed to list events: {str(e)}") from e
