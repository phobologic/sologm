"""Tests for event management functionality."""

import logging
from typing import Callable  # Added for type hinting

import pytest
from sqlalchemy.orm import Session  # Added for type hinting

# Import factory and models needed for test setup
from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext
from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.scene import Scene
from sologm.utils.errors import EventError

logger = logging.getLogger(__name__)


# Helper function to create base test data within a session context
def create_base_test_data(
    session: Session,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    game_active: bool = True,
    act_active: bool = True,
    scene_active: bool = True,
) -> tuple[Game, Act, Scene]:
    """Creates a standard game, act, and scene for testing."""
    # Pass session to factory fixtures
    game = create_test_game(session=session, is_active=game_active)
    act = create_test_act(session=session, game_id=game.id, is_active=act_active)
    scene = create_test_scene(session=session, act_id=act.id, is_active=scene_active)
    return game, act, scene


class TestEventManager:
    """Tests for the EventManager class using the new session/manager pattern."""

    def test_add_event(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test adding an event."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            event = managers.event.add_event(
                description="Test event",
                scene_id=scene.id,  # Pass the ID of the scene just created
                source="manual",
            )

            assert event.scene_id == scene.id
            assert event.description == "Test event"
            assert event.source.name == "manual"

            # Verify event was saved to database using the test's session
            db_event = session.get(Event, event.id)
            assert db_event is not None
            assert db_event.description == "Test event"

    def test_add_event_with_active_scene(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ):
        """Test adding an event using the active scene."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Ensure scene is active (default in helper)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            event = managers.event.add_event(description="Test event with active scene")

            assert event.scene_id == scene.id
            assert event.description == "Test event with active scene"

    def test_add_event_nonexistent_scene(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test adding an event to a nonexistent scene."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            with pytest.raises(EventError) as exc:
                managers.event.add_event(
                    description="Test event",
                    scene_id="nonexistent-scene",
                )
            assert "Scene nonexistent-scene not found" in str(exc.value)

    def test_list_events_empty(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ):
        """Test listing events when none exist."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            events = managers.event.list_events(scene_id=scene.id)
            assert len(events) == 0

    def test_list_events_with_active_scene(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test listing events using the active scene."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Ensure scene is active (default in helper)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Add some events using the factory
            create_test_event(
                session=session, scene_id=scene.id, description="First event"
            )
            create_test_event(
                session=session, scene_id=scene.id, description="Second event"
            )

            events = managers.event.list_events()  # Uses active scene by default
            assert len(events) == 2
            # Events should be in reverse chronological order (newest first)
            assert events[0].description == "Second event"
            assert events[1].description == "First event"

    def test_list_events(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test listing multiple events."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Add some events
            create_test_event(
                session=session, scene_id=scene.id, description="First event"
            )
            create_test_event(
                session=session, scene_id=scene.id, description="Second event"
            )

            events = managers.event.list_events(scene_id=scene.id)
            assert len(events) == 2
            # Events should be in reverse chronological order (newest first)
            assert events[0].description == "Second event"
            assert events[1].description == "First event"

    def test_list_events_with_limit(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test listing events with a limit."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Add some events
            create_test_event(
                session=session, scene_id=scene.id, description="First event"
            )
            create_test_event(
                session=session, scene_id=scene.id, description="Second event"
            )
            create_test_event(
                session=session, scene_id=scene.id, description="Third event"
            )

            events = managers.event.list_events(scene_id=scene.id, limit=2)
            assert len(events) == 2
            assert events[0].description == "Third event"
            assert events[1].description == "Second event"

    def test_list_events_nonexistent_scene(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test listing events for a nonexistent scene."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            with pytest.raises(EventError) as exc:
                managers.event.list_events(scene_id="nonexistent-scene")
            assert "Scene nonexistent-scene not found" in str(exc.value)

    def test_get_active_scene_id(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ):
        """Test getting active scene ID."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Ensure scene is active (default in helper)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            scene_id = managers.event.get_active_scene_id()
            assert scene_id == scene.id

    def test_get_active_scene_id_no_game(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test getting active scene ID with no active game."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Deactivate all games using the test's session
            session.query(Game).update({Game.is_active: False})
            # No commit needed, context manager handles it

            with pytest.raises(EventError) as exc:
                managers.event.get_active_scene_id()
            # The error might bubble up from GameManager now
            assert "No active game found" in str(exc.value)

    # Assuming create_test_interpretation_set and create_test_interpretation exist
    # and were refactored in Phase 4 to accept session.
    # If not, these fixtures need to be updated in conftest.py first.
    # @pytest.mark.skip(
    #     reason="Requires create_test_interpretation* fixtures refactored in Phase 4"
    # )
    def test_add_event_from_interpretation(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ):
        """Test adding an event from an interpretation."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Create interpretation data using factories
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id, context="Test context"
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Test Interp"
            )

            event = managers.event.add_event(
                scene_id=scene.id,
                description="Event from interpretation",
                source="oracle",
                interpretation_id=interpretation.id,
            )

            assert event.interpretation_id == interpretation.id

            # Verify relationship works using the test's session
            session.refresh(event)
            assert event.interpretation is not None
            assert event.interpretation.id == interpretation.id

    def test_get_event(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test getting an event by ID."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Create a test event using factory
            logger.debug(f"Creating test event with scene_id={scene.id}")
            event = create_test_event(
                session=session, scene_id=scene.id, description="Test event to retrieve"
            )
            logger.debug(
                f"Created event with id={event.id}, description={event.description}"
            )

            # Get the event using the manager
            retrieved_event = managers.event.get_event(event.id)
            logger.debug(f"Retrieved event: {retrieved_event}")
            if retrieved_event:
                logger.debug(
                    f"Retrieved event id={retrieved_event.id}, "
                    f"description={retrieved_event.description}"
                )

            # Verify the event was retrieved correctly
            assert retrieved_event is not None
            assert retrieved_event.id == event.id
            assert retrieved_event.description == "Test event to retrieve"

    def test_get_nonexistent_event(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test getting a nonexistent event."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Try to get a nonexistent event
            event = managers.event.get_event("nonexistent-event-id")

            # Verify no event was found
            assert event is None

    def test_update_event(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test updating an event's description."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Create a test event
            logger.debug(f"Creating test event with scene_id={scene.id}")
            event = create_test_event(
                session=session, scene_id=scene.id, description="Original description"
            )
            logger.debug(
                f"Created event with id={event.id}, description={event.description}"
            )
            logger.debug(f"Event source: {event.source_id}")
            if hasattr(event, "source") and event.source:
                logger.debug(f"Event source name: {event.source.name}")

            # Update the event
            updated_event = managers.event.update_event(event.id, "Updated description")
            logger.debug(f"Updated event: {updated_event}")
            logger.debug(f"Updated event description: {updated_event.description}")
            logger.debug(f"Updated event source_id: {updated_event.source_id}")
            if hasattr(updated_event, "source") and updated_event.source:
                logger.debug(f"Updated event source name: {updated_event.source.name}")

            # Verify the event was updated correctly
            assert updated_event.id == event.id
            assert updated_event.description == "Updated description"
            assert (
                updated_event.source.name == "manual"
            )  # Source should remain unchanged

            # Verify the event was updated in the database
            retrieved_event = managers.event.get_event(event.id)
            assert retrieved_event.description == "Updated description"

    def test_update_event_with_source(
        self,
        session_context: SessionContext,  # Updated type hint
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test updating an event's description and source."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Create a test event
            logger.debug(f"Creating test event with scene_id={scene.id}")
            event = create_test_event(
                session=session, scene_id=scene.id, description="Original description"
            )
            logger.debug(
                f"Created event with id={event.id}, description={event.description}"
            )
            logger.debug(f"Event source_id: {event.source_id}")
            if hasattr(event, "source") and event.source:
                logger.debug(f"Event source name: {event.source.name}")

            # Check source name
            assert event.source.name == "manual"  # Default source

            # Update the event with a new source
            updated_event = managers.event.update_event(
                event.id, "Updated description", "oracle"
            )
            logger.debug(f"Updated event: {updated_event}")
            logger.debug(f"Updated event description: {updated_event.description}")
            logger.debug(f"Updated event source_id: {updated_event.source_id}")
            if hasattr(updated_event, "source") and updated_event.source:
                logger.debug(f"Updated event source name: {updated_event.source.name}")

            # Verify the event was updated correctly
            assert updated_event.id == event.id
            assert updated_event.description == "Updated description"
            assert updated_event.source.name == "oracle"  # Source should be updated

            # Verify the event was updated in the database
            retrieved_event = managers.event.get_event(event.id)
            assert retrieved_event.description == "Updated description"
            assert retrieved_event.source.name == "oracle"

    def test_update_nonexistent_event(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test updating a nonexistent event."""
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Try to update a nonexistent event
            with pytest.raises(EventError) as exc:
                managers.event.update_event(
                    "nonexistent-event-id", "Updated description"
                )

            # Verify the correct error was raised
            assert "Event with ID 'nonexistent-event-id' not found" in str(exc.value)

    def test_get_event_sources(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):  # Updated type hint
        """Test getting all event sources."""
        # Sources are initialized by the initialize_event_sources fixture in conftest
        with session_context as session:  # Use fixture directly
            initialize_event_sources(session)
            managers = create_all_managers(session)
            # Get all event sources
            sources = managers.event.get_event_sources()

            # Verify we have the expected default sources
            assert len(sources) >= 3  # Allow for potentially more sources later
            source_names = [s.name for s in sources]
            assert "manual" in source_names
            assert "oracle" in source_names
            assert "dice" in source_names
