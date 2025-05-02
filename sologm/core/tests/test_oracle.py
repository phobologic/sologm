"""Tests for oracle interpretation system."""

import logging
from typing import Callable  # Added for type hinting
from unittest.mock import MagicMock  # Added for mock_anthropic_client

import pytest
from sqlalchemy.orm import Session  # Added for type hinting

# Import factory and models needed for test setup
from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext

# Create a dedicated logger for the test module
logger = logging.getLogger(__name__)

# Import models needed for test setup and assertions
from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene
from sologm.utils.errors import OracleError


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
    game = create_test_game(session, is_active=game_active)
    act = create_test_act(session, game_id=game.id, is_active=act_active)
    scene = create_test_scene(session, act_id=act.id, is_active=scene_active)
    return game, act, scene


class TestOracle:
    """Tests for oracle interpretation system."""

    def test_get_active_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting active game, act, and scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Ensure the test objects are active (default in helper)
            game, act, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Get the active context
            retrieved_scene, retrieved_act, retrieved_game = (
                managers.oracle.get_active_context()
            )

            # Verify we got the expected objects
            assert retrieved_scene.id == scene.id
            assert retrieved_act.id == act.id
            assert retrieved_game.id == game.id

    def test_get_active_context_no_game(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test validation with no active game."""
        with session_context as session:
            managers = create_all_managers(session)
            # Make sure no game is active
            session.query(Game).update({Game.is_active: False})

            with pytest.raises(OracleError) as exc:
                managers.oracle.get_active_context()
            assert "No active game found" in str(exc.value)

    def test_get_active_context_no_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
    ) -> None:
        """Test validation with no active act."""
        with session_context as session:
            managers = create_all_managers(session)
            # Make sure the game is active but no act is active
            game = create_test_game(session, is_active=True)
            session.query(Act).filter(Act.game_id == game.id).update(
                {Act.is_active: False}
            )

            with pytest.raises(OracleError) as exc:
                managers.oracle.get_active_context()
            assert "No active act found" in str(exc.value)

    def test_get_active_context_no_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test validation with no active scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Make sure the game and act are active but no scene is active
            game = create_test_game(session, is_active=True)
            act = create_test_act(session, game_id=game.id, is_active=True)
            session.query(Scene).filter(Scene.act_id == act.id).update(
                {Scene.is_active: False}
            )

            with pytest.raises(OracleError) as exc:
                managers.oracle.get_active_context()
            assert "No active scene found" in str(exc.value)

    def test_build_prompt(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        monkeypatch,
    ) -> None:
        """Test building prompts for Claude."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Mock the OraclePrompts.build_interpretation_prompt method
            from sologm.core.prompts.oracle import OraclePrompts

            def mock_build_prompt(*args, **kwargs):
                # Check that the first argument is the scene object
                assert isinstance(args[0], Scene)
                assert args[0].id == scene.id
                return "Mocked prompt"

            monkeypatch.setattr(
                OraclePrompts, "build_interpretation_prompt", mock_build_prompt
            )

            prompt = managers.oracle._build_prompt(
                scene,  # Pass the actual scene object
                "What happens next?",
                "Mystery, Danger",
                3,
            )

            assert prompt == "Mocked prompt"

    def test_parse_interpretations(self, session_context: SessionContext) -> None:
        """Test parsing Claude's response."""
        with session_context as session:
            managers = create_all_managers(session)
            response = """## Test Title 1
Test Description 1

## Test Title 2
Test Description 2"""

            parsed = managers.oracle._parse_interpretations(response)

            assert len(parsed) == 2
            assert parsed[0]["title"] == "Test Title 1"
            assert parsed[0]["description"] == "Test Description 1"
            assert parsed[1]["title"] == "Test Title 2"
            assert parsed[1]["description"] == "Test Description 2"

    def test_get_interpretations(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ) -> None:
        """Test getting interpretations."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Configure mock to return string response
            response_text = """## Test Title
Test Description"""
            mock_anthropic_client.send_message.return_value = response_text

            result = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            assert isinstance(result, InterpretationSet)
            assert result.scene_id == scene.id
            assert result.context == "What happens?"
            assert result.oracle_results == "Mystery"
            assert len(result.interpretations) == 1
            assert result.interpretations[0].title == "Test Title"
            assert result.interpretations[0].description == "Test Description"
            assert result.is_current is True

    def test_get_interpretations_error(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ) -> None:
        """Test handling errors when getting interpretations."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client
            mock_anthropic_client.send_message.side_effect = Exception("API Error")

            with pytest.raises(OracleError) as exc:
                managers.oracle.get_interpretations(
                    scene.id,
                    "What happens?",
                    "Mystery",
                    1,
                )
            assert "Failed to get interpretations" in str(exc.value)

    def test_select_interpretation(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
        initialize_event_sources: Callable[[Session], None],  # Add this fixture
    ) -> None:
        """Test selecting an interpretation."""
        with session_context as session:
            # Initialize event sources first
            initialize_event_sources(session)  # Call the initializer here

            managers = create_all_managers(session)
            game, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Configure mock to return string response
            response_text = """## Test Title
Test Description"""
            mock_anthropic_client.send_message.return_value = response_text

            # First create an interpretation set
            interp_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            # Test selecting by UUID
            selected = managers.oracle.select_interpretation(
                interp_set.id, interp_set.interpretations[0].id
            )

            assert isinstance(selected, Interpretation)
            assert selected.id == interp_set.interpretations[0].id
            assert selected.title == interp_set.interpretations[0].title
            assert selected.is_selected is True

            # Verify no event was created automatically
            # Get the oracle source
            oracle_source = (
                session.query(EventSource).filter(EventSource.name == "oracle").first()
            )
            # Add an assertion to ensure the source was found after initialization
            assert oracle_source is not None, (
                "Oracle event source not found after initialization"
            )

            events = (
                session.query(Event)
                .filter(
                    Event.scene_id == scene.id,
                    Event.source_id == oracle_source.id,
                    Event.interpretation_id == selected.id,
                )
                .all()
            )

            assert len(events) == 0

            # Now explicitly add an event
            event = managers.oracle.add_interpretation_event(selected)

            # Verify event was created
            events = (
                session.query(Event)
                .filter(
                    Event.scene_id == scene.id,
                    Event.source_id == oracle_source.id,
                    Event.interpretation_id == selected.id,
                )
                .all()
            )

            assert len(events) == 1
            assert selected.title in events[0].description

    def test_select_interpretation_not_found(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
    ) -> None:
        """Test selecting a non-existent interpretation from an existing empty set."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )
            # Create an empty interpretation set
            empty_set = create_test_interpretation_set(session, scene_id=scene.id)

            with pytest.raises(OracleError) as exc:
                managers.oracle.select_interpretation(
                    empty_set.id, "nonexistent-interp"
                )
            assert "No interpretations found" in str(exc.value)

    def test_find_interpretation_by_different_identifiers(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ) -> None:
        """Test finding interpretations by different identifier types."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Configure mock to return string response with multiple interpretations
            response_text = """## First Option
Description of first option

## Second Option
Description of second option"""
            mock_anthropic_client.send_message.return_value = response_text

            # Create an interpretation set with multiple interpretations
            interp_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                2,
            )

            assert len(interp_set.interpretations) == 2

            # Test finding by sequence number (as string)
            interp1 = managers.oracle.find_interpretation(interp_set.id, "1")
            assert interp1.title == "First Option"

            interp2 = managers.oracle.find_interpretation(interp_set.id, "2")
            assert interp2.title == "Second Option"

            # Test finding by slug
            interp_by_slug = managers.oracle.find_interpretation(
                interp_set.id, "first-option"
            )
            assert interp_by_slug.id == interp1.id

            # Test finding by UUID
            interp_by_id = managers.oracle.find_interpretation(
                interp_set.id, interp1.id
            )
            assert interp_by_id.id == interp1.id

            # Test invalid identifier
            with pytest.raises(OracleError) as exc:
                managers.oracle.find_interpretation(interp_set.id, "99")
            assert "not found" in str(exc.value)

    def test_get_interpretations_with_retry(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ) -> None:
        """Test getting interpretations with retry attempt."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Configure mock to return string response
            response_text = """## Test Title
