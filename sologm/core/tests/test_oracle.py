"""Tests for oracle interpretation system."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from sologm.core.oracle import OracleManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.errors import OracleError


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def oracle_manager(
    mock_anthropic_client: MagicMock, session: Session
) -> OracleManager:
    """Create an oracle manager instance."""
    return OracleManager(
        anthropic_client=mock_anthropic_client, session=session
    )


@pytest.fixture
def test_game(session: Session) -> Game:
    """Create a test game."""
    game = Game.create(
        name="Test Game",
        description="A test game",
    )
    game.is_active = True
    session.add(game)
    session.commit()
    return game


@pytest.fixture
def test_scene(session: Session, test_game: Game) -> Scene:
    """Create a test scene."""
    scene = Scene.create(
        game_id=test_game.id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
    )
    scene.status = SceneStatus.ACTIVE
    scene.is_current = True
    session.add(scene)
    session.commit()
    return scene


@pytest.fixture
def test_events(session: Session, test_game: Game, test_scene: Scene) -> list[Event]:
    """Create test events."""
    events = [
        Event.create(
            game_id=test_game.id,
            scene_id=test_scene.id,
            description=f"Test event {i}",
            source="manual",
        )
        for i in range(1, 3)
    ]
    session.add_all(events)
    session.commit()
    return events


class TestOracle:
    """Tests for oracle interpretation system."""

    def test_validate_active_context(
        self, oracle_manager: OracleManager, test_game: Game, test_scene: Scene, session: Session
    ) -> None:
        """Test validating active game and scene."""
        from sologm.core.game import GameManager
        from sologm.core.scene import SceneManager
        
        game_manager = GameManager(session=session)
        scene_manager = SceneManager(session=session)
        
        game_id, scene_id = oracle_manager.validate_active_context(game_manager, scene_manager)
        assert game_id == test_game.id
        assert scene_id == test_scene.id

    def test_validate_active_context_no_game(
        self, oracle_manager: OracleManager, session: Session
    ) -> None:
        """Test validation with no active game."""
        from sologm.core.game import GameManager
        from sologm.core.scene import SceneManager
        
        game_manager = GameManager(session=session)
        scene_manager = SceneManager(session=session)
        
        # Make sure no game is active
        session.query(Game).update({Game.is_active: False})
        session.commit()
        
        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context(game_manager, scene_manager)
        assert "No active game found" in str(exc.value)

    def test_validate_active_context_no_scene(
        self, oracle_manager: OracleManager, test_game: Game, session: Session
    ) -> None:
        """Test validation with no active scene."""
        from sologm.core.game import GameManager
        from sologm.core.scene import SceneManager
        
        game_manager = GameManager(session=session)
        scene_manager = SceneManager(session=session)
        
        # Make sure no scene is current
        session.query(Scene).update({Scene.is_current: False})
        session.commit()
        
        with pytest.raises(OracleError) as exc:
            oracle_manager.validate_active_context(game_manager, scene_manager)
        assert "No active scene found" in str(exc.value)

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
        test_game: Game,
        test_scene: Scene,
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
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: Game,
        test_scene: Scene,
    ) -> None:
        """Test handling errors when getting interpretations."""
        mock_anthropic_client.send_message.side_effect = Exception("API Error")

        with pytest.raises(OracleError) as exc:
            oracle_manager.get_interpretations(
                test_game.id, test_scene.id, "What happens?", "Mystery", 1
            )
        assert "Failed to get interpretations" in str(exc.value)

    def test_select_interpretation(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: Game,
        test_scene: Scene,
        session: Session,
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
        events = session.query(Event).filter(
            Event.game_id == test_game.id,
            Event.scene_id == test_scene.id,
            Event.source == "oracle",
            Event.interpretation_id == selected.id
        ).all()
        
        assert len(events) == 1
        assert selected.title in events[0].description

    def test_select_interpretation_not_found(
        self, oracle_manager: OracleManager, test_game: Game, test_scene: Scene
    ) -> None:
        """Test selecting a non-existent interpretation."""
        with pytest.raises(OracleError) as exc:
            oracle_manager.select_interpretation(
                "nonexistent-set", "nonexistent-interp"
            )
        assert "not found" in str(exc.value)

    def test_get_interpretations_with_retry(
        self,
        oracle_manager: OracleManager,
        mock_anthropic_client: MagicMock,
        test_game: Game,
        test_scene: Scene,
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
        assert result1.is_current is False

        # Verify different prompt was used for retry
        retry_call = mock_anthropic_client.send_message.call_args_list[1]
        assert "retry attempt #2" in retry_call[0][0].lower()
        assert "different" in retry_call[0][0].lower()
