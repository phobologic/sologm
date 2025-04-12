"""Tests for oracle prompt templates."""

from unittest.mock import MagicMock

from sologm.core.prompts.oracle import OraclePrompts


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


    def test_build_interpretation_prompt(self, test_scene, test_events):
        """Test building the complete interpretation prompt."""
        result = OraclePrompts.build_interpretation_prompt(
            test_scene,
            "What happens next?",
            "Mystery, Danger",
            3,
        )

        # Check that all components are included
        assert "You are interpreting oracle results for a solo RPG player" in result
        assert f"Game: {test_scene.act.game.description}" in result
        assert f"Act: {test_scene.act.description}" in result
        assert f"Current Scene: {test_scene.description}" in result
        # Check for events if they exist in the fixture
        if test_scene.events:
            assert test_scene.events[0].description in result
        assert "Player's Question/Context: What happens next?" in result
        assert "Oracle Results: Mystery, Danger" in result
        assert "Please provide 3 different interpretations" in result

    def test_build_interpretation_prompt_with_retry(self, test_scene):
        """Test building the prompt with retry information."""
        previous_interpretations = [
            {"title": "Previous Title", "description": "Previous Description"},
        ]

        result = OraclePrompts.build_interpretation_prompt(
            test_scene,
            "What happens next?",
            "Mystery, Danger",
            3,
            previous_interpretations=previous_interpretations,
            retry_attempt=1,
        )

        assert "=== PREVIOUS INTERPRETATIONS (DO NOT REPEAT THESE) ===" in result
        assert "## Previous Title" in result
        assert "Previous Description" in result
        assert "retry attempt #2" in result
        assert "COMPLETELY DIFFERENT" in result
