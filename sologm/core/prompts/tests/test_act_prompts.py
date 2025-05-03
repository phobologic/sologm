"""Unit tests for the ActPrompts class."""

import pytest

from sologm.core.prompts.act import ActPrompts


class TestActPrompts:
    """Tests for the ActPrompts prompt generation methods."""

    def _get_base_narrative_data(self) -> dict:
        """Provides a base dictionary with minimal required data."""
        return {
            "game": {"id": "g1", "name": "Test Game", "description": "A test game."},
            "act": {
                "id": "a1",
                "sequence": 1,
                "title": "Act One",
                "summary": "The beginning.",
            },
            "previous_act_summary": None,
            "scenes": [],
            "user_guidance": None,
        }

    def _get_full_narrative_data(self) -> dict:
        """Provides a dictionary with all optional data populated."""
        data = self._get_base_narrative_data()
        data["previous_act_summary"] = "Previously, things happened."
        data["scenes"] = [
            {
                "id": "s1",
                "sequence": 1,
                "title": "Scene One",
                "description": "The first scene.",
                "events": [
                    {
                        "id": "e1",
                        "description": "Event 1 happened.",
                        "source_name": "Manual",
                        "created_at": "2023-01-01T10:00:00Z",
                    },
                    {
                        "id": "e2",
                        "description": "Event 2 followed.",
                        "source_name": "Oracle",
                        "created_at": "2023-01-01T10:05:00Z",
                    },
                ],
            },
            {
                "id": "s2",
                "sequence": 2,
                "title": "Scene Two",
                "description": "The second scene.",
                "events": [],  # Scene with no events
            },
        ]
        data["user_guidance"] = {
            "tone_style": "Gritty noir",
            "point_of_view": "Third-person limited",
            "key_focus": "The detective's internal struggle.",
            "other_instructions": "Mention the rain.",
        }
        return data

    def test_build_narrative_prompt_minimal(self):
        """Test prompt generation with minimal data."""
        data = self._get_base_narrative_data()
        prompt = ActPrompts.build_narrative_prompt(data)

        assert "master storyteller" in prompt  # System instruction
        assert "GAME INFORMATION" in prompt
        assert "Test Game" in prompt
        assert "CURRENT ACT" in prompt
        assert "Act One" in prompt
        assert "SCENES" in prompt
        assert "TASK INSTRUCTION" in prompt
        assert "Markdown format" in prompt

        assert "PREVIOUS ACT CONTEXT" not in prompt
        assert "USER GUIDANCE" not in prompt
        assert "Scene One" not in prompt  # No scenes in minimal data

    def test_build_narrative_prompt_complete(self):
        """Test prompt generation with complete data."""
        data = self._get_full_narrative_data()
        prompt = ActPrompts.build_narrative_prompt(data)

        assert "master storyteller" in prompt
        assert "GAME INFORMATION" in prompt
        assert "Test Game" in prompt
        assert "PREVIOUS ACT CONTEXT" in prompt
        assert "Previously, things happened." in prompt
        assert "CURRENT ACT" in prompt
        assert "Act One" in prompt
        assert "SCENES" in prompt
        assert "Scene One" in prompt
        assert "Event 1 happened." in prompt
        assert "Event 2 followed." in prompt
        assert "Scene Two" in prompt
        assert "USER GUIDANCE" in prompt
        assert "Tone/Style: Gritty noir" in prompt  # Assuming label format
        assert "Point of View: Third-person limited" in prompt
        assert "Key Focus: The detective's internal struggle." in prompt
        assert "Other Instructions: Mention the rain." in prompt
        assert "TASK INSTRUCTION" in prompt
        assert "Markdown format" in prompt

    def test_build_narrative_prompt_no_previous_act(self):
        """Test prompt generation without previous act summary."""
        data = self._get_full_narrative_data()
        data["previous_act_summary"] = None
        prompt = ActPrompts.build_narrative_prompt(data)
        assert "PREVIOUS ACT CONTEXT" not in prompt

    def test_build_narrative_prompt_no_guidance(self):
        """Test prompt generation without user guidance."""
        data = self._get_full_narrative_data()
        data["user_guidance"] = None
        prompt = ActPrompts.build_narrative_prompt(data)
        assert "USER GUIDANCE" not in prompt

        data["user_guidance"] = {}  # Empty dict
        prompt = ActPrompts.build_narrative_prompt(data)
        assert "USER GUIDANCE" not in prompt  # Should also be omitted if empty

    def test_build_narrative_regeneration_prompt(self):
        """Test prompt generation for regeneration with feedback."""
        data = self._get_full_narrative_data()
        previous_narrative = "This was the first attempt."
        feedback = "Make it more exciting."

        prompt = ActPrompts.build_narrative_regeneration_prompt(
            data, previous_narrative, feedback
        )

        # Check all sections from initial prompt are still there
        assert "GAME INFORMATION" in prompt
        assert "PREVIOUS ACT CONTEXT" in prompt
        assert "CURRENT ACT" in prompt
        assert "SCENES" in prompt
        assert "USER GUIDANCE" in prompt

        # Check new sections
        assert "PREVIOUS NARRATIVE" in prompt
        assert previous_narrative in prompt
        assert "USER FEEDBACK" in prompt
        assert feedback in prompt

        # Check modified task instruction
        assert "Generate a *new* narrative" in prompt  # Or similar wording
        assert "incorporating the user feedback" in prompt  # Or similar wording
        assert "Markdown format" in prompt  # Still required
