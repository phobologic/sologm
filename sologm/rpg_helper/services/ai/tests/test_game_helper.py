"""
Tests for the game AI helper.
"""
import pytest
from unittest.mock import MagicMock, patch

from sologm.rpg_helper.models.game import Game
from sologm.rpg_helper.models.scene import Scene
from sologm.rpg_helper.services.ai import AIService
from sologm.rpg_helper.services.ai.game_helper import GameAIHelper


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = MagicMock(spec=AIService)
    service.generate_text.return_value = """
Here are 5 potential outcome ideas:

1. The ancient artifact suddenly glows with an eerie blue light, revealing hidden symbols on the cave walls that point to a secret passage.

2. A group of rival adventurers bursts into the chamber, demanding that you hand over the map and threatening violence if you refuse.

3. The ground begins to shake violently, causing stalactites to fall from the ceiling and blocking your original entrance path.

4. One of your companions suddenly clutches their head in pain, claiming to hear whispers from the artifact that promise great power in exchange for a sacrifice.

5. You notice strange markings on the floor that, when stepped on in the correct sequence, might activate a magical portal to another location entirely.
"""
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


def test_parse_outcome_ideas_fallback():
    """Test parsing when the response doesn't have numbered items."""
    helper = GameAIHelper(MagicMock())
    
    # Response without numbered items
    response = """
The artifact reveals a hidden map.

A strange creature appears from the shadows.

The cave begins to collapse.

You hear voices coming from deeper in the cave.

A magical barrier prevents you from leaving.
"""
    
    ideas = helper._parse_outcome_ideas(response, 5)
    
    assert len(ideas) == 5
    assert "artifact reveals" in ideas[0]
    assert "strange creature" in ideas[1]
    assert "cave begins to collapse" in ideas[2]
    assert "hear voices" in ideas[3]
    assert "magical barrier" in ideas[4] 