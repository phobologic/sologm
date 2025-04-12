"""Event management functionality."""

import logging
from typing import List, Optional

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

    def __init__(
        self,
        session: Optional[Session] = None,
        scene_manager: Optional[SceneManager] = None,
    ):
        """Initialize the EventManager.

        Args:
            session: Optional SQLAlchemy session
            scene_manager: Optional SceneManager instance
        """
        super().__init__(session)
        self._scene_manager = scene_manager

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager."""
        return self._lazy_init_manager(
            "_scene_manager", "sologm.core.scene.SceneManager"
        )

    @property
    def act_manager(self) -> ActManager:
        """Access act manager through scene manager."""
        return self.scene_manager.act_manager

    @property
    def game_manager(self) -> GameManager:
        """Access game manager through act manager."""
        return self.act_manager.game_manager

    def get_active_scene_id(self) -> str:
        """Get the active scene ID.

        Returns:
            The ID of the active scene

        Raises:
            EventError: If no active scene is found
        """
        try:
            context = self.scene_manager.get_active_context()
            return context["scene"].id
        except Exception as e:
            raise EventError(f"Failed to get active scene: {str(e)}") from e

    def _get_source_by_name(self, session: Session, source_name: str) -> EventSource:
        """Get an event source by name.

        Args:
            session: SQLAlchemy session
            source_name: Name of the source

        Returns:
            The EventSource object

        Raises:
            EventError: If the source doesn't exist
        """
        source = (
            session.query(EventSource).filter(EventSource.name == source_name).first()
        )
        if not source:
            valid_sources = [s.name for s in session.query(EventSource).all()]
            raise EventError(
                f"Invalid source '{source_name}'. Valid sources: {', '.join(valid_sources)}"
            )
        return source

    def add_event(
        self,
        description: str,
        scene_id: Optional[str] = None,
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        """Add a new event to a scene.

        Args:
            description: Description of the event
            scene_id: ID of the scene (uses active scene if None)
            source: Source name of the event (manual, oracle, dice)
            interpretation_id: Optional ID of the interpretation

        Returns:
            The created Event

        Raises:
            EventError: If the scene is not found or source is invalid
        """
        # Use active scene if none provided
        if scene_id is None:
            scene_id = self.get_active_scene_id()

        def _add_event(session: Session) -> Event:
            # Validate scene exists
            self.get_entity_or_error(
                session, Scene, scene_id, EventError, f"Scene {scene_id} not found"
            )

            # Get source
            event_source = self._get_source_by_name(session, source)

            # Create and return event
            event = Event.create(
                scene_id=scene_id,
                description=description,
                source_id=event_source.id,
                interpretation_id=interpretation_id,
            )

            session.add(event)
            session.flush()
            return event

        try:
            return self._execute_db_operation("add event", _add_event)
        except Exception as e:
            self._handle_operation_error("add event", e, EventError)

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            The event if found, None otherwise
        """
        try:

            def _get_event(session: Session) -> Optional[Event]:
                return session.query(Event).filter(Event.id == event_id).first()

            return self._execute_db_operation("get event", _get_event)
        except Exception as e:
            self._handle_operation_error("get event", e, EventError)

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

        def _update_event(session: Session) -> Event:
            # Get the event
            event = self.get_entity_or_error(
                session,
                Event,
                event_id,
                EventError,
                f"Event with ID '{event_id}' not found",
            )

            # Update description
            event.description = description

            # Update source if provided
            if source is not None:
                event_source = self._get_source_by_name(session, source)
                event.source_id = event_source.id

            return event

        try:
            return self._execute_db_operation("update event", _update_event)
        except Exception as e:
            self._handle_operation_error("update event", e, EventError)

    def list_events(
        self, scene_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """List events for a scene.

        Args:
            scene_id: ID of the scene (uses active scene if None)
            limit: Maximum number of events to return

        Returns:
            List of Event objects

        Raises:
            EventError: If the scene is not found
        """
        # Use active scene if none provided
        if scene_id is None:
            scene_id = self.get_active_scene_id()

        try:
            # Validate scene exists
            def _validate_scene(session: Session) -> None:
                self.get_entity_or_error(
                    session, Scene, scene_id, EventError, f"Scene {scene_id} not found"
                )

            self._execute_db_operation("validate scene", _validate_scene)

            # List events
            return self.list_entities(
                Event,
                filters={"scene_id": scene_id},
                order_by="created_at",
                order_direction="desc",
                limit=limit,
            )
        except Exception as e:
            self._handle_operation_error("list events", e, EventError)

    def get_event_sources(self) -> List[EventSource]:
        """Get all available event sources.

        Returns:
            List of EventSource objects

        Raises:
            EventError: If there was an error retrieving the sources
        """
        try:
            return self.list_entities(EventSource, order_by="name")
        except Exception as e:
            self._handle_operation_error("get event sources", e, EventError)
