"""
Tests for the GameAIHelper class.
"""
import json
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType, MythicChaosFactor
from sologm.rpg_helper.models.scene import Scene, SceneStatus
from sologm.rpg_helper.models.scene_event import SceneEvent
from sologm.rpg_helper.services.ai.game_helper import GameAIHelper
from sologm.rpg_helper.services.game.mythic_game_service import MythicGameService
from sologm.rpg_helper.services.game.game_service import GameService


@pytest.fixture
def mock_game():
    """Create a mock game."""
    game = MagicMock(spec=Game)
    game.id = "test-game-id"
    game.title = "Test Game"
    game.description = "A test game"
    game.setting_info = "A test setting"
    game.current_scene_id = None
    return game


@pytest.fixture
def mock_scene():
    """Create a mock scene."""
    scene = MagicMock(spec=Scene)
    scene.id = "test-scene-id"
    scene.title = "Test Scene"
    scene.description = "A test scene"
    
    # Add events with proper datetime objects
    event1 = MagicMock(spec=SceneEvent)
    event1.text = "Event 1"
    event1.created_at = datetime(2023, 1, 1, 12, 0, 0)
    
    event2 = MagicMock(spec=SceneEvent)
    event2.text = "Event 2"
    event2.created_at = datetime(2023, 1, 1, 12, 5, 0)
    
    scene.events = [event1, event2]
    return scene


@pytest.fixture
def mock_game_with_scene(mock_game, mock_scene):
    """Create a mock game with a scene."""
    mock_game.current_scene_id = mock_scene.id
    return mock_game


def test_init(mock_game):
    """Test initialization of GameAIHelper."""
    helper = GameAIHelper(mock_game)
    assert helper.game == mock_game
    assert helper.game_service is not None


def test_get_game_context_standard(mock_game, mock_scene):
    """Test getting game context for a standard game."""
    # Setup
    mock_game.game_type = GameType.STANDARD
    mock_game.current_scene_id = "test-scene-id"
    
    # Mock the game service
    mock_service = MagicMock(spec=GameService)
    mock_service.get_scene.return_value = mock_scene
    
    # Create helper with mocked service
    helper = GameAIHelper(mock_game)
    helper.game_service = mock_service
    
    # Execute
    context = helper.get_game_context()
    
    # Verify
    assert context["game_id"] == mock_game.id
    assert context["game_name"] == mock_game.name
    assert context["game_type"] == mock_game.game_type.value
    assert context["game_description"] == mock_game.description
    
    # Verify active scene
    assert "active_scene" in context
    assert context["active_scene"]["id"] == mock_scene.id
    assert context["active_scene"]["title"] == mock_scene.title
    assert context["active_scene"]["description"] == mock_scene.description
    assert len(context["active_scene"]["events"]) == 2


def test_get_game_context_mythic(mock_game):
    """Test getting game context for a Mythic game."""
    # Setup
    mock_game.game_type = GameType.MYTHIC
    mock_game.current_scene_id = None
    
    # Mock the Mythic game service with proper spec and methods
    mock_service = MagicMock(spec=MythicGameService)
    mock_service.get_scene = MagicMock(return_value=None)
    mock_service.get_chaos_factor = MagicMock(return_value=MythicChaosFactor.AVERAGE)
    
    # Create helper with mocked service
    helper = GameAIHelper(mock_game)
    helper.game_service = mock_service
    
    # Execute
    context = helper.get_game_context()
    
    # Verify
    assert context["game_id"] == mock_game.id
    assert context["game_name"] == mock_game.name
    assert context["game_type"] == mock_game.game_type.value
    assert context["chaos_factor"] == MythicChaosFactor.AVERAGE
    assert "active_scene" not in context


def test_generate_outcome_ideas_default_params(mock_game, mock_scene):
    """Test generating ideas with default parameters."""
    # Mock AI service
    ai_service = MagicMock()
    ai_service.generate_text = MagicMock(return_value=json.dumps([
        "Outcome 1",
        "Outcome 2",
        "Outcome 3",
        "Outcome 4",
        "Outcome 5"
    ]))

    # Mock game service
    mock_service = MagicMock(spec=GameService)
    mock_service.get_scene.return_value = mock_scene

    # Set current scene on game
    mock_game.current_scene_id = mock_scene.id

    # Create helper with mocked services
    helper = GameAIHelper(mock_game)
    helper.game_service = mock_service
    helper.ai_service = ai_service

    # Execute
    outcomes = helper.generate_outcome_ideas(game=mock_game)

    # Verify
    assert len(outcomes) == 5
    assert "Outcome 1" in outcomes
    assert "Outcome 5" in outcomes

    # Verify AI service was called with appropriate prompt
    ai_service.generate_text.assert_called_once()
    call_args = ai_service.generate_text.call_args
    assert call_args is not None
    assert "prompt" in call_args.kwargs
    prompt = call_args.kwargs["prompt"]
    assert mock_scene.title in prompt
    assert mock_scene.description in prompt


def test_generate_outcome_ideas_no_scene(mock_game):
    """Test generating ideas with no scene."""
    helper = GameAIHelper(mock_game)
    mock_game.current_scene_id = None

    with pytest.raises(ValueError) as excinfo:
        helper.generate_outcome_ideas(game=mock_game)
    assert "No scene provided and game has no current scene" in str(excinfo.value)


def test_generate_outcome_ideas_with_scene_id(mock_game_with_scene, mock_scene):
    """Test generating ideas with scene ID."""
    # Mock AI service
    ai_service = MagicMock()
    ai_service.generate_text.return_value = json.dumps([
        "Outcome 1",
        "Outcome 2",
        "Outcome 3"
    ])
    
    # Create helper with mocked services
    helper = GameAIHelper(mock_game_with_scene)
    helper.ai_service = ai_service
    
    # Generate ideas using the scene directly
    ideas = helper.generate_outcome_ideas(
        game=mock_game_with_scene,
        scene=mock_scene,
        num_ideas=3
    )
    
    # Check results
    assert len(ideas) == 3
    
    # Check that AI service was called
    ai_service.generate_text.assert_called_once()


def test_parse_outcome_ideas():
    """Test parsing outcome ideas from AI response."""
    helper = GameAIHelper(MagicMock())
    
    # Test with valid JSON array
    response = json.dumps([
        "Idea 1",
        "Idea 2",
        "Idea 3"
    ])
    
    ideas = helper._parse_outcome_ideas(response, 3)
    
    assert len(ideas) == 3
    assert ideas[0] == "Idea 1"
    assert ideas[1] == "Idea 2"
    assert ideas[2] == "Idea 3"
    
    # Test with fewer ideas than requested
    response = json.dumps([
        "Idea 1",
        "Idea 2"
    ])
    
    ideas = helper._parse_outcome_ideas(response, 3)
    
    assert len(ideas) == 2
    
    # Test with more ideas than requested
    response = json.dumps([
        "Idea 1",
        "Idea 2",
        "Idea 3",
        "Idea 4"
    ])
    
    ideas = helper._parse_outcome_ideas(response, 3)
    
    assert len(ideas) == 3  # Should truncate to requested number 


@pytest.fixture
def mock_game_service(mock_game, mock_scene):
    service = MagicMock(spec=GameService)
    service.game = mock_game
    service.get_scene.return_value = mock_scene
    return service


@pytest.fixture
def mock_mythic_service(mock_game, mock_scene):
    service = MagicMock(spec=MythicGameService)
    service.game = mock_game
    service.get_scene.return_value = mock_scene
    service.get_chaos_factor.return_value = 5
    return service 