"""Tests for markdown generation utilities."""

import pytest
from unittest.mock import MagicMock, patch

from sologm.cli.utils.markdown import (
    generate_game_markdown,
    generate_scene_markdown,
    generate_event_markdown,
)
from sologm.models.scene import SceneStatus


def test_generate_event_markdown():
    """Test generating markdown for an event."""
    # Create a mock event
    event = MagicMock()
    event.description = "Test event description"
    event.source = "manual"
    
    # Test basic event markdown
    result = generate_event_markdown(event, include_metadata=False)
    assert isinstance(result, list)
    assert "- Test event description" in result[0]
    
    # Test with multiline description
    event.description = "Line 1\nLine 2\nLine 3"
    result = generate_event_markdown(event, include_metadata=False)
    assert len(result) == 3
    assert "- Line 1" in result[0]
    assert "   Line 2" in result[1]
    assert "   Line 3" in result[2]
    
    # Test with oracle source
    event.source = "oracle"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🔮" in result[0]
    
    # Test with dice source
    event.source = "dice"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🎲" in result[0]
    
    # Test with metadata
    event.metadata = {
        "dice_results": {
            "notation": "2d6",
            "total": 7,
            "results": [3, 4]
        }
    }
    result = generate_event_markdown(event, include_metadata=True)
    assert any("Roll: 2d6 = 7" in line for line in result)


def test_generate_scene_markdown():
    """Test generating markdown for a scene."""
    # Create mock objects
    scene = MagicMock()
    scene.sequence = 1
    scene.title = "Test Scene"
    scene.description = "Test scene description"
    scene.status = SceneStatus.ACTIVE
    scene.id = "scene123"
    scene.created_at.strftime.return_value = "2023-01-01"
    scene.completed_at = None
    
    event_manager = MagicMock()
    event_manager.list_events.return_value = []
    
    # Test basic scene markdown without events
    result = generate_scene_markdown(scene, event_manager, include_metadata=False)
    assert isinstance(result, list)
    assert any("### Scene 1: Test Scene" in line for line in result)
    assert any("Test scene description" in line for line in result)
    assert not any("Events" in line for line in result)
    
    # Test with metadata
    result = generate_scene_markdown(scene, event_manager, include_metadata=True)
    assert any("*Scene ID: scene123*" in line for line in result)
    assert any("*Created: 2023-01-01*" in line for line in result)
    
    # Test completed scene
    scene.status = SceneStatus.COMPLETED
    result = generate_scene_markdown(scene, event_manager, include_metadata=False)
    assert any("### Scene 1: Test Scene ✓" in line for line in result)
    
    # Test with events
    mock_event = MagicMock()
    mock_event.description = "Test event"
    mock_event.source = "manual"
    mock_event.created_at.timestamp.return_value = 1
    event_manager.list_events.return_value = [mock_event]
    
    result = generate_scene_markdown(scene, event_manager, include_metadata=False)
    assert any("### Events" in line for line in result)


def test_generate_game_markdown():
    """Test generating markdown for a game."""
    # Create mock objects
    game = MagicMock()
    game.name = "Test Game"
    game.description = "Test game description"
    game.id = "game123"
    game.created_at.strftime.return_value = "2023-01-01"
    
    scene_manager = MagicMock()
    event_manager = MagicMock()
    
    # Test game with no acts
    game.acts = []
    
    # Mock the scene_manager to return scenes when asked
    scene_manager.list_scenes.return_value = []
    
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=False)
    assert "# Test Game" in result
    assert "Test game description" in result
    assert "*No scenes found for this game*" in result
    
    # Test with metadata
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=True)
    assert "*Game ID: game123*" in result
    assert "*Created: 2023-01-01*" in result
    
    # Test with acts and scenes
    act1 = MagicMock()
    act1.sequence = 1
    act1.title = "Act One"
    act1.summary = "Act one summary"
    act1.id = "act1"
    act1.created_at.strftime.return_value = "2023-01-02"
    
    act2 = MagicMock()
    act2.sequence = 2
    act2.title = "Act Two"
    act2.summary = "Act two summary"
    act2.id = "act2"
    act2.created_at.strftime.return_value = "2023-01-03"
    
    game.acts = [act2, act1]  # Deliberately out of order to test sorting
    
    # Mock scenes for each act
    scene1 = MagicMock()
    scene1.sequence = 1
    scene1.title = "Scene One"
    scene1.description = "Scene one description"
    scene1.status = SceneStatus.COMPLETED
    scene1.id = "scene1"
    scene1.created_at.strftime.return_value = "2023-01-02"
    scene1.completed_at = None
    
    scene2 = MagicMock()
    scene2.sequence = 2
    scene2.title = "Scene Two"
    scene2.description = "Scene two description"
    scene2.status = SceneStatus.ACTIVE
    scene2.id = "scene2"
    scene2.created_at.strftime.return_value = "2023-01-03"
    scene2.completed_at = None
    
    # Configure scene_manager to return different scenes for different acts
    def mock_list_scenes(act_id=None, **kwargs):
        if act_id == "act1":
            return [scene1]
        elif act_id == "act2":
            return [scene2]
        return []
    
    scene_manager.list_scenes.side_effect = mock_list_scenes
    
    # Mock empty events list
    event_manager.list_events.return_value = []
    
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=True)
    
    # Check that acts are in correct order
    act1_pos = result.find("## Act 1: Act One")
    act2_pos = result.find("## Act 2: Act Two")
    assert act1_pos < act2_pos
    assert act1_pos > 0
    
    # Check that scenes are included
    assert "### Scene 1: Scene One ✓" in result
    assert "### Scene 2: Scene Two" in result
    
    # Test with untitled act
    act1.title = None
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=False)
    assert "## Act 1: Untitled Act" in result


def test_generate_game_markdown_fallbacks():
    """Test fallback mechanisms in generate_game_markdown."""
    # Create mock objects
    game = MagicMock()
    game.name = "Test Game"
    game.description = "Test game description"
    game.id = "game123"
    
    scene_manager = MagicMock()
    event_manager = MagicMock()
    
    # Test fallback to game.scenes when no acts
    game.acts = None
    
    scene = MagicMock()
    scene.sequence = 1
    scene.title = "Direct Scene"
    scene.description = "Direct scene description"
    scene.status = SceneStatus.ACTIVE
    scene.id = "scene1"
    scene.created_at.strftime.return_value = "2023-01-01"
    scene.completed_at = None
    
    game.scenes = [scene]
    
    # Mock empty events
    event_manager.list_events.return_value = []
    
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=False)
    assert "### Scene 1: Direct Scene" in result
    
    # Test fallback to scene_manager.list_scenes with game_id
    game.scenes = None
    
    scene_manager.list_scenes.return_value = [scene]
    
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=False)
    assert "### Scene 1: Direct Scene" in result
    
    # Test error handling when all fallbacks fail
    scene_manager.list_scenes.side_effect = Exception("Test exception")
    
    result = generate_game_markdown(game, scene_manager, event_manager, include_metadata=False)
    assert "*No scenes found for this game*" in result
