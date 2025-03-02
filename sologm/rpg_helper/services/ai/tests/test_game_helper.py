"""
Tests for the GameAIHelper class.
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from sologm.rpg_helper.services.ai.game_helper import GameAIHelper
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.scene import Scene

def test_init():
    """Test initialization."""
    ai_service = MagicMock()
    helper = GameAIHelper(ai_service)
    
    assert helper.ai_service is ai_service

def test_generate_outcome_ideas():
    """Test generating ideas."""
    # Mock AI service
    ai_service = MagicMock()
    ai_service.generate_text.return_value = json.dumps([
        "The heroes find a hidden treasure.",
        "A trap is sprung, separating the party.",
        "An old enemy appears unexpectedly."
    ])
    
    helper = GameAIHelper(ai_service)
    
    # Create game and scene
    game = Game(id="game1", name="Test", creator_id="user1", channel_id="channel1")
    scene = game.current_scene  # Use the automatically created scene
    
    # Generate ideas
    ideas = helper.generate_outcome_ideas(
        game=game,
        scene=scene,
        additional_context="The party is exploring a dungeon.",
        focus_words=["treasure", "trap"],
        num_ideas=3
    )
    
    # Check results
    assert len(ideas) == 3
    assert "treasure" in ideas[0]
    assert "trap" in ideas[1]
    assert "enemy" in ideas[2]
    
    # Check that AI service was called with appropriate prompt
    ai_service.generate_text.assert_called_once()
    # Use kwargs instead of positional args
    prompt = ai_service.generate_text.call_args.kwargs.get('prompt')
    assert "Test" in prompt
    assert "exploring a dungeon" in prompt
    assert "treasure" in prompt
    assert "trap" in prompt

def test_generate_outcome_ideas_default_params():
    """Test generating ideas with default parameters."""
    # Mock AI service
    ai_service = MagicMock()
    ai_service.generate_text.return_value = json.dumps([
        "Outcome 1",
        "Outcome 2",
        "Outcome 3",
        "Outcome 4",
        "Outcome 5"
    ])
    
    helper = GameAIHelper(ai_service)
    
    # Create game and scene
    game = Game(id="game1", name="Test", creator_id="user1", channel_id="channel1")
    scene = game.current_scene  # Use the automatically created scene
    
    # Generate ideas with minimal parameters
    ideas = helper.generate_outcome_ideas(game=game, scene=scene)
    
    # Check results
    assert len(ideas) == 5  # Default is 5 ideas
    
    # Check that AI service was called
    ai_service.generate_text.assert_called_once()

def test_generate_outcome_ideas_no_scene():
    """Test generating ideas with no scene."""
    helper = GameAIHelper(MagicMock())
    game = Game(id="game1", name="Test", creator_id="user1", channel_id="channel1")
    
    # Remove the automatically created scene
    game.current_scene = None
    
    with pytest.raises(ValueError) as excinfo:
        helper.generate_outcome_ideas(game=game)
    
    assert "No scene provided and game has no current scene" in str(excinfo.value)

def test_generate_outcome_ideas_with_scene_id():
    """Test generating ideas with scene ID."""
    # Mock AI service
    ai_service = MagicMock()
    ai_service.generate_text.return_value = json.dumps([
        "Outcome 1",
        "Outcome 2",
        "Outcome 3"
    ])
    
    helper = GameAIHelper(ai_service)
    
    # Create game and scene
    game = Game(id="game1", name="Test", creator_id="user1", channel_id="channel1")
    scene = game.current_scene  # Use the automatically created scene
    
    # Generate ideas using the scene directly
    ideas = helper.generate_outcome_ideas(
        game=game,
        scene=scene,
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