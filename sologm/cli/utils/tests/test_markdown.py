"""Tests for markdown generation utilities."""

from unittest.mock import MagicMock

# Import markdown functions
from sologm.cli.utils.markdown import (
    generate_act_markdown,
    generate_concepts_header,
    generate_event_markdown,
    generate_game_markdown,
    generate_scene_markdown,
)

# Import factory function
from sologm.core.factory import create_all_managers


def test_generate_event_markdown():
    """Test generating markdown for an event."""
    event = MagicMock()
    event.description = "Test event description"
    event.source = "manual"
    # Mock the source_name property which is used when include_metadata=True
    event.source_name = "manual"

    result = generate_event_markdown(event, include_metadata=False)
    assert isinstance(result, list)
    assert "- Test event description" in result[0]

    event.description = "Line 1\nLine 2\nLine 3"
    result = generate_event_markdown(event, include_metadata=False)
    assert len(result) == 3
    assert "- Line 1" in result[0]
    # Note: Indentation adjusted based on markdown generator logic
    assert "    Line 2" in result[1]
    assert "    Line 3" in result[2]

    event.source = "oracle"
    event.source_name = "oracle"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🔮" in result[0]
    # Check multiline indentation with source indicator
    assert "- 🔮: Line 1" in result[0]
    assert "     Line 2" in result[1]  # Verify indentation with source indicator.
    assert "     Line 3" in result[2]

    event.source = "dice"
    event.source_name = "dice"
    result = generate_event_markdown(event, include_metadata=False)
    assert "🎲" in result[0]
    # Check multiline indentation with source indicator
    assert "- 🎲: Line 1" in result[0]
    assert "     Line 2" in result[1]
    assert "     Line 3" in result[2]

    event.source = "dice"
    event.source_name = "dice"  # Ensure source_name is set for metadata test.
    result = generate_event_markdown(event, include_metadata=True)
    # Verify metadata is indented under the list item.
    assert any("  - Source: dice" in line for line in result)


# Test uses session_context and factory fixtures for realistic data.
def test_generate_scene_markdown(
    session_context,
    create_test_game,
    create_test_act,
    create_test_scene,
    initialize_event_sources,  # Add the fixture here
):
    """Test generating markdown for a scene using real models."""
    with session_context as session:
        initialize_event_sources(session)  # Call the initializer function

        managers = create_all_managers(session)
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)

        result = generate_scene_markdown(scene, managers.event, include_metadata=False)
        assert isinstance(result, list)
        assert any(
            f"### Scene {scene.sequence}: {scene.title}" in line for line in result
        )
        assert any(scene.description in line for line in result)
        assert not any(
            "### Events" in line for line in result
        )  # Verify no events section yet.

        result = generate_scene_markdown(scene, managers.event, include_metadata=True)
        assert any(f"*Scene ID: {scene.id}*" in line for line in result)
        assert any("*Created:" in line for line in result)

        event = managers.event.add_event(
            description="Test event for markdown", scene_id=scene.id, source="manual"
        )
        session.flush()  # Ensure event is persisted before querying again by generate_scene_markdown.

        result = generate_scene_markdown(scene, managers.event, include_metadata=False)
        assert any("### Events" in line for line in result)
        events_section_started = False
        event_found = False
        for line in result:
            if "### Events" in line:
                events_section_started = True
            if events_section_started and "Test event for markdown" in line:
                event_found = True
                break
        assert event_found, "Event description not found in markdown output"


# Test uses session_context and factory fixtures for realistic data.
def test_generate_act_markdown(
    session_context, create_test_game, create_test_act, create_test_scene
):
    """Test generating markdown for an act using real models."""
    with session_context as session:
        managers = create_all_managers(session)
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
        scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

        result = generate_act_markdown(
            act, managers.scene, managers.event, include_metadata=False
        )
        assert isinstance(result, list)
        assert any(f"## Act {act.sequence}: {act.title}" in line for line in result)
        assert any(act.summary in line for line in result)
        # Refresh scene objects to ensure sequence numbers are loaded before assertion.
        session.refresh(scene1)
        session.refresh(scene2)
        assert any(
            f"### Scene {scene1.sequence}: {scene1.title}" in line for line in result
        )
        assert any(
            f"### Scene {scene2.sequence}: {scene2.title}" in line for line in result
        )

        result = generate_act_markdown(
            act, managers.scene, managers.event, include_metadata=True
        )
        assert any(f"*Act ID: {act.id}*" in line for line in result)
        assert any("*Created:" in line for line in result)
        # Verify scene metadata is included when act metadata is requested.
        assert any(f"*Scene ID: {scene1.id}*" in line for line in result)