Test Description"""
            mock_anthropic_client.send_message.return_value = response_text

            # First interpretation request
            result1 = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )
            assert result1.retry_attempt == 0
            assert result1.is_current is True

            # Retry interpretation
            result2 = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
                retry_attempt=1,
            )
            assert result2.retry_attempt == 1
            assert result2.is_current is True

            # Verify first set is no longer current
            session.refresh(result1)
            assert result1.is_current is False

            # Verify different prompt was used for retry
            retry_call = mock_anthropic_client.send_message.call_args_list[1]
            assert "retry attempt #2" in retry_call[0][0].lower()
            assert "different" in retry_call[0][0].lower()

    def test_automatic_retry_on_parse_failure(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test automatic retry when parsing fails."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # First response has no interpretations (bad format)
            # Second response has valid interpretations
            mock_anthropic_client.send_message.side_effect = [
                "No proper format here",  # First call - bad format
                """## Retry Title
Retry Description""",  # Second call - good format
            ]

            # This should automatically retry once
            result = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            # Verify we got the result from the second attempt
            assert mock_anthropic_client.send_message.call_count == 2
            assert result.retry_attempt == 1  # Should be marked as retry attempt 1
            assert len(result.interpretations) == 1
            assert result.interpretations[0].title == "Retry Title"

    def test_automatic_retry_max_attempts(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test that we don't exceed max retry attempts."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # All responses have bad format
            mock_anthropic_client.send_message.side_effect = [
                "Bad format 1",  # First call
                "Bad format 2",  # Second call
                "Bad format 3",  # Third call (shouldn't be reached with default max_retries=2)
            ]

            # This should try the original + 2 retries, then fail
            with pytest.raises(OracleError) as exc:
                managers.oracle.get_interpretations(
                    scene.id,
                    "What happens?",
                    "Mystery",
                    1,
                )

            # Verify we tried 3 times total (original + 2 retries)
            assert mock_anthropic_client.send_message.call_count == 3
            assert "after 3 attempts" in str(exc.value)

    def test_automatic_retry_with_custom_max(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test custom max_retries parameter."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # First two responses have bad format, third is good
            mock_anthropic_client.send_message.side_effect = [
                "Bad format 1",  # First call
                "Bad format 2",  # Second call
                """## Custom Max Retry
