"""Tests for oracle interpretation system."""

import pytest

from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene
from sologm.utils.errors import OracleError


class TestOracle:
    """Tests for oracle interpretation system."""

    def test_validate_active_context(
        self, oracle_manager, test_game, test_scene, game_manager, scene_manager
    ) -> None:
        """Test validating active game and scene."""
        game_id, scene_id = oracle_manager.validate_active_context(
            game_manager, scene_manager
        )
        assert game_id == test_game.id
        assert scene_id == test_scene.id

    def test_validate_active_context_no_game(
        self, oracle_manager, game_manager, scene_manager, db_session
    ) -> None:
        """Test validation with no active game."""
        # Make sure no game is active
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context(game_manager, scene_manager)
        assert "No active game found" in str(exc.value)

    def test_validate_active_context_no_scene(
        self, oracle_manager, test_game, game_manager, scene_manager, db_session
    ) -> None:
        """Test validation with no active scene."""
        # Make sure no scene is active
        db_session.query(Scene).update({Scene.is_active: False})
        db_session.commit()

        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context(game_manager, scene_manager)
        assert "No active scene found" in str(exc.value)

    def test_build_prompt(self, oracle_manager) -> None:
        """Test building prompts for Claude."""
        prompt = oracle_manager._build_prompt(
            "Test Game",
            "Test Scene",
            ["Event 1", "Event 2"],
            "What happens next?",
            "Mystery, Danger",
            3,
        )

        assert "Test Game" in prompt
        assert "Test Scene" in prompt
        assert "Event 1" in prompt
        assert "Event 2" in prompt
        assert "What happens next?" in prompt
        assert "Mystery, Danger" in prompt
        assert "3 different interpretations" in prompt
        assert "## [Title of first interpretation]" in prompt
        assert "Do not number the interpretations" in prompt
        
    def test_build_prompt_with_previous_interpretations(self, oracle_manager) -> None:
        """Test building prompts with previous interpretations."""
        previous_interpretations = [
            {"title": "Previous Title 1", "description": "Previous Description 1"},
            {"title": "Previous Title 2", "description": "Previous Description 2"},
        ]
        
        prompt = oracle_manager._build_prompt(
            "Test Game",
            "Test Scene",
            ["Event 1", "Event 2"],
            "What happens next?",
            "Mystery, Danger",
            3,
            previous_interpretations=previous_interpretations,
            retry_attempt=1,
        )
        
        assert "=== PREVIOUS INTERPRETATIONS (DO NOT REPEAT THESE) ===" in prompt
        assert "## Previous Title 1" in prompt
        assert "Previous Description 1" in prompt
        assert "## Previous Title 2" in prompt
        assert "Previous Description 2" in prompt
        assert "=== END OF PREVIOUS INTERPRETATIONS ===" in prompt
        assert "retry attempt #2" in prompt

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
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
    ) -> None:
        """Test getting interpretations."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        result = oracle_manager.get_interpretations(
            test_game.id, test_scene.id, "What happens?", "Mystery", 1
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
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
    ) -> None:
        """Test handling errors when getting interpretations."""
        mock_anthropic_client.send_message.side_effect = Exception("API Error")

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                test_game.id, test_scene.id, "What happens?", "Mystery", 1
            )
        assert "Failed to get interpretations" in str(exc.value)

    def test_select_interpretation(
        self, oracle_manager, mock_anthropic_client, test_game, test_scene, db_session
    ) -> None:
        """Test selecting an interpretation."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        # First create an interpretation set
        interp_set = oracle_manager.get_interpretations(
            test_game.id, test_scene.id, "What happens?", "Mystery", 1
        )

        # Then select the interpretation
        selected = oracle_manager.select_interpretation(
            interp_set.id, interp_set.interpretations[0].id, add_event=True
        )

        assert isinstance(selected, Interpretation)
        assert selected.id == interp_set.interpretations[0].id
        assert selected.title == interp_set.interpretations[0].title
        assert selected.is_selected is True

        # Verify event was created
        events = (
            db_session.query(Event)
            .filter(
                Event.game_id == test_game.id,
                Event.scene_id == test_scene.id,
                Event.source == "oracle",
                Event.interpretation_id == selected.id,
            )
            .all()
        )

        assert len(events) == 1
        assert selected.title in events[0].description

    def test_select_interpretation_not_found(
        self, oracle_manager, test_game, test_scene
    ) -> None:
        """Test selecting a non-existent interpretation."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.select_interpretation(
                "nonexistent-set", "nonexistent-interp"
            )
        assert "not found" in str(exc.value)

    def test_get_interpretations_with_retry(
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
    ) -> None:
        """Test getting interpretations with retry attempt."""
        # Configure mock to return string response
        response_text = """## Test Title
