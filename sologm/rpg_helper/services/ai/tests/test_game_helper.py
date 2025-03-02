"""
Tests for the game AI helper.
"""
import pytest
from unittest.mock import MagicMock, patch

from sologm.rpg_helper.models.game import Game
from sologm.rpg_helper.models.scene import Scene
from sologm.rpg_helper.services.ai import AIService, AIResponseError
from sologm.rpg_helper.services.ai.game_helper import GameAIHelper
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = MagicMock(spec=AIService)
    service.generate_text.return_value = """[
        "The ancient artifact suddenly glows with an eerie blue light, revealing hidden symbols on the cave walls that point to a secret passage.",
        "A group of rival adventurers bursts into the chamber, demanding that you hand over the map and threatening violence if you refuse.",
        "The ground begins to shake violently, causing stalactites to fall from the ceiling and blocking your original entrance path.",
        "One of your companions suddenly clutches their head in pain, claiming to hear whispers from the artifact that promise great power in exchange for a sacrifice.",
        "You notice strange markings on the floor that, when stepped on in the correct sequence, might activate a magical portal to another location entirely."
    ]"""
    return service


@pytest.fixture
def test_game():
    """Create a test game."""
    return Game(
        id="game1",
        name="Test Adventure",
        creator_id="user1",
        channel_id="channel1",
        setting_info="A high fantasy world with ancient ruins and powerful magic."
    )


@pytest.fixture
def test_scene(test_game):
    """Create a test scene."""
    scene = Scene(
        id="scene1",
        game=test_game,
        title="The Hidden Cave",
        description="The party has discovered a hidden cave behind a waterfall, containing strange symbols and an ancient artifact."
    )
    scene.add_event("The party carefully approached the artifact on the pedestal.")
    scene.add_event("Mysterious runes began to glow faintly when touched.")
    return scene


def test_generate_outcome_ideas(mock_ai_service, test_game, test_scene):
    """Test generating outcome ideas."""
    helper = GameAIHelper(mock_ai_service)
    
    ideas = helper.generate_outcome_ideas(
        game=test_game,
        scene=test_scene,
        additional_context="The party is looking for a way to unlock the artifact's power.",
        focus_words=["trap", "guardian"]
    )
    
    # Check that the AI service was called with appropriate arguments
    mock_ai_service.generate_text.assert_called_once()
    prompt = mock_ai_service.generate_text.call_args[1]["prompt"]
    
    # Verify prompt contains key elements
    assert "Test Adventure" in prompt
    assert "The Hidden Cave" in prompt
    assert "high fantasy world" in prompt
    assert "trap, guardian" in prompt
    assert "looking for a way to unlock" in prompt
    assert "FORMAT: Respond with a JSON array" in prompt
    
    # Check that we got the expected number of ideas
    assert len(ideas) == 5
    assert "ancient artifact suddenly glows" in ideas[0]
    assert "rival adventurers" in ideas[1]
    assert "ground begins to shake" in ideas[2]
    assert "whispers from the artifact" in ideas[3]
    assert "strange markings on the floor" in ideas[4]


def test_generate_outcome_ideas_no_scene():
    """Test generating ideas with no scene."""
    helper = GameAIHelper(MagicMock())
    game = Game(id="game1", name="Test", creator_id="user1", channel_id="channel1")
    
    with pytest.raises(ValueError) as excinfo:
        helper.generate_outcome_ideas(game=game)
    
    assert "No scene provided" in str(excinfo.value)


def test_parse_outcome_ideas_invalid_json():
    """Test handling invalid JSON response."""
    helper = GameAIHelper(MagicMock())
    
    invalid_response = """
    Here are some ideas:
    1. The artifact reveals a hidden map.
    2. A strange creature appears.
    """
    
    with pytest.raises(AIResponseError) as excinfo:
        helper._parse_outcome_ideas(invalid_response, 5)
    
    assert "Failed to parse JSON response" in str(excinfo.value)


def test_parse_outcome_ideas_not_array():
    """Test handling JSON response that's not an array."""
    helper = GameAIHelper(MagicMock())
    
    invalid_response = '{"ideas": ["First idea", "Second idea"]}'
    
    with pytest.raises(AIResponseError) as excinfo:
        helper._parse_outcome_ideas(invalid_response, 5)
    
    assert "Expected JSON array in response" in str(excinfo.value)


def test_parse_outcome_ideas_fewer_than_expected():
    """Test handling fewer ideas than requested."""
    helper = GameAIHelper(MagicMock())
    
    response = '["First idea", "Second idea"]'
    
    ideas = helper._parse_outcome_ideas(response, 5)
    
    assert len(ideas) == 2
    assert ideas[0] == "First idea"
    assert ideas[1] == "Second idea" 