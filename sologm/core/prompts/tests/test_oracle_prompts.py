"""Tests for oracle prompt templates."""

from typing import Callable  # Import Callable for type hinting factory fixtures

from sologm.core.prompts.oracle import OraclePrompts  # Import the class being tested

# Import necessary model types for type hinting if needed
from sologm.database.session import Session, SessionContext  # Import Session type hint
from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.scene import Scene


class TestOraclePrompts:
    """Tests for oracle prompt templates."""

    def test_format_events_with_events(self):
        """Test formatting events when events exist."""
        events = ["Event 1", "Event 2", "Event 3"]
        result = OraclePrompts._format_events(events)
        assert result == "- Event 1\n- Event 2\n- Event 3"

    def test_format_events_without_events(self):
        """Test formatting events when no events exist."""
        result = OraclePrompts._format_events([])
        assert result == "No recent events"

    def test_get_example_format(self):
        """Test getting example format."""
        result = OraclePrompts._get_example_format()
        assert "## The Mysterious Footprints" in result
        assert "## An Inside Job" in result

    def test_format_previous_interpretations_with_interpretations(self):
        """Test formatting previous interpretations when they exist."""
        interpretations = [
            {"title": "Title 1", "description": "Description 1"},
            {"title": "Title 2", "description": "Description 2"},
        ]
        result = OraclePrompts._format_previous_interpretations(interpretations, 1)
        assert "=== PREVIOUS INTERPRETATIONS (DO NOT REPEAT THESE) ===" in result
        assert "## Title 1" in result
        assert "Description 1" in result
        assert "## Title 2" in result
        assert "Description 2" in result
        assert "=== END OF PREVIOUS INTERPRETATIONS ===" in result

    def test_format_previous_interpretations_without_interpretations(self):
        """Test formatting previous interpretations when none exist."""
        result = OraclePrompts._format_previous_interpretations(None, 1)
        assert result == ""

    def test_format_previous_interpretations_first_attempt(self):
        """Test formatting previous interpretations on first attempt."""
        interpretations = [
            {"title": "Title 1", "description": "Description 1"},
        ]
        result = OraclePrompts._format_previous_interpretations(interpretations, 0)
        assert result == ""

    def test_get_retry_text_with_retry(self):
        """Test getting retry text when retrying."""
        result = OraclePrompts._get_retry_text(1)
        assert "retry attempt #2" in result
        assert "COMPLETELY DIFFERENT" in result

    def test_get_retry_text_first_attempt(self):
        """Test getting retry text on first attempt."""
        result = OraclePrompts._get_retry_text(0)
        assert result == ""

    # Corrected test signature and implementation - NO fixture imports needed
    def test_build_interpretation_prompt(
        self,
        session_context: SessionContext,  # Request the fixture directly
        create_test_game: Callable[..., Game],  # Request the fixture directly
        create_test_act: Callable[..., Act],  # Request the fixture directly
        create_test_scene: Callable[..., Scene],  # Request the fixture directly
        create_test_event: Callable[..., Event],  # Request the fixture directly
        initialize_event_sources: Callable[
            [Session], None
        ],  # Request the initializer fixture
    ):
        """Test building the complete interpretation prompt."""
        with session_context as session:
            # Initialize default event sources needed by create_test_event
            initialize_event_sources(session)

            # Create necessary data within the session context
            game = create_test_game(
                session, name="Test Game", description="Test Game Description"
            )
            act = create_test_act(
                session, game_id=game.id, title="Test Act", summary="Test Act Summary"
            )
            scene = create_test_scene(
                session,
                act_id=act.id,
                title="Test Scene",
                description="Test Scene Description",
            )
            event1 = create_test_event(
                session, scene_id=scene.id, description="Event 1 Description"
            )

            # Refresh relationships if needed for nested access in the prompt generation
            session.refresh(scene, attribute_names=["act", "events"])
            session.refresh(act, attribute_names=["game"])

            # Call the method under test with the created data
            result = OraclePrompts.build_interpretation_prompt(
                scene,  # Use the created scene object
                "What happens next?",
                "Mystery, Danger",
                3,
            )

            # Check that all components are included using the created data
            assert "You are interpreting oracle results for a solo RPG player" in result
            assert f"Game: {game.description}" in result
            assert f"Act: {act.summary}" in result
            assert f"Current Scene: {scene.description}" in result
            # Ensure the event description is correctly formatted in the prompt's event list
            assert f"- {event1.description}" in result  # Check formatting if applicable
            assert "Player's Question/Context: What happens next?" in result
            assert "Oracle Results: Mystery, Danger" in result
            assert "Please provide 3 different interpretations" in result

    # Corrected test signature - NO fixture imports needed
    def test_build_interpretation_prompt_with_retry(
        self,
        session_context: SessionContext,  # Request the fixture directly
        create_test_game: Callable[..., Game],  # Request the fixture directly
        create_test_act: Callable[..., Act],  # Request the fixture directly
        create_test_scene: Callable[..., Scene],  # Request the fixture directly
        # Add initializer if events are created or might be needed by prompt logic
        initialize_event_sources: Callable[[Session], None],
    ):
        """Test building the prompt with retry information."""
        previous_interpretations = [
            {"title": "Previous Title", "description": "Previous Description"},
        ]
        with session_context as session:
            # Initialize default event sources if needed
            initialize_event_sources(session)

            # Create necessary data
            game = create_test_game(session)
            act = create_test_act(session, game_id=game.id)
            scene = create_test_scene(session, act_id=act.id)
            # Refresh if needed for nested access
            session.refresh(
                scene, attribute_names=["act", "events"]
            )  # Add 'events' if created
            session.refresh(act, attribute_names=["game"])

            # Call the method under test
            result = OraclePrompts.build_interpretation_prompt(
                scene,  # Use the created scene
                "What happens next?",
                "Mystery, Danger",
                3,
                previous_interpretations=previous_interpretations,
                retry_attempt=1,
            )

            # Assertions
            assert "=== PREVIOUS INTERPRETATIONS (DO NOT REPEAT THESE) ===" in result
            assert "## Previous Title" in result
            assert "Previous Description" in result
            assert "retry attempt #2" in result
            assert "COMPLETELY DIFFERENT" in result
            # Add assertion for event if created:
            # assert "- Retry Test Event" in result
