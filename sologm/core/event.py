"""Event management functionality."""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.scene import Scene
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)


class EventManager(BaseManager[Event, Event]):
    """Manages event operations."""

    def get_active_context(
        self,
        game_manager: Optional[GameManager] = None,
        scene_manager: Optional[SceneManager] = None,
        act_manager: Optional[ActManager] = None,
    ) -> Dict[str, Any]:
        """Get the active game, act, and scene context.

        Args:
            game_manager: Optional GameManager instance. If not provided, a new one will be created.
            scene_manager: Optional SceneManager instance. If not provided, a new one will be created.
            act_manager: Optional ActManager instance. If not provided, a new one will be created.

        Returns:
            Dictionary containing 'game', 'act', and 'scene' keys with their respective objects.

        Raises:
            EventError: If no active game, act, or scene is found.
        """
        if game_manager is None:
            game_manager = GameManager(self._session)

        if scene_manager is None:
            scene_manager = SceneManager(self._session)

        try:
            return scene_manager.get_active_context(game_manager, act_manager)
        except Exception as e:
            raise EventError(str(e)) from e

    def validate_active_context(
        self,
        game_manager: GameManager,
        scene_manager: SceneManager,
        act_manager: Optional[ActManager] = None,
    ) -> tuple[str, str]:
        """Validate and return active game and scene IDs.

        Args:
            game_manager: GameManager instance
            scene_manager: SceneManager instance
            act_manager: Optional ActManager instance

        Returns:
            Tuple of (game_id, scene_id)

        Raises:
            EventError: If no active game, act, or scene is found
        """
        try:
            context = self.get_active_context(game_manager, scene_manager, act_manager)
            return context["game"].id, context["scene"].id
        except Exception as e:
            raise EventError(str(e)) from e

    def _validate_scene(self, session: Session, scene_id: str) -> Scene:
        """Validate that a scene exists.

        Args:
            session: SQLAlchemy session
            scene_id: ID of the scene to validate

        Returns:
            The validated Scene object

        Raises:
            EventError: If the scene doesn't exist
        """
        scene = session.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise EventError(f"Scene {scene_id} not found")
        return scene

    def _validate_source(self, session: Session, source: str) -> EventSource:
        """Validate that an event source exists.

        Args:
            session: SQLAlchemy session
            source: Name of the source to validate

        Returns:
            The validated EventSource object

        Raises:
            EventError: If the source doesn't exist
        """
        event_source = (
            session.query(EventSource).filter(EventSource.name == source).first()
        )
        if not event_source:
            valid_sources = [s.name for s in session.query(EventSource).all()]
            raise EventError(
                f"Invalid source '{source}'. Valid sources: {', '.join(valid_sources)}"
            )
        return event_source

    def add_event(
        self,
        scene_id: str,
        description: str,
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        """Add a new event to the specified scene.

        Args:
            scene_id: ID of the scene.
            description: Description of the event.
            source: Source name of the event (manual, oracle, dice).
            interpretation_id: Optional ID of the interpretation that created
                               this event.

        Returns:
            The created Event.

        Raises:
            EventError: If the scene is not found or source is invalid.
        """

        def _add_event(
            session: Session,
            scene_id: str,
            description: str,
            source: str,
            interpretation_id: Optional[str],
        ) -> Event:
            # Validate scene exists
            scene = self._validate_scene(session, scene_id)

            # Validate source exists
            event_source = self._validate_source(session, source)

            # Create event
            event = Event.create(
                scene_id=scene_id,
                description=description,
                source_id=event_source.id,
                interpretation_id=interpretation_id,
            )

            session.add(event)
            session.flush()  # Generate ID before returning

            return event

        try:
            return self._execute_db_operation(
                "add event",
                _add_event,
                scene_id,
                description,
                source,
                interpretation_id,
            )
        except Exception as e:
            self.logger.error(f"Failed to add event: {str(e)}")
            raise EventError(f"Failed to add event: {str(e)}") from e

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

    def update_event(
        self, event_id: str, description: str, source: Optional[str] = None
    ) -> Event:
        """Update an event's description and optionally its source.

        Args:
            event_id: ID of the event to update
            description: New description for the event
            source: Optional new source name for the event

        Returns:
            The updated event

        Raises:
            EventError: If the event is not found
        """

        def _update_event(
            session: Session, event_id: str, description: str, source: Optional[str]
        ) -> Event:
            event = session.query(Event).filter(Event.id == event_id).first()
            if not event:
                raise EventError(f"Event with ID '{event_id}' not found")

            event.description = description
            if source is not None:
                # Validate source exists
                event_source = self._validate_source(session, source)
                event.source_id = event_source.id

            session.add(event)
            return event

        try:
            return self._execute_db_operation(
                "update event", _update_event, event_id, description, source
            )
        except Exception as e:
            self.logger.error(f"Failed to update event: {str(e)}")
            raise EventError(f"Failed to update event: {str(e)}") from e

    def list_events(self, scene_id: str, limit: Optional[int] = None) -> List[Event]:
        """List events for the specified scene.

        Args:
            scene_id: ID of the scene.
            limit: Optional limit on number of events to return.
                If provided, returns the most recent events.

        Returns:
            List of Event objects.

        Raises:
            EventError: If the scene is not found.
        """

        def _list_events(
            session: Session, scene_id: str, limit: Optional[int]
        ) -> List[Event]:
            # Validate scene exists
            self._validate_scene(session, scene_id)

            # Query events
            query = (
                session.query(Event)
                .filter(Event.scene_id == scene_id)
                .order_by(Event.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            return query.all()

        try:
            return self._execute_db_operation(
                "list events", _list_events, scene_id, limit
            )
        except Exception as e:
            self.logger.error(f"Failed to list events: {str(e)}")
            raise EventError(f"Failed to list events: {str(e)}") from e

    def get_event_sources(self) -> List[EventSource]:
        """Get all available event sources.

        Returns:
            List of EventSource objects
        """
        return self._execute_db_operation(
            "get event sources",
            lambda session: session.query(EventSource).order_by(EventSource.name).all(),
        )
