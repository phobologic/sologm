"""Tests for event management functionality."""

import pytest

from sologm.models.event import Event
from sologm.models.game import Game
from sologm.utils.errors import EventError


class TestEventManager:
    """Tests for the EventManager class."""

    def test_add_event(self, event_manager, test_game, test_scene, db_session):
        """Test adding an event."""
        event = event_manager.add_event(
            game_id=test_game.id,
            scene_id=test_scene.id,
            description="Test event",
            source="manual",
        )

        assert event.scene_id == test_scene.id
        assert event.game_id == test_game.id
        assert event.description == "Test event"
        assert event.source == "manual"

        # Verify event was saved to database
        db_event = db_session.query(Event).filter(Event.id == event.id).first()
        assert db_event is not None
        assert db_event.description == "Test event"

    def test_add_event_nonexistent_scene(self, event_manager, test_game):
        """Test adding an event to a nonexistent scene."""
        with pytest.raises(EventError) as exc:
            event_manager.add_event(
                game_id=test_game.id,
                scene_id="nonexistent-scene",
                description="Test event",
            )
        assert "Scene nonexistent-scene not found" in str(exc.value)

    def test_list_events_empty(self, event_manager, test_game, test_scene):
        """Test listing events when none exist."""
        events = event_manager.list_events(game_id=test_game.id, scene_id=test_scene.id)
        assert len(events) == 0

    def test_list_events(self, event_manager, test_game, test_scene, create_test_event):
        """Test listing multiple events."""
        # Add some events
        create_test_event(test_game.id, test_scene.id, "First event")
        create_test_event(test_game.id, test_scene.id, "Second event")

        events = event_manager.list_events(game_id=test_game.id, scene_id=test_scene.id)
        assert len(events) == 2
        # Events should be in reverse chronological order (newest first)
        assert events[0].description == "Second event"
        assert events[1].description == "First event"

    def test_list_events_with_limit(
        self, event_manager, test_game, test_scene, create_test_event
    ):
        """Test listing events with a limit."""
        # Add some events
        create_test_event(test_game.id, test_scene.id, "First event")
        create_test_event(test_game.id, test_scene.id, "Second event")
        create_test_event(test_game.id, test_scene.id, "Third event")

        events = event_manager.list_events(
            game_id=test_game.id, scene_id=test_scene.id, limit=2
        )
        assert len(events) == 2
        assert events[0].description == "Third event"
        assert events[1].description == "Second event"

    def test_list_events_nonexistent_scene(self, event_manager, test_game):
        """Test listing events for a nonexistent scene."""
        with pytest.raises(EventError) as exc:
            event_manager.list_events(
                game_id=test_game.id, scene_id="nonexistent-scene"
            )
        assert "Scene nonexistent-scene not found" in str(exc.value)

    def test_validate_active_context(
        self, event_manager, game_manager, scene_manager, test_game, test_scene
    ):
        """Test validating active game and scene context."""
        game_id, scene_id = event_manager.validate_active_context(
            game_manager, scene_manager
        )
        assert game_id == test_game.id
        assert scene_id == test_scene.id

    def test_validate_active_context_no_game(
        self, event_manager, game_manager, scene_manager, db_session
    ):
        """Test validation with no active game."""
        # Deactivate all games
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        with pytest.raises(EventError) as exc:
            event_manager.validate_active_context(game_manager, scene_manager)
        assert "No active game" in str(exc.value)

    def test_add_event_from_interpretation(
        self,
        event_manager,
        test_game,
        test_scene,
        test_interpretation_set,
        test_interpretations,
        db_session,
    ):
        """Test adding an event from an interpretation."""
        interpretation = test_interpretations[0]

        event = event_manager.add_event(
            game_id=test_game.id,
            scene_id=test_scene.id,
            description="Event from interpretation",
            source="oracle",
            interpretation_id=interpretation.id,
        )

        assert event.interpretation_id == interpretation.id

        # Verify relationship works
        db_session.refresh(event)
        assert event.interpretation is not None
        assert event.interpretation.id == interpretation.id
