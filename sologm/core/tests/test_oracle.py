"""Tests for oracle interpretation system."""

import pytest

from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene
from sologm.utils.errors import OracleError


class TestOracle:
    """Tests for oracle interpretation system."""

    def test_get_active_context(
        self,
        oracle_manager,
        test_game,
        test_act,
        test_scene,
        game_manager,
        scene_manager,
        act_manager,
        monkeypatch,
    ) -> None:
        """Test getting active game, act, and scene."""
        # Monkeypatch the manager properties to use our test managers
        monkeypatch.setattr(oracle_manager, "game_manager", game_manager)
        monkeypatch.setattr(oracle_manager, "act_manager", act_manager)
        monkeypatch.setattr(oracle_manager, "scene_manager", scene_manager)

        game_id, act_id, scene_id = oracle_manager.get_active_context()
        assert game_id == test_game.id
        assert act_id == test_act.id
        assert scene_id == test_scene.id

    def test_get_active_context_no_game(
        self,
        oracle_manager,
        game_manager,
        scene_manager,
        act_manager,
        db_session,
        monkeypatch,
    ) -> None:
        """Test validation with no active game."""
        # Monkeypatch the manager properties to use our test managers
        monkeypatch.setattr(oracle_manager, "game_manager", game_manager)
        monkeypatch.setattr(oracle_manager, "act_manager", act_manager)
        monkeypatch.setattr(oracle_manager, "scene_manager", scene_manager)

        # Make sure no game is active
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_active_context()
        assert "No active game found" in str(exc.value)

    def test_get_active_context_no_act(
        self,
        oracle_manager,
        test_game,
        game_manager,
        scene_manager,
        act_manager,
        db_session,
        monkeypatch,
    ) -> None:
        """Test validation with no active act."""
        # Monkeypatch the manager properties to use our test managers
        monkeypatch.setattr(oracle_manager, "game_manager", game_manager)
        monkeypatch.setattr(oracle_manager, "act_manager", act_manager)
        monkeypatch.setattr(oracle_manager, "scene_manager", scene_manager)

        # Make sure no act is active
        db_session.query(Act).filter(Act.game_id == test_game.id).update(
            {Act.is_active: False}
        )
        db_session.commit()

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_active_context()
        assert "No active act found" in str(exc.value)

    def test_get_active_context_no_scene(
        self,
        oracle_manager,
        test_game,
        test_act,
        game_manager,
        scene_manager,
        act_manager,
        db_session,
        monkeypatch,
    ) -> None:
        """Test validation with no active scene."""
        # Monkeypatch the manager properties to use our test managers
        monkeypatch.setattr(oracle_manager, "game_manager", game_manager)
        monkeypatch.setattr(oracle_manager, "act_manager", act_manager)
        monkeypatch.setattr(oracle_manager, "scene_manager", scene_manager)

        # Make sure no scene is active in the active act
        db_session.query(Scene).filter(Scene.act_id == test_act.id).update(
            {Scene.is_active: False}
        )
        db_session.commit()

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_active_context()
        assert "No active scene found" in str(exc.value)

    def test_build_prompt(self, oracle_manager, monkeypatch) -> None:
        """Test building prompts for Claude."""
        # Mock the OraclePrompts.build_interpretation_prompt method
        from sologm.core.prompts.oracle import OraclePrompts

        def mock_build_prompt(*args, **kwargs):
            return "Mocked prompt"

        monkeypatch.setattr(
            OraclePrompts, "build_interpretation_prompt", mock_build_prompt
        )

        prompt = oracle_manager._build_prompt(
            "Test Game",
            "Test Scene",
            ["Event 1", "Event 2"],
            "What happens next?",
            "Mystery, Danger",
            3,
        )

        assert prompt == "Mocked prompt"

    def test_parse_interpretations(self, oracle_manager) -> None:
        """Test parsing Claude's response."""
        response = """## Test Title 1
Test Description 1

## Test Title 2
Test Description 2"""

        parsed = oracle_manager._parse_interpretations(response)

        assert len(parsed) == 2
        assert parsed[0]["title"] == "Test Title 1"
        assert parsed[0]["description"] == "Test Description 1"
        assert parsed[1]["title"] == "Test Title 2"
        assert parsed[1]["description"] == "Test Description 2"

    def test_get_interpretations(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ) -> None:
        """Test getting interpretations."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        result = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )

        assert isinstance(result, InterpretationSet)
        assert result.scene_id == test_scene.id
        assert result.context == "What happens?"
        assert result.oracle_results == "Mystery"
        assert len(result.interpretations) == 1
        assert result.interpretations[0].title == "Test Title"
        assert result.interpretations[0].description == "Test Description"
        assert result.is_current is True

    def test_get_interpretations_error(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ) -> None:
        """Test handling errors when getting interpretations."""
        mock_anthropic_client.send_message.side_effect = Exception("API Error")

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                test_game.id,
                test_act.id,
                test_scene.id,
                "What happens?",
                "Mystery",
                1,
            )
        assert "Failed to get interpretations" in str(exc.value)

    def test_select_interpretation(
        self,
        oracle_manager,
        mock_anthropic_client,
        test_game,
        test_act,
        test_scene,
        db_session,
    ) -> None:
        """Test selecting an interpretation."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        # First create an interpretation set
        interp_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )

        # Test selecting by UUID
        selected = oracle_manager.select_interpretation(
            interp_set.id, interp_set.interpretations[0].id
        )

        assert isinstance(selected, Interpretation)
        assert selected.id == interp_set.interpretations[0].id
        assert selected.title == interp_set.interpretations[0].title
        assert selected.is_selected is True

        # Verify no event was created automatically
        # Get the oracle source
        oracle_source = (
            db_session.query(EventSource).filter(EventSource.name == "oracle").first()
        )

        events = (
            db_session.query(Event)
            .filter(
                Event.game_id == test_game.id,
                Event.scene_id == test_scene.id,
                Event.source_id == oracle_source.id,
                Event.interpretation_id == selected.id,
            )
            .all()
        )

        assert len(events) == 0

        # Now explicitly add an event
        event = oracle_manager.add_interpretation_event(selected)

        # Get the oracle source
        oracle_source = (
            db_session.query(EventSource).filter(EventSource.name == "oracle").first()
        )

        # Verify event was created
        events = (
            db_session.query(Event)
            .filter(
                Event.game_id == test_game.id,
                Event.scene_id == test_scene.id,
                Event.source_id == oracle_source.id,
                Event.interpretation_id == selected.id,
            )
            .all()
        )

        assert len(events) == 1
        assert selected.title in events[0].description

    def test_select_interpretation_not_found(
        self, oracle_manager, test_game, test_act, test_scene
    ) -> None:
        """Test selecting a non-existent interpretation."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.select_interpretation(
                "nonexistent-set", "nonexistent-interp"
            )
        assert "No interpretations found" in str(exc.value)

    def test_find_interpretation_by_different_identifiers(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ) -> None:
        """Test finding interpretations by different identifier types."""
        # Configure mock to return string response with multiple interpretations
        response_text = """## First Option
