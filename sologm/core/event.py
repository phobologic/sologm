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
            session: Optional database session for testing or CLI command injection
            scene_manager: Optional SceneManager instance
        """
        super().__init__(session=session)
        self._scene_manager = scene_manager

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager."""
        return self._lazy_init_manager(
            "_scene_manager", "sologm.core.scene.SceneManager", session=self._session
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
            GameError: If there's an issue retrieving the active game
        """
        self.logger.debug("Getting active scene ID")

        # Get the active game first
        game = self.game_manager.get_active_game()
        if not game:
            self.logger.error("No active game found")
            raise EventError("No active game found")

        # Use the model hierarchy to get the active scene
        if not game.has_active_scene:
            self.logger.error("No active scene found in the active game")
            raise EventError("No active scene found in the active game")

        scene_id = game.active_scene.id
        self.logger.debug(f"Active scene ID: {scene_id}")
        return scene_id

    def validate_active_context(self) -> tuple[str, str]:
        """Validate active game, act, and scene context.

        Returns:
            Tuple of (game_id, scene_id)

        Raises:
            EventError: If no active game, act, or scene
            SceneError: If there's an issue with the scene context
            ActError: If there's an issue with the act
        """
        self.logger.debug("Validating active context from EventManager")

        # Use the scene_manager to validate the active context
        act_id, scene = self.scene_manager.validate_active_context()

        # Get the game_id from the act
        act = self.act_manager.get_act(act_id)
        game_id = act.game_id

        self.logger.debug(
            f"Active context validated: game={game_id}, act={act_id}, scene={scene.id}"
        )
        return game_id, scene.id

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
        self.logger.debug(f"Getting event source by name: {source_name}")

        # Query for the source
        source = (
            session.query(EventSource).filter(EventSource.name == source_name).first()
        )

        # If not found, provide helpful error with valid sources
        if not source:
            valid_sources = [s.name for s in session.query(EventSource).all()]
            error_msg = f"Invalid source '{source_name}'. Valid sources: {', '.join(valid_sources)}"
            self.logger.error(error_msg)
            raise EventError(error_msg)

        self.logger.debug(f"Found source: {source.name} (ID: {source.id})")
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
        self.logger.debug(
            f"Adding event: description='{description[:30]}...', "
            f"scene_id={scene_id or 'active'}, source={source}, "
            f"interpretation_id={interpretation_id or 'None'}"
        )

        # Use active scene if none provided
        if scene_id is None:
            scene_id = self.get_active_scene_id()
            self.logger.debug(f"Using active scene ID: {scene_id}")

        def _add_event(session: Session) -> Event:
            # Validate scene exists
            scene = self.get_entity_or_error(
                session, Scene, scene_id, EventError, f"Scene {scene_id} not found"
            )
            self.logger.debug(f"Found scene: {scene.title} (ID: {scene.id})")

            # Get source
            event_source = self._get_source_by_name(session, source)
            self.logger.debug(
                f"Using source: {event_source.name} (ID: {event_source.id})"
            )

            # Create event
            event = Event.create(
                scene_id=scene_id,
                description=description,
                source_id=event_source.id,
                interpretation_id=interpretation_id,
            )
            self.logger.debug(f"Created event with ID: {event.id}")

            session.add(event)
            session.flush()
            return event

        event = self._execute_db_operation("add event", _add_event)
        self.logger.info(
            f"Added event: ID={event.id}, scene_id={event.scene_id}, "
            f"source={event.source_name}"
        )
        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            The event if found, None otherwise
        """
        self.logger.debug(f"Getting event by ID: {event_id}")

        def _get_event(session: Session) -> Optional[Event]:
            event = session.query(Event).filter(Event.id == event_id).first()
            if event:
                self.logger.debug(f"Found event: {event.id}")
            else:
                self.logger.debug(f"Event not found with ID: {event_id}")
            return event

        return self._execute_db_operation("get event", _get_event)

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
            EventError: If the event is not found or source is invalid
        """
        self.logger.debug(
            f"Updating event: id={event_id}, description='{description[:30]}...', "
            f"source={source or 'unchanged'}"
        )

        def _update_event(session: Session) -> Event:
            # Get the event
            event = self.get_entity_or_error(
                session,
                Event,
                event_id,
                EventError,
                f"Event with ID '{event_id}' not found",
            )
            self.logger.debug(f"Found event: {event.id} (scene: {event.scene_id})")

            # Store original values for logging
            original_description = event.description
            original_source_id = event.source_id

            # Update description
            event.description = description
            self.logger.debug(
                f"Updated description from '{original_description[:30]}...'"
                f"to '{description[:30]}...'"
            )

            # Update source if provided
            if source is not None:
                event_source = self._get_source_by_name(session, source)
                event.source = event_source
                self.logger.debug(
                    f"Updated source from ID {original_source_id} to "
                    f"{event_source.id} ({event_source.name})"
                )

            return event

        event = self._execute_db_operation("update event", _update_event)
        self.logger.info(
            f"Updated event: ID={event.id}, scene_id={event.scene_id}, "
            f"source={event.source_name}"
        )
        return event

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
        self.logger.debug(
            f"Listing events: scene_id={scene_id or 'active'}, limit={limit or 'None'}"
        )

        # Use active scene if none provided
        if scene_id is None:
            scene_id = self.get_active_scene_id()
            self.logger.debug(f"Using active scene ID: {scene_id}")

        # Validate scene exists
        def _validate_scene(session: Session) -> Scene:
            scene = self.get_entity_or_error(
                session, Scene, scene_id, EventError, f"Scene {scene_id} not found"
            )
            self.logger.debug(f"Found scene: {scene.title} (ID: {scene.id})")
            return scene

        scene = self._execute_db_operation("validate scene", _validate_scene)

        # If we have a scene with events, we could potentially use the model directly
        # But for consistency and to handle the limit parameter, we'll use list_entities

        # List events
        events = self.list_entities(
            Event,
            filters={"scene_id": scene_id},
            order_by="created_at",
            order_direction="desc",
            limit=limit,
        )

        self.logger.debug(f"Found {len(events)} events")
        return events

    def get_event_sources(self) -> List[EventSource]:
        """Get all available event sources.

        Returns:
            List of EventSource objects

        Raises:
            EventError: If there was an error retrieving the sources
        """
        self.logger.debug("Getting all event sources")
        sources = self.list_entities(EventSource, order_by="name")
        self.logger.debug(f"Found {len(sources)} event sources")
        return sources