Test Description"""
        mock_anthropic_client.send_message.return_value = response_text

        # First interpretation request
        result1 = oracle_manager.get_interpretations(
            test_game.id, test_scene.id, "What happens?", "Mystery", 1
        )
        assert result1.retry_attempt == 0
        assert result1.is_current is True

        # Retry interpretation
        result2 = oracle_manager.get_interpretations(
            test_game.id, test_scene.id, "What happens?", "Mystery", 1, retry_attempt=1
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
        self, oracle_manager, mock_anthropic_client, test_game, test_scene, db_session
    ):
        """Test automatic retry when parsing fails."""
        # Debug: Print initial state
        from sologm.models.game import Game
        from sologm.models.scene import Scene
        games = db_session.query(Game).all()
        scenes = db_session.query(Scene).all()
        print("\n=== INITIAL STATE ===")
        print(f"Test game ID: {test_game.id}")
        print(f"Test scene ID: {test_scene.id}")
        print(f"Games in DB: {[g.id for g in games]}")
        print(f"Scenes in DB: {[s.id for s in scenes]}")
        
        # First response has no interpretations (bad format)
        # Second response has valid interpretations
        mock_anthropic_client.send_message.side_effect = [
            "No proper format here",  # First call - bad format
            """## Retry Title
Retry Description""",  # Second call - good format
        ]

        # This should automatically retry once
        try:
            result = oracle_manager.get_interpretations(
                test_game.id, test_scene.id, "What happens?", "Mystery", 1
            )
            
            # Debug: Print final state if successful
            games = db_session.query(Game).all()
            scenes = db_session.query(Scene).all()
            print("\n=== FINAL STATE (SUCCESS) ===")
            print(f"Games in DB: {[g.id for g in games]}")
            print(f"Scenes in DB: {[s.id for s in scenes]}")
            
        except Exception as e:
            # Debug: Print state after error
            games = db_session.query(Game).all()
            scenes = db_session.query(Scene).all()
            print("\n=== FINAL STATE (ERROR) ===")
            print(f"Error: {str(e)}")
            print(f"Games in DB: {[g.id for g in games]}")
            print(f"Scenes in DB: {[s.id for s in scenes]}")
            raise

        # Verify we got the result from the second attempt
        assert mock_anthropic_client.send_message.call_count == 2
        assert result.retry_attempt == 1  # Should be marked as retry attempt 1
        assert len(result.interpretations) == 1
        assert result.interpretations[0].title == "Retry Title"

    def test_automatic_retry_max_attempts(
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
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
                test_game.id, test_scene.id, "What happens?", "Mystery", 1
            )

        # Verify we tried 3 times total (original + 2 retries)
        assert mock_anthropic_client.send_message.call_count == 3
        assert "after 3 attempts" in str(exc.value)

    def test_automatic_retry_with_custom_max(
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
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
        self, oracle_manager, mock_anthropic_client, test_game, test_scene
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
            test_game.id, test_scene.id, "What happens?", "Mystery, Danger", 2
        )

        assert len(result.interpretations) == 2
        assert result.interpretations[0].title == "First Interpretation"
        assert "multiple lines" in result.interpretations[0].description
        assert result.interpretations[1].title == "Second Interpretation"