Description of first option

## Second Option
Description of second option"""
        mock_anthropic_client.send_message.return_value = response_text

        # Create an interpretation set with multiple interpretations
        interp_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            2,
        )

        assert len(interp_set.interpretations) == 2

        # Test finding by sequence number (as string)
        interp1 = oracle_manager.find_interpretation(interp_set.id, "1")
        assert interp1.title == "First Option"

        interp2 = oracle_manager.find_interpretation(interp_set.id, "2")
        assert interp2.title == "Second Option"

        # Test finding by slug
        interp_by_slug = oracle_manager.find_interpretation(
            interp_set.id, "first-option"
        )
        assert interp_by_slug.id == interp1.id

        # Test finding by UUID
        interp_by_id = oracle_manager.find_interpretation(interp_set.id, interp1.id)
        assert interp_by_id.id == interp1.id

        # Test invalid identifier
        with pytest.raises(OracleError) as exc:
            oracle_manager.find_interpretation(interp_set.id, "99")
        assert "not found" in str(exc.value)

    def test_get_interpretations_with_retry(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ) -> None:
        """Test getting interpretations with retry attempt."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        # First interpretation request
        result1 = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )
        assert result1.retry_attempt == 0
        assert result1.is_current is True

        # Retry interpretation
        result2 = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
            retry_attempt=1,
        )
        assert result2.retry_attempt == 1
        assert result2.is_current is True

        # Verify first set is no longer current
        db_session = oracle_manager._session
        db_session.refresh(result1)
        assert result1.is_current is False

        # Verify different prompt was used for retry
        retry_call = mock_anthropic_client.send_message.call_args_list[1]
        assert "retry attempt #2" in retry_call[0][0].lower()
        assert "different" in retry_call[0][0].lower()

    def test_automatic_retry_on_parse_failure(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test automatic retry when parsing fails."""
        # First response has no interpretations (bad format)
        # Second response has valid interpretations
        mock_anthropic_client.send_message.side_effect = [
            "No proper format here",  # First call - bad format
            """## Retry Title
Retry Description""",  # Second call - good format
        ]

        # This should automatically retry once
        result = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
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
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test that we don't exceed max retry attempts."""
        # All responses have bad format
        mock_anthropic_client.send_message.side_effect = [
            "Bad format 1",  # First call
            "Bad format 2",  # Second call
            "Bad format 3",  # Third call (shouldn't be reached with default max_retries=2)
        ]

        # This should try the original + 2 retries, then fail
        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                test_game.id,
                test_act.id,
                test_scene.id,
                "What happens?",
                "Mystery",
                1,
            )

        # Verify we tried 3 times total (original + 2 retries)
        assert mock_anthropic_client.send_message.call_count == 3
        assert "after 3 attempts" in str(exc.value)

    def test_automatic_retry_with_custom_max(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test custom max_retries parameter."""
        # First two responses have bad format, third is good
        mock_anthropic_client.send_message.side_effect = [
            "Bad format 1",  # First call
            "Bad format 2",  # Second call
            """## Custom Max Retry
Custom Description""",  # Third call
        ]

        # Set max_retries to 1 (so we should only try twice total)
        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                test_game.id,
                test_act.id,
                test_scene.id,
                "What happens?",
                "Mystery",
                1,
                max_retries=1,
            )

        # Verify we only tried twice (original + 1 retry)
        assert mock_anthropic_client.send_message.call_count == 2
        assert "after 2 attempts" in str(exc.value)

    def test_oracle_manager_get_interpretations_detailed(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test detailed interpretation generation and parsing."""
        # Configure mock with a more complex response
        response_text = """## First Interpretation
This is the first interpretation with multiple lines
and some formatting.

## Second Interpretation
This is the second interpretation.
It also has multiple lines."""
        mock_anthropic_client.send_message.return_value = response_text

        result = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery, Danger",
            2,
        )

        assert len(result.interpretations) == 2
        assert result.interpretations[0].title == "First Interpretation"
        assert "multiple lines" in result.interpretations[0].description
        assert result.interpretations[1].title == "Second Interpretation"

    def test_get_context_data(self, oracle_manager, test_game, test_act, test_scene):
        """Test getting context data for interpretations."""
        game, act, scene, events, previous = oracle_manager._get_context_data(
            test_scene.id, 0, None
        )

        assert game.id == test_game.id
        assert act.id == test_act.id
        assert scene.id == test_scene.id
        assert isinstance(events, list)
        assert previous is None

    def test_create_interpretation_set(self, oracle_manager, test_scene):
        """Test creating interpretation set."""
        parsed = [{"title": "Test Title", "description": "Test Description"}]

        result = oracle_manager._create_interpretation_set(
            test_scene.id, "Test context", "Test results", parsed, 0
        )

        assert isinstance(result, InterpretationSet)
        assert result.scene_id == test_scene.id
        assert result.context == "Test context"
        assert result.oracle_results == "Test results"
        assert result.retry_attempt == 0
        assert result.is_current is True
        assert len(result.interpretations) == 1
        assert result.interpretations[0].title == "Test Title"

    def test_get_most_recent_interpretation(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test getting most recent interpretation."""
        # Create an interpretation set
        response_text = """## Test Title\nTest Description"""
        mock_anthropic_client.send_message.return_value = response_text

        interp_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )

        # Select an interpretation
        selected = oracle_manager.select_interpretation(interp_set.id, "1")

        # Get most recent interpretation
        result = oracle_manager.get_most_recent_interpretation(test_scene.id)

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0].id == interp_set.id
        assert result[1].id == selected.id

        # Test with no selected interpretations
        # First clear all selections
        db_session = oracle_manager._session
        db_session.query(Interpretation).update({Interpretation.is_selected: False})
        db_session.commit()

        result = oracle_manager.get_most_recent_interpretation(test_scene.id)
        assert result is None

    def test_add_interpretation_event(
        self,
        oracle_manager,
        mock_anthropic_client,
        test_game,
        test_act,
        test_scene,
        db_session,
    ):
        """Test adding interpretation as event directly."""
        # Create an interpretation set
        response_text = """## Test Title\nTest Description"""
        mock_anthropic_client.send_message.return_value = response_text

        interp_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )

        interpretation = interp_set.interpretations[0]

        # Add as event directly
        oracle_manager.add_interpretation_event(interpretation)

        # Get the oracle source
        oracle_source = (
            db_session.query(EventSource).filter(EventSource.name == "oracle").first()
        )

        # Verify event was created
        events = (
            db_session.query(Event)
            .filter(
                Event.game_id == test_game.id,
                Event.scene_id == test_scene.id,
                Event.source_id == oracle_source.id,
                Event.interpretation_id == interpretation.id,
            )
            .all()
        )

        assert len(events) == 1
        assert interpretation.title in events[0].description
        assert events[0].source.name == "oracle"

    def test_parse_interpretations_malformed(self, oracle_manager):
        """Test parsing malformed responses."""
        # Test with completely invalid format
        response = "This is not formatted correctly at all."
        parsed = oracle_manager._parse_interpretations(response)
        assert len(parsed) == 0

        # Test with partial formatting
        response = "Some text\n## Title Only\nNo other titles"
        parsed = oracle_manager._parse_interpretations(response)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Title Only"

        # Test with code blocks (which should be removed)
        response = "```markdown\n## Code Block Title\nDescription\n```"
        parsed = oracle_manager._parse_interpretations(response)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Code Block Title"

    def test_multiple_interpretation_sets(
        self,
        oracle_manager,
        mock_anthropic_client,
        test_game,
        test_act,
        test_scene,
        db_session,
    ):
        """Test managing multiple interpretation sets."""
        # Create multiple interpretation sets
        mock_anthropic_client.send_message.side_effect = [
            "## First Set\nDescription 1",
            "## Second Set\nDescription 2",
            "## Third Set\nDescription 3",
        ]

        # Create three sets
        set1 = oracle_manager.get_interpretations(
            test_game.id, test_act.id, test_scene.id, "Question 1", "Result 1", 1
        )
        set2 = oracle_manager.get_interpretations(
            test_game.id, test_act.id, test_scene.id, "Question 2", "Result 2", 1
        )
        set3 = oracle_manager.get_interpretations(
            test_game.id, test_act.id, test_scene.id, "Question 3", "Result 3", 1
        )

        # Verify only the last one is current
        db_session.refresh(set1)
        db_session.refresh(set2)
        db_session.refresh(set3)

        assert set1.is_current is False
        assert set2.is_current is False
        assert set3.is_current is True

        # Verify get_current_interpretation_set returns the last one
        current = oracle_manager.get_current_interpretation_set(test_scene.id)
        assert current.id == set3.id

    def test_get_current_interpretation_set(
        self, oracle_manager, mock_anthropic_client, test_game, test_act, test_scene
    ):
        """Test getting current interpretation set."""
        # Create an interpretation set
        response_text = """## Test Title\nTest Description"""
        mock_anthropic_client.send_message.return_value = response_text

        created_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens?",
            "Mystery",
            1,
        )

        # Get current set and verify it matches
        current_set = oracle_manager.get_current_interpretation_set(test_scene.id)
        assert current_set is not None
        assert current_set.id == created_set.id
        assert current_set.is_current is True

        # Create another set and verify the first is no longer current
        new_set = oracle_manager.get_interpretations(
            test_game.id,
            test_act.id,
            test_scene.id,
            "What happens next?",
            "Danger",
            1,
        )

        current_set = oracle_manager.get_current_interpretation_set(test_scene.id)
        assert current_set.id == new_set.id

        # Verify old set is no longer current
        db_session = oracle_manager._session
        db_session.refresh(created_set)
        assert created_set.is_current is False

    def test_get_current_interpretation_set_none(self, oracle_manager, test_scene):
        """Test getting current interpretation set when none exists."""
        # Ensure no current interpretation sets exist
        db_session = oracle_manager._session
        db_session.query(InterpretationSet).filter(
            InterpretationSet.scene_id == test_scene.id
        ).update({InterpretationSet.is_current: False})
        db_session.commit()

        # Verify get_current_interpretation_set returns None
        current_set = oracle_manager.get_current_interpretation_set(test_scene.id)
        assert current_set is None

    def test_build_interpretation_prompt_for_active_context(
        self,
        oracle_manager,
        game_manager,
        scene_manager,
        act_manager,
        test_game,
        test_act,
        test_scene,
        monkeypatch,
    ):
        """Test building interpretation prompt for active context with acts."""
        # Monkeypatch the manager properties to use our test managers
        monkeypatch.setattr(oracle_manager, "game_manager", game_manager)
        monkeypatch.setattr(oracle_manager, "act_manager", act_manager)
        monkeypatch.setattr(oracle_manager, "scene_manager", scene_manager)

        # Mock the _build_prompt method to avoid actual prompt generation
        original_build_prompt = oracle_manager._build_prompt

        def mock_build_prompt(*args, **kwargs):
            # Just return the arguments to verify they're correct
            return {
                "game_description": args[0],
                "scene_description": args[1],
                "recent_events": args[2],
                "context": args[3],
                "oracle_results": args[4],
                "count": args[5],
            }

        oracle_manager._build_prompt = mock_build_prompt

        try:
            # Call the method
            result = oracle_manager.build_interpretation_prompt_for_active_context(
                "Test context",
                "Test results",
                3,
            )

            # Verify the correct data was passed to _build_prompt
            assert result["game_description"] == test_game.description
            assert result["scene_description"] == test_scene.description
            assert isinstance(result["recent_events"], list)
            assert result["context"] == "Test context"
            assert result["oracle_results"] == "Test results"
            assert result["count"] == 3

        finally:
            # Restore the original method
            oracle_manager._build_prompt = original_build_prompt
