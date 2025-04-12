"""Event management functionality."""

import logging
from typing import Any, Dict, List, Optional

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

    def get_active_context(self) -> Dict[str, Any]:
        """Get the active game, act, and scene context.

        Returns:
            Dictionary containing 'game', 'act', and 'scene' keys with their
            respective objects.

        Raises:
            EventError: If no active game, act, or scene is found.
        """
        try:
            return self.scene_manager.get_active_context()
        except Exception as e:
            raise EventError(str(e)) from e

    def validate_active_context(self) -> tuple[str, str]:
        """Validate and return active game and scene IDs.

        Returns:
            Tuple of (game_id, scene_id)

        Raises:
            EventError: If no active game, act, or scene is found
        """
        try:
            context = self.get_active_context()
            return context["game"].id, context["scene"].id
        except Exception as e:
            raise EventError(str(e)) from e

    def _get_scene(self, session: Session, scene_id: str) -> Scene:
        """Get a scene by ID, raising EventError if not found.

        Args:
            session: SQLAlchemy session
            scene_id: ID of the scene to validate

        Returns:
            The validated Scene object

        Raises:
            EventError: If the scene doesn't exist
        """
        return self.get_entity_or_error(
            session, Scene, scene_id, EventError, f"Scene {scene_id} not found"
        )

    def _get_source(self, session: Session, source_name: str) -> EventSource:
        """Get an event source by name, raising EventError if not found.

        Args:
            session: SQLAlchemy session
            source_name: Name of the source to validate

        Returns:
            The validated EventSource object

        Raises:
            EventError: If the source doesn't exist
        """
        try:
            return self.get_entity_or_error(
                session,
                EventSource,
                source_name,
                EventError,
                f"Invalid source '{source_name}'",
                lambda q, val: q.filter(EventSource.name == val),
            )
        except EventError:
            # If not found, provide more helpful error with valid sources
            valid_sources = [s.name for s in session.query(EventSource).all()]
            raise EventError(
                f"Invalid source '{source_name}'. Valid sources: {', '.join(valid_sources)}"
            )

    def add_event(
        self,
        description: str,
        scene_id: Optional[str] = None,
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        """Add a new event to the specified scene or active scene.

        Args:
            description: Description of the event.
            scene_id: ID of the scene. If None, uses the active scene.
            source: Source name of the event (manual, oracle, dice).
            interpretation_id: Optional ID of the interpretation that created
                               this event.

        Returns:
            The created Event.

        Raises:
            EventError: If the scene is not found or source is invalid.
        """
        if scene_id is None:
            _, scene_id = self.validate_active_context()

        def _add_event(
            session: Session,
            scene_id: str,
            description: str,
            source: str,
            interpretation_id: Optional[str],
        ) -> Event:
            # Validate scene exists
            self._get_scene(session, scene_id)

            # Validate source exists
            event_source = self._get_source(session, source)

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
            self._handle_operation_error("add event", e, EventError)

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            The event if found, None otherwise
        """
        try:
            return self._execute_db_operation(
                "get event",
                lambda session: session.query(Event)
                .filter(Event.id == event_id)
                .first(),
            )
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

        def _update_event(
            session: Session, event_id: str, description: str, source: Optional[str]
        ) -> Event:
            event = self.get_entity_or_error(
                session,
                Event,
                event_id,
                EventError,
                f"Event with ID '{event_id}' not found",
            )

            event.description = description
            if source is not None:
                # Validate source exists
                event_source = self._get_source(session, source)
                event.source_id = event_source.id

            session.add(event)
            return event

        try:
            return self._execute_db_operation(
                "update event", _update_event, event_id, description, source
            )
        except Exception as e:
            self._handle_operation_error("update event", e, EventError)

    def list_events(
        self, scene_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """List events for the specified scene or active scene.

        Args:
            scene_id: ID of the scene. If None, uses the active scene.
            limit: Optional limit on number of events to return.
                If provided, returns the most recent events.

        Returns:
            List of Event objects.

        Raises:
            EventError: If the scene is not found.
        """
        if scene_id is None:
            _, scene_id = self.validate_active_context()

        try:
            # Validate scene exists (in a separate operation)
            self._execute_db_operation(
                "validate scene", lambda session: self._get_scene(session, scene_id)
            )

            # Use list_entities for the actual query
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
        """
        try:
            return self.list_entities(EventSource, order_by="name")
        except Exception as e:
            self._handle_operation_error("get event sources", e, EventError)
