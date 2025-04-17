"""Tests for markdown generation utilities."""

from unittest.mock import MagicMock

from sologm.cli.utils.markdown import (
    generate_act_markdown,
    generate_concepts_header,
    generate_event_markdown,
    generate_game_markdown,
    generate_scene_markdown,
)
from sologm.models.scene import SceneStatus


def test_generate_event_markdown():
    """Test generating markdown for an event."""
    # Create a mock event
    event = MagicMock()
    event.description = "Test event description"
    event.source = "manual"
    event.metadata = {}

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
    event.source_name = "dice"  # Add source_name attribute
    result = generate_event_markdown(event, include_metadata=True)
    assert any("Source: dice" in line for line in result)


def test_generate_scene_markdown(test_scene, event_manager):
    """Test generating markdown for a scene using real models."""
    # Test basic scene markdown without events
    result = generate_scene_markdown(test_scene, event_manager, include_metadata=False)
    assert isinstance(result, list)
    assert any(
        f"### Scene {test_scene.sequence}: {test_scene.title}" in line
        for line in result
    )
    assert any(test_scene.description in line for line in result)

    # Test with metadata
    result = generate_scene_markdown(test_scene, event_manager, include_metadata=True)
    assert any(f"*Scene ID: {test_scene.id}*" in line for line in result)
    assert any("*Created:" in line for line in result)

    # Add an event to the scene
    event = event_manager.add_event(
        description="Test event for markdown", scene_id=test_scene.id, source="manual"
    )

    # Test scene with events
    result = generate_scene_markdown(test_scene, event_manager, include_metadata=False)
    assert any("### Events" in line for line in result)
    assert "Test event for markdown" in " ".join(result)


def test_generate_act_markdown(test_act, scene_manager, event_manager):
    """Test generating markdown for an act using real models."""
    # Test basic act markdown
    result = generate_act_markdown(
        test_act, scene_manager, event_manager, include_metadata=False
    )
    assert isinstance(result, list)
    assert any(
        f"## Act {test_act.sequence}: {test_act.title}" in line for line in result
    )
    assert any(test_act.summary in line for line in result)

    # Test with metadata
    result = generate_act_markdown(
        test_act, scene_manager, event_manager, include_metadata=True
    )
    assert any(f"*Act ID: {test_act.id}*" in line for line in result)
    assert any("*Created:" in line for line in result)


def test_generate_game_markdown_with_hierarchy(
    test_game_with_complete_hierarchy, scene_manager, event_manager, session_context
):
    """Test generating markdown for a game with a complete hierarchy."""
    game, acts, scenes, events = test_game_with_complete_hierarchy

    # Use session_context to ensure the game is attached to a session
    with session_context as session:
        # Merge the game into the current session
        game = session.merge(game)

        # Test basic game markdown
        result = generate_game_markdown(
            game, scene_manager, event_manager, include_metadata=False
        )
    assert f"# {game.name}" in result
    assert game.description in result

    # Check that all acts are included
    for act in acts:
        assert f"## Act {act.sequence}: {act.title}" in result

    # Check that all scenes are included
    for scene in scenes:
        scene_title = f"### Scene {scene.sequence}: {scene.title}"
        if scene.status == SceneStatus.COMPLETED:
            scene_title += " ✓"
        assert scene_title in result

        # Check that all events are included
        for event in events:
            assert event.description in result

        # Test with metadata
        result = generate_game_markdown(
            game, scene_manager, event_manager, include_metadata=True
        )
        assert f"*Game ID: {game.id}*" in result

        # Check act metadata
        for act in acts:
            assert f"*Act ID: {act.id}*" in result

        # Check scene metadata
        for scene in scenes:
            assert f"*Scene ID: {scene.id}*" in result


def test_generate_game_markdown_empty(game_manager, scene_manager, event_manager):
    """Test generating markdown for a game with no acts."""
    # Create an empty game
    empty_game = game_manager.create_game("Empty Game", "Game with no acts")

    # Test basic game markdown with no acts
    result = generate_game_markdown(
        empty_game, scene_manager, event_manager, include_metadata=False
    )
    assert "# Empty Game" in result
    assert "Game with no acts" in result
    # No acts should be included
    assert "## Act" not in result


def test_generate_concepts_header():
    """Test generating the concepts header."""
    header = generate_concepts_header()

    # Check that it's a list of strings
    assert isinstance(header, list)
    assert all(isinstance(line, str) for line in header)

    # Check for key sections
    assert "# Game Structure Guide" in header
    assert any("## Game" in line for line in header)
    assert any("## Acts" in line for line in header)
    assert any("## Scenes" in line for line in header)
    assert any("## Events" in line for line in header)

    # Check for specific content
    assert any("🔮 Oracle interpretations" in line for line in header)
    assert any("🎲 Dice rolls" in line for line in header)
    assert any("✓ indicates completed scenes" in line for line in header)


def test_game_markdown_with_concepts(game_manager, scene_manager, event_manager):
    """Test generating markdown for a game with concepts header."""
    # Create a game
    game = game_manager.create_game("Test Game", "Game with concepts header")

    # Generate markdown with concepts header
    result = generate_game_markdown(
        game,
        scene_manager,
        event_manager,
        include_metadata=False,
        include_concepts=True,
    )

    # Check that concepts header is included
    assert "# Game Structure Guide" in result
    assert "## Game" in result
    assert "## Acts" in result
    assert "## Scenes" in result
    assert "## Events" in result

    # Check that game content follows the concepts header
    assert "# Test Game" in result
    assert "Game with concepts header" in result
