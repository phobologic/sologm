"""Tests for markdown generation utilities."""

from unittest.mock import MagicMock

# Import factory function
from sologm.core.factory import create_all_managers

# Import markdown functions
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
    # Mock the source_name property which is used when include_metadata=True
    event.source_name = "manual"

    # Test basic event markdown
    result = generate_event_markdown(event, include_metadata=False)
    assert isinstance(result, list)
    assert "- Test event description" in result[0]

    # Test with multiline description
    event.description = "Line 1\nLine 2\nLine 3"
    result = generate_event_markdown(event, include_metadata=False)
    assert len(result) == 3
    assert "- Line 1" in result[0]
    # Note: Indentation adjusted based on markdown generator logic
    assert "    Line 2" in result[1]
    assert "    Line 3" in result[2]

    # Test with oracle source
    event.source = "oracle"
    event.source_name = "oracle"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🔮" in result[0]
    # Check multiline indentation with source indicator
    assert "- 🔮: Line 1" in result[0]
    assert "     Line 2" in result[1] # 2 spaces + 3 for indicator + 1 space
    assert "     Line 3" in result[2]

    # Test with dice source
    event.source = "dice"
    event.source_name = "dice"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🎲" in result[0]
    # Check multiline indentation with source indicator
    assert "- 🎲: Line 1" in result[0]
    assert "     Line 2" in result[1]
    assert "     Line 3" in result[2]


    # Test with metadata
    event.source = "dice"
    event.source_name = "dice" # Ensure source_name is set
    result = generate_event_markdown(event, include_metadata=True)
    # Metadata should be indented under the list item
    assert any("  - Source: dice" in line for line in result)


# Updated test using session_context and factory fixtures
def test_generate_scene_markdown(
    session_context, create_test_game, create_test_act, create_test_scene
):
    """Test generating markdown for a scene using real models."""
    with session_context as session:
        managers = create_all_managers(session)
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)

        # Test basic scene markdown without events
        result = generate_scene_markdown(scene, managers.event, include_metadata=False)
        assert isinstance(result, list)
        assert any(
            f"### Scene {scene.sequence}: {scene.title}" in line for line in result
        )
        assert any(scene.description in line for line in result)
        assert not any("### Events" in line for line in result) # No events yet

        # Test with metadata
        result = generate_scene_markdown(scene, managers.event, include_metadata=True)
        assert any(f"*Scene ID: {scene.id}*" in line for line in result)
        assert any("*Created:" in line for line in result)

        # Add an event to the scene using the manager
        event = managers.event.add_event(
            description="Test event for markdown", scene_id=scene.id, source="manual"
        )
        session.flush() # Ensure event is persisted before querying again

        # Test scene with events
        result = generate_scene_markdown(scene, managers.event, include_metadata=False)
        assert any("### Events" in line for line in result)
        # Check if the event description appears after the "### Events" header
        events_section_started = False
        event_found = False
        for line in result:
            if "### Events" in line:
                events_section_started = True
            if events_section_started and "Test event for markdown" in line:
                event_found = True
                break
        assert event_found, "Event description not found in markdown output"


# Updated test using session_context and factory fixtures
def test_generate_act_markdown(
    session_context, create_test_game, create_test_act, create_test_scene
):
    """Test generating markdown for an act using real models."""
    with session_context as session:
        managers = create_all_managers(session)
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        # Add scenes to test their inclusion
        scene1 = create_test_scene(session, act_id=act.id, sequence=1, title="First Scene")
        scene2 = create_test_scene(session, act_id=act.id, sequence=2, title="Second Scene")

        # Test basic act markdown
        result = generate_act_markdown(
            act, managers.scene, managers.event, include_metadata=False
        )
        assert isinstance(result, list)
        assert any(f"## Act {act.sequence}: {act.title}" in line for line in result)
        assert any(act.summary in line for line in result)
        # Check if scenes are included
        assert any(f"### Scene {scene1.sequence}: {scene1.title}" in line for line in result)
        assert any(f"### Scene {scene2.sequence}: {scene2.title}" in line for line in result)


        # Test with metadata
        result = generate_act_markdown(
            act, managers.scene, managers.event, include_metadata=True
        )
        assert any(f"*Act ID: {act.id}*" in line for line in result)
        assert any("*Created:" in line for line in result)
        # Check scene metadata inclusion within act metadata test
        assert any(f"*Scene ID: {scene1.id}*" in line for line in result)


