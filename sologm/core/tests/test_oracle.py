"""Tests for oracle interpretation system."""

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

from sologm.core.oracle import Interpretation, InterpretationSet, OracleManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.storage.file_manager import FileManager
from sologm.utils.errors import OracleError


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory."""
    return tmp_path


@pytest.fixture
def file_manager(temp_dir: Path) -> FileManager:
    """Create a file manager instance."""
    return FileManager(base_dir=temp_dir)


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def oracle_manager(
    file_manager: FileManager, mock_anthropic_client: MagicMock
) -> OracleManager:
    """Create an oracle manager instance."""
    return OracleManager(
        file_manager=file_manager, anthropic_client=mock_anthropic_client
    )


@pytest.fixture
def test_game(file_manager: FileManager) -> Generator[dict, None, None]:
    """Create a test game."""
    game_data = {
        "id": "test-game",
        "name": "Test Game",
        "description": "A test game",
        "created_at": "2025-04-02T12:00:00Z",
        "modified_at": "2025-04-02T12:00:00Z",
        "scenes": ["test-scene"],
    }

    file_manager.write_yaml(file_manager.get_game_path("test-game"), game_data)
    file_manager.set_active_game_id("test-game")

    yield game_data


@pytest.fixture
def test_scene(
    file_manager: FileManager, test_game: dict
) -> Generator[dict, None, None]:
    """Create a test scene."""
    scene_data = {
        "id": "test-scene",
        "game_id": "test-game",
        "title": "Test Scene",
        "description": "A test scene",
        "status": "active",
        "created_at": "2025-04-02T12:00:00Z",
        "modified_at": "2025-04-02T12:00:00Z",
    }

    file_manager.write_yaml(
        file_manager.get_scene_path("test-game", "test-scene"), scene_data
    )
    file_manager.set_active_scene_id("test-game", "test-scene")

    yield scene_data


@pytest.fixture
def test_events(
    file_manager: FileManager, test_game: dict, test_scene: dict
) -> Generator[dict, None, None]:
    """Create test events."""
    events_data = {
        "events": [
            {
                "id": "event-1",
                "description": "Test event 1",
                "source": "manual",
                "created_at": "2025-04-02T12:00:00Z",
            },
            {
                "id": "event-2",
                "description": "Test event 2",
                "source": "manual",
                "created_at": "2025-04-02T12:01:00Z",
            },
        ]
    }

    file_manager.write_yaml(
        file_manager.get_events_path("test-game", "test-scene"), events_data
    )

    yield events_data


class TestOracle:
    """Tests for oracle interpretation system."""

    def test_validate_active_context(
        self, oracle_manager: OracleManager, test_game: dict, test_scene: dict
    ) -> None:
        """Test validating active game and scene."""
        game_id, scene_id = oracle_manager.validate_active_context()
        assert game_id == "test-game"
        assert scene_id == "test-scene"

    def test_validate_active_context_no_game(
        self, oracle_manager: OracleManager
    ) -> None:
        """Test validation with no active game."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context()
        assert "No active game found" in str(exc.value)

    def test_validate_active_context_no_scene(
        self, oracle_manager: OracleManager, test_game: dict
    ) -> None:
        """Test validation with no active scene."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context()
        assert "No active scene found" in str(exc.value)

    def test_get_current_interpretation(
        self, oracle_manager: OracleManager, test_game: dict
    ) -> None:
        """Test getting current interpretation."""
        # Set up test data
        game_data = oracle_manager._read_game_data("test-game")
        game_data["current_interpretation"] = {
            "id": "test-interp",
            "context": "test context",
            "results": "test results",
            "retry_count": 0,
        }
        oracle_manager.file_manager.write_yaml(
            oracle_manager.file_manager.get_game_path("test-game"), game_data
        )

        current = oracle_manager.get_current_interpretation("test-game")
        assert current["id"] == "test-interp"
        assert current["context"] == "test context"
        assert current["results"] == "test results"
        assert current["retry_count"] == 0

    def test_build_prompt(self, oracle_manager: OracleManager) -> None:
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

    def test_parse_interpretations(self, oracle_manager: OracleManager) -> None:
        """Test parsing Claude's response."""
        response = """=== BEGIN INTERPRETATIONS ===

--- INTERPRETATION 1 ---
TITLE: Test Title 1
DESCRIPTION: Test Description 1
--- END INTERPRETATION 1 ---

--- INTERPRETATION 2 ---
TITLE: Test Title 2
DESCRIPTION: Test Description 2
--- END INTERPRETATION 2 ---

=== END INTERPRETATIONS ==="""

        parsed = oracle_manager._parse_interpretations(response)

        assert len(parsed) == 2
        assert parsed[0]["title"] == "Test Title 1"
        assert parsed[0]["description"] == "Test Description 1"
        assert parsed[1]["title"] == "Test Title 2"
        assert parsed[1]["description"] == "Test Description 2"

    def test_get_interpretations(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: dict,
        test_scene: dict,
        test_events: dict,
    ) -> None:
        """Test getting interpretations."""
        # Configure mock to return string response
        response_text = """=== BEGIN INTERPRETATIONS ===

--- INTERPRETATION 1 ---
TITLE: Test Title
DESCRIPTION: Test Description
--- END INTERPRETATION 1 ---

=== END INTERPRETATIONS ==="""
        mock_anthropic_client.send_message.return_value = response_text

        result = oracle_manager.get_interpretations(
            "test-game", "test-scene", "What happens?", "Mystery", 1
        )

        assert isinstance(result, InterpretationSet)
        assert result.scene_id == "test-scene"
        assert result.context == "What happens?"
        assert result.oracle_results == "Mystery"
        assert len(result.interpretations) == 1
        assert result.interpretations[0].title == "Test Title"
        assert result.interpretations[0].description == "Test Description"

    def test_get_interpretations_error(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: dict,
        test_scene: dict,
    ) -> None:
        """Test handling errors when getting interpretations."""
        mock_anthropic_client.send_message.side_effect = Exception("API Error")

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                "test-game", "test-scene", "What happens?", "Mystery", 1
            )
        assert "Failed to get interpretations" in str(exc.value)

    def test_get_interpretation_set(
        self,
        oracle_manager: OracleManager,
        test_game: dict,
        test_scene: dict,
    ) -> None:
        """Test getting an interpretation set by ID."""
        # Create test interpretation set
        interp_data = {
            "id": "test-interp-set",
            "scene_id": "test-scene",
            "context": "test context",
            "oracle_results": "test results",
            "created_at": "2025-04-02T12:00:00Z",
            "selected_interpretation": None,
            "retry_attempt": 0,
            "interpretations": [
                {
                    "id": "interp-1",
                    "title": "Test Title",
                    "description": "Test Description",
                    "created_at": "2025-04-02T12:00:00Z",
                }
            ],
        }
        oracle_manager.file_manager.write_yaml(
            Path(
                oracle_manager.file_manager.get_interpretations_dir(
                    "test-game", "test-scene"
                ),
                "test-interp-set.yaml",
            ),
            interp_data,
        )

        result = oracle_manager.get_interpretation_set(
            "test-game", "test-scene", "test-interp-set"
        )

        assert isinstance(result, InterpretationSet)
        assert result.id == "test-interp-set"
        assert result.scene_id == "test-scene"
        assert result.context == "test context"
        assert result.oracle_results == "test results"
        assert len(result.interpretations) == 1
        assert result.interpretations[0].title == "Test Title"
        assert result.interpretations[0].description == "Test Description"

    def test_select_interpretation(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: dict,
        test_scene: dict,
    ) -> None:
        """Test selecting an interpretation."""
        # Configure mock to return string response
        response_text = """=== BEGIN INTERPRETATIONS ===

--- INTERPRETATION 1 ---
TITLE: Test Title
DESCRIPTION: Test Description
--- END INTERPRETATION 1 ---

=== END INTERPRETATIONS ==="""
        mock_anthropic_client.send_message.return_value = response_text

        # First create an interpretation set
        interp_set = oracle_manager.get_interpretations(
            "test-game", "test-scene", "What happens?", "Mystery", 1
        )

        # Then select the interpretation
        selected = oracle_manager.select_interpretation(
            "test-game", "test-scene", interp_set.id, interp_set.interpretations[0].id
        )

        assert isinstance(selected, Interpretation)
        assert selected.id == interp_set.interpretations[0].id
        assert selected.title == interp_set.interpretations[0].title

        # Verify event was created
        events = oracle_manager.file_manager.read_yaml(
            oracle_manager.file_manager.get_events_path("test-game", "test-scene")
        )
        assert any(
            event["source"] == "oracle" and selected.title in event["description"]
            for event in events["events"]
        )

    def test_select_interpretation_not_found(
        self, oracle_manager: OracleManager, test_game: dict, test_scene: dict
    ) -> None:
        """Test selecting a non-existent interpretation."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.select_interpretation(
                "test-game", "test-scene", "nonexistent-set", "nonexistent-interp"
            )
        assert "not found" in str(exc.value)

    def test_get_interpretations_with_retry(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: dict,
        test_scene: dict,
    ) -> None:
        """Test getting interpretations with retry attempt."""
        # Configure mock to return string response
        response_text = """=== BEGIN INTERPRETATIONS ===