Custom Description""",  # Third call
            ]

            # Set max_retries to 1 (so we should only try twice total)
            with pytest.raises(OracleError) as exc:
                managers.oracle.get_interpretations(
                    scene.id,
                    "What happens?",
                    "Mystery",
                    1,
                    max_retries=1,
                )

            # Verify we only tried twice (original + 1 retry)
            assert mock_anthropic_client.send_message.call_count == 2
            assert "after 2 attempts" in str(exc.value)

    def test_oracle_manager_get_interpretations_detailed(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test detailed interpretation generation and parsing."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Configure mock with a more complex response
            response_text = """## First Interpretation
This is the first interpretation with multiple lines
and some formatting.

## Second Interpretation
This is the second interpretation.
It also has multiple lines."""
            mock_anthropic_client.send_message.return_value = response_text

            result = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery, Danger",
                2,
            )

            assert len(result.interpretations) == 2
            assert result.interpretations[0].title == "First Interpretation"
            assert "multiple lines" in result.interpretations[0].description
            assert result.interpretations[1].title == "Second Interpretation"

    # This test is removed as _get_context_data method no longer exists

    # This test is removed as _create_interpretation_set method no longer exists

    def test_get_most_recent_interpretation(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test getting most recent interpretation."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Create an interpretation set
            response_text = """## Test Title\nTest Description"""
            mock_anthropic_client.send_message.return_value = response_text

            interp_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            # Select an interpretation
            selected = managers.oracle.select_interpretation(interp_set.id, "1")

            # Get most recent interpretation
            result = managers.oracle.get_most_recent_interpretation(scene.id)

            assert result is not None
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result[0].id == interp_set.id
            assert result[1].id == selected.id

            # Test with no selected interpretations
            # First clear all selections
            session.query(Interpretation).update({Interpretation.is_selected: False})

            result = managers.oracle.get_most_recent_interpretation(scene.id)
            assert result is None

    def test_add_interpretation_event(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
        initialize_event_sources: Callable[[Session], None],  # Add fixture
    ):
        """Test adding interpretation as event directly."""
        with session_context as session:
            # Initialize event sources first
            initialize_event_sources(session)  # Call initializer

            managers = create_all_managers(session)
            game, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Create an interpretation set
            response_text = """## Test Title\nTest Description"""
            mock_anthropic_client.send_message.return_value = response_text

            interp_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            interpretation = interp_set.interpretations[0]

            # Add as event directly
            managers.oracle.add_interpretation_event(interpretation)

            # Get the oracle source
            oracle_source = (
                session.query(EventSource).filter(EventSource.name == "oracle").first()
            )
            # Add assertion to ensure oracle_source is found after initialization
            assert oracle_source is not None, (
                "Oracle event source not found after initialization"
            )

            # Verify event was created
            events = (
                session.query(Event)
                .filter(
                    Event.scene_id == scene.id,
                    Event.source_id == oracle_source.id,
                    Event.interpretation_id == interpretation.id,
                )
                .all()
            )

            assert len(events) == 1
            assert interpretation.title in events[0].description
            assert events[0].source.name == "oracle"

    def test_parse_interpretations_malformed(self, session_context: SessionContext):
        """Test parsing malformed responses."""
        with session_context as session:
            managers = create_all_managers(session)
            # Test with completely invalid format
            response = "This is not formatted correctly at all."
            parsed = managers.oracle._parse_interpretations(response)
            assert len(parsed) == 0

            # Test with partial formatting
            response = "Some text\n## Title Only\nNo other titles"
            parsed = managers.oracle._parse_interpretations(response)
            assert len(parsed) == 1
            assert parsed[0]["title"] == "Title Only"

            # Test with code blocks (which should be removed)
            response = "```markdown\n## Code Block Title\nDescription\n```"
            parsed = managers.oracle._parse_interpretations(response)
            assert len(parsed) == 1
            assert parsed[0]["title"] == "Code Block Title"

    def test_multiple_interpretation_sets(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test managing multiple interpretation sets."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Create multiple interpretation sets
            mock_anthropic_client.send_message.side_effect = [
                "## First Set\nDescription 1",
                "## Second Set\nDescription 2",
                "## Third Set\nDescription 3",
            ]

            # Create three sets
            set1 = managers.oracle.get_interpretations(
                scene.id, "Question 1", "Result 1", 1
            )
            set2 = managers.oracle.get_interpretations(
                scene.id, "Question 2", "Result 2", 1
            )
            set3 = managers.oracle.get_interpretations(
                scene.id, "Question 3", "Result 3", 1
            )

            # Verify only the last one is current
            session.refresh(set1)
            session.refresh(set2)
            session.refresh(set3)

            assert set1.is_current is False
            assert set2.is_current is False
            assert set3.is_current is True

            # Verify get_current_interpretation_set returns the last one
            current = managers.oracle.get_current_interpretation_set(scene.id)
            assert current.id == set3.id

    def test_get_current_interpretation_set(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        mock_anthropic_client: MagicMock,
    ):
        """Test getting current interpretation set."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Manually set the mock client on the manager instance
            managers.oracle.anthropic_client = mock_anthropic_client

            # Create an interpretation set
            response_text = """## Test Title\nTest Description"""
            mock_anthropic_client.send_message.return_value = response_text

            created_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens?",
                "Mystery",
                1,
            )

            # Get current set and verify it matches
            current_set = managers.oracle.get_current_interpretation_set(scene.id)

            assert current_set is not None
            assert current_set.id == created_set.id
            assert current_set.is_current is True

            # Create another set and verify the first is no longer current
            new_set = managers.oracle.get_interpretations(
                scene.id,
                "What happens next?",
                "Danger",
                1,
            )

            current_set = managers.oracle.get_current_interpretation_set(scene.id)
            assert current_set.id == new_set.id

            # Verify old set is no longer current
            session.refresh(created_set)
            assert created_set.is_current is False

    def test_get_current_interpretation_set_none(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test getting current interpretation set when none exists."""
        with session_context as session:
            managers = create_all_managers(session)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Ensure no current interpretation sets exist
            session.query(InterpretationSet).filter(
                InterpretationSet.scene_id == scene.id
            ).update({InterpretationSet.is_current: False})

            # Verify get_current_interpretation_set returns None
            current_set = managers.oracle.get_current_interpretation_set(scene.id)
            assert current_set is None

    def test_build_interpretation_prompt_for_active_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        monkeypatch,
    ):
        """Test building interpretation prompt for active context with acts."""
        with session_context as session:
            managers = create_all_managers(session)
            # Ensure the test objects are active (default in helper)
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Mock the _build_prompt method to avoid actual prompt generation
            original_build_prompt = managers.oracle._build_prompt

            def mock_build_prompt(*args, **kwargs):
                # Just return the arguments to verify they're correct
                return {
                    "scene": args[0],
                    "context": args[1],
                    "oracle_results": args[2],
                    "count": args[3],
                }

            monkeypatch.setattr(managers.oracle, "_build_prompt", mock_build_prompt)

            # Call the method
            result = managers.oracle.build_interpretation_prompt_for_active_context(
                "Test context",
                "Test results",
                3,
            )

            # Verify the correct data was passed to _build_prompt
            assert result["scene"].id == scene.id
            assert result["context"] == "Test context"
            assert result["oracle_results"] == "Test results"
            assert result["count"] == 3