# Updated test using session_context and factory fixtures
def test_generate_game_markdown_with_hierarchy(
    session_context,
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
):
    """Test generating markdown for a game with a complete hierarchy."""
    with session_context as session:
        managers = create_all_managers(session)

        # Build the hierarchy using factory fixtures
        game = create_test_game(session, name="Hierarchy Test Game", description="Full test game.")
        act1 = create_test_act(session, game_id=game.id, title="The First Act", sequence=1)
        act2 = create_test_act(session, game_id=game.id, title="The Second Act", sequence=2)
        scene1_1 = create_test_scene(session, act_id=act1.id, title="Opening Scene", sequence=1)
        scene1_2 = create_test_scene(session, act_id=act1.id, title="Completed Scene", sequence=2, status=SceneStatus.COMPLETED)
        scene2_1 = create_test_scene(session, act_id=act2.id, title="Another Scene", sequence=1)
        event1 = create_test_event(session, scene_id=scene1_1.id, description="First event happens.")
        event2 = create_test_event(session, scene_id=scene1_2.id, description="Second event (oracle).", source="oracle")
        event3 = create_test_event(session, scene_id=scene2_1.id, description="Third event (dice).", source="dice")

        # Store for easier assertion checks
        acts = [act1, act2]
        scenes = [scene1_1, scene1_2, scene2_1]
        events = [event1, event2, event3]

        # Test basic game markdown
        result_str = generate_game_markdown(
            game, managers.scene, managers.event, include_metadata=False
        )

    assert f"# {game.name}" in result_str
    assert game.description in result_str

    # Check that all acts are included
    for act in acts:
        assert f"## Act {act.sequence}: {act.title}" in result_str

    # Check that all scenes are included
    for scene in scenes:
        scene_title = f"### Scene {scene.sequence}: {scene.title}"
        if scene.status == SceneStatus.COMPLETED:
            scene_title += " ✓"
        assert scene_title in result_str

    # Check that all events are included (simple check)
    for event in events:
        # Check only the first line of the event description for simplicity
        first_line_desc = event.description.split('\n')[0]
        assert first_line_desc in result_str
        # Check source indicators
        if event.source == "oracle":
            assert f"🔮: {first_line_desc}" in result_str
        elif event.source == "dice":
            assert f"🎲: {first_line_desc}" in result_str


    # Test with metadata
    with session_context as session: # Re-enter context if needed for managers
        managers = create_all_managers(session)
        # Re-fetch game if necessary, though it should still be in scope
        game = session.get(type(game), game.id)
        result_str_meta = generate_game_markdown(
            game, managers.scene, managers.event, include_metadata=True
        )

    assert f"*Game ID: {game.id}*" in result_str_meta

    # Check act metadata
    for act in acts:
        assert f"*Act ID: {act.id}*" in result_str_meta

    # Check scene metadata
    for scene in scenes:
        assert f"*Scene ID: {scene.id}*" in result_str_meta

    # Check event metadata (source name)
    assert "Source: manual" in result_str_meta
    assert "Source: oracle" in result_str_meta
    assert "Source: dice" in result_str_meta


# Updated test using session_context and factory fixtures
def test_generate_game_markdown_empty(session_context, create_test_game):
    """Test generating markdown for a game with no acts."""
    with session_context as session:
        managers = create_all_managers(session)
        # Create an empty game using the factory
        empty_game = create_test_game(session, name="Empty Game", description="Game with no acts")

        # Test basic game markdown with no acts
        result = generate_game_markdown(
            empty_game, managers.scene, managers.event, include_metadata=False
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


# Updated test using session_context and factory fixtures
def test_game_markdown_with_concepts(session_context, create_test_game):
    """Test generating markdown for a game with concepts header."""
    with session_context as session:
        managers = create_all_managers(session)
        # Create a game using the factory
        game = create_test_game(session, name="Test Game", description="Game with concepts header")

        # Generate markdown with concepts header
        result = generate_game_markdown(
            game,
            managers.scene,
            managers.event,
            include_metadata=False,
            include_concepts=True,
        )

    # Check that concepts header is included
    assert "# Game Structure Guide" in result
    assert "## Game" in result # Concept header section
    assert "## Acts" in result # Concept header section
    assert "## Scenes" in result # Concept header section
    assert "## Events" in result # Concept header section

    # Check that game content follows the concepts header
    assert "# Test Game" in result # Actual game title
    assert "Game with concepts header" in result # Actual game description