--- INTERPRETATION 1 ---
TITLE: Test Title
DESCRIPTION: Test Description
--- END INTERPRETATION 1 ---

=== END INTERPRETATIONS ==="""
        mock_anthropic_client.send_message.return_value = response_text

        # First interpretation request
        result1 = oracle_manager.get_interpretations(
            "test-game", "test-scene", "What happens?", "Mystery", 1
        )

        # Verify current interpretation was set
        game_data = oracle_manager.file_manager.read_yaml(
            oracle_manager.file_manager.get_game_path("test-game")
        )
        assert "current_interpretation" in game_data
        assert game_data["current_interpretation"]["id"] == result1.id
        assert game_data["current_interpretation"]["retry_count"] == 0

        # Retry interpretation
        result2 = oracle_manager.get_interpretations(
            "test-game", "test-scene", "What happens?", "Mystery", 1, retry_attempt=1
        )

        # Verify retry count was updated
        game_data = oracle_manager.file_manager.read_yaml(
            oracle_manager.file_manager.get_game_path("test-game")
        )
        assert game_data["current_interpretation"]["id"] == result2.id
        assert game_data["current_interpretation"]["retry_count"] == 1

        # Verify different prompt was used for retry
        retry_call = mock_anthropic_client.send_message.call_args_list[1]
        assert "retry attempt #2" in retry_call[0][0].lower()
        assert "different" in retry_call[0][0].lower()