# Test uses session_context and factory fixtures for realistic data.
def test_generate_game_markdown_with_hierarchy(
    session_context,
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources,  # <-- Add fixture argument here
):
    """Test generating markdown for a game with a complete hierarchy."""
    with session_context as session:
        initialize_event_sources(session)  # <-- Call the initializer here
        managers = create_all_managers(session)

        game = create_test_game(
            session, name="Hierarchy Test Game", description="Full test game."
        )
        act1 = create_test_act(
            session, game_id=game.id, title="The First Act", sequence=1
        )
        act2 = create_test_act(
            session,
            game_id=game.id,
            title="The Second Act",
            sequence=2,
            is_active=False,  # Ensure this act isn't set active during creation for test variety.
        )
        scene1_1 = create_test_scene(session, act_id=act1.id, title="Opening Scene")
        scene1_2 = create_test_scene(
            session,  # <-- Added session argument
            act_id=act1.id,
            title="Completed Scene",
        )
        scene2_1 = create_test_scene(session, act_id=act2.id, title="Another Scene")
        event1 = create_test_event(
            session, scene_id=scene1_1.id, description="First event happens."
        )
        event2 = create_test_event(
            session,
            scene_id=scene1_2.id,
            description="Second event (oracle).",
            source="oracle",
        )
        event3 = create_test_event(
            session,
            scene_id=scene2_1.id,
            description="Third event (dice).",
            source="dice",
        )

        # Store object lists for easier assertion checks below.
        acts = [act1, act2]
        scenes = [scene1_1, scene1_2, scene2_1]
        events = [event1, event2, event3]

        result_str = generate_game_markdown(
            game, managers.scene, managers.event, include_metadata=False
        )

    assert f"# {game.name}" in result_str
    assert game.description in result_str

    for act in acts:
        assert f"## Act {act.sequence}: {act.title}" in result_str

    for scene in scenes:
        scene_title = f"### Scene {scene.sequence}: {scene.title}"
        assert scene_title in result_str

    for event in events:
        first_line_desc = event.description.split("\n")[0]
        assert first_line_desc in result_str
        # Check source indicators are present for relevant events.
        if event.source == "oracle":
            assert f"🔮: {first_line_desc}" in result_str
        elif event.source == "dice":
            assert f"🎲: {first_line_desc}" in result_str

    with session_context as session:
        managers = create_all_managers(session)
        # Re-fetch game to ensure it's attached to the current session if needed.
        game = session.get(type(game), game.id)
        result_str_meta = generate_game_markdown(
            game, managers.scene, managers.event, include_metadata=True
        )

    assert f"*Game ID: {game.id}*" in result_str_meta

    for act in acts:
        assert f"*Act ID: {act.id}*" in result_str_meta

    for scene in scenes:
        assert f"*Scene ID: {scene.id}*" in result_str_meta

    assert "Source: manual" in result_str_meta
    assert "Source: oracle" in result_str_meta
    assert "Source: dice" in result_str_meta


# Test uses session_context and factory fixtures for realistic data.
def test_generate_game_markdown_empty(session_context, create_test_game):
    """Test generating markdown for a game with no acts."""
    with session_context as session:
        managers = create_all_managers(session)
        empty_game = create_test_game(
            session, name="Empty Game", description="Game with no acts"
        )

        result = generate_game_markdown(
            empty_game, managers.scene, managers.event, include_metadata=False
        )

    assert "# Empty Game" in result
    assert "Game with no acts" in result
    assert "## Act" not in result  # Ensure no act headers are present.


def test_generate_concepts_header():
    """Test generating the concepts header."""
    header = generate_concepts_header()

    assert isinstance(header, list)
    assert all(isinstance(line, str) for line in header)

    assert "# Game Structure Guide" in header
    assert any("## Game" in line for line in header)
    assert any("## Acts" in line for line in header)
    assert any("## Scenes" in line for line in header)
    assert any("## Events" in line for line in header)

    assert any("🔮 Oracle interpretations" in line for line in header)
    assert any("🎲 Dice rolls" in line for line in header)


# Test uses session_context and factory fixtures for realistic data.
def test_game_markdown_with_concepts(session_context, create_test_game):
    """Test generating markdown for a game with concepts header."""
    with session_context as session:
        managers = create_all_managers(session)
        game = create_test_game(
            session, name="Test Game", description="Game with concepts header"
        )

        result = generate_game_markdown(
            game,
            managers.scene,
            managers.event,
            include_metadata=False,
            include_concepts=True,
        )

    assert "# Game Structure Guide" in result
    assert "## Game" in result
    assert "## Acts" in result
    assert "## Scenes" in result
    assert "## Events" in result

    assert "# Test Game" in result
    assert "Game with concepts header" in result
