"""
Unit tests for the MarkdownRenderer class.
"""

import logging
from datetime import UTC, datetime  # Import datetime and UTC for DiceRoll creation
from typing import Callable  # Import Callable for factory types
from unittest.mock import MagicMock

import pytest
from rich.console import Console
from sqlalchemy.orm import Session  # Import Session for type hinting

# Import the renderer and models needed for tests
from sologm.cli.rendering.markdown_renderer import MarkdownRenderer
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

# Set up logging for tests
logger = logging.getLogger(__name__)


# Fixture for mock console (can be shared or defined here)
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width if needed for truncation tests later
    console.width = 100
    return console


# --- Test for display_dice_roll ---


def test_display_dice_roll_markdown(mock_console: MagicMock):
    """Test displaying a dice roll as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Create DiceRoll object directly within the test
    test_dice_roll = DiceRoll(
        id="dice-roll-test",
        notation="2d6+1",
        individual_results=[4, 3],
        modifier=1,
        total=8,
        reason="Test Roll",
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
        # scene_id=None # Optional, not needed for this display method
    )

    renderer.display_dice_roll(test_dice_roll)

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert key components
    assert "### Dice Roll: 2d6+1" in rendered_output
    assert "(Reason: Test Roll)" in rendered_output
    assert "*   **Result:** `8`" in rendered_output
    assert "*   Rolls: `[4, 3]`" in rendered_output
    assert "*   Modifier: `+1`" in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_interpretation ---


def test_display_interpretation_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying a single interpretation as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        interp = create_test_interpretation(
            session,
            set_id=interp_set.id,
            title="Test Interp Title",
            description="Test Interp Desc.",
        )

        # Test case 1: Basic interpretation
        mock_console.reset_mock()
        renderer.display_interpretation(interp)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_basic = call_args[0]
        assert f"#### {interp.title}" in rendered_output_basic
        assert interp.description in rendered_output_basic
        assert f"*ID: {interp.id} / {interp.slug}*" in rendered_output_basic
        assert "Interpretation #" not in rendered_output_basic
        assert "(**Selected**)" not in rendered_output_basic
        assert call_kwargs == {"highlight": False, "markup": False}

        # Test case 2: Selected interpretation with sequence
        mock_console.reset_mock()
        renderer.display_interpretation(interp, selected=True, sequence=1)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_selected = call_args[0]
        assert f"#### Interpretation #1: {interp.title}" in rendered_output_selected
        assert "(**Selected**)" in rendered_output_selected
        assert interp.description in rendered_output_selected
        assert f"*ID: {interp.id} / {interp.slug}*" in rendered_output_selected
        assert call_kwargs == {"highlight": False, "markup": False}

        # Test case 3: Interpretation with sequence but not selected
        mock_console.reset_mock()
        renderer.display_interpretation(interp, selected=False, sequence=2)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_sequence = call_args[0]
        assert f"#### Interpretation #2: {interp.title}" in rendered_output_sequence
        assert "(**Selected**)" not in rendered_output_sequence
        assert interp.description in rendered_output_sequence
        assert f"*ID: {interp.id} / {interp.slug}*" in rendered_output_sequence
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_events_table ---


def test_display_events_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # Add the fixture here
):
    """Test displaying a list of events as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        # Call the initializer function with the session *first*
        initialize_event_sources(session)

        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id, title="Event Scene")

        # Now this should work because 'manual' exists
        event1 = create_test_event(
            session, scene_id=scene.id, description="First test event", source="manual"
        )
        event2 = create_test_event(
            session, scene_id=scene.id, description="Second test event", source="oracle"
        )
        test_events = [event1, event2]

        # Test with events
        mock_console.reset_mock()
        renderer.display_events_table(test_events, scene)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        assert f"### Events in Scene: {scene.title}" in rendered_output
        assert "| ID | Time | Source | Description |" in rendered_output
        assert "|---|---|---|---|" in rendered_output
        # Check event 1 details
        assert f"| `{event1.id}`" in rendered_output
        assert f"| {event1.created_at.strftime('%Y-%m-%d %H:%M')}" in rendered_output
        assert f"| {event1.source_name}" in rendered_output
        assert f"| {event1.description} |" in rendered_output
        # Check event 2 details
        assert f"| `{event2.id}`" in rendered_output
        assert f"| {event2.created_at.strftime('%Y-%m-%d %H:%M')}" in rendered_output
        assert f"| {event2.source_name}" in rendered_output
        assert f"| {event2.description} |" in rendered_output
        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}

        # Test with pipe character escaping
        mock_console.reset_mock()
        event_with_pipe = create_test_event(
            session,
            scene_id=scene.id,
            description="Event | with pipe",
            source="manual",
        )
        renderer.display_events_table([event_with_pipe], scene)

        # Capture the output
        call_args_pipe, call_kwargs_pipe = mock_console.print.call_args
        rendered_output_pipe = call_args_pipe[0]

        # Assert key components including escaped pipe
        assert f"### Events in Scene: {scene.title}" in rendered_output_pipe
        assert "| ID | Time | Source | Description |" in rendered_output_pipe
        assert f"| `{event_with_pipe.id}`" in rendered_output_pipe
        assert f"| {event_with_pipe.source_name}" in rendered_output_pipe
        assert "| Event \\| with pipe |" in rendered_output_pipe  # Check escaped pipe
        assert call_kwargs_pipe == {"highlight": False, "markup": False}


def test_display_events_table_no_events_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying an empty list of events as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id, title="Empty Scene")
        renderer.display_events_table([], scene)
        expected_output = f"\nNo events in scene '{scene.title}'"
        mock_console.print.assert_called_with(
            expected_output, highlight=False, markup=False
        )


# --- Test for display_games_table ---


def test_display_games_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
):
    """Test displaying a list of games as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        test_game = create_test_game(
            session, name="Active Game", description="The main game", is_active=True
        )
        other_game = create_test_game(
            session, name="Other Game", description="Another game.", is_active=False
        )
        # The factories don't create acts/scenes by default, so counts will be 0
        # If counts were needed, we'd use create_test_act/scene here.
        # test_game.acts = [] # Not needed, calculated property
        # test_game.scenes = [] # Not needed, calculated property
        # other_game.acts = [] # Not needed
        # other_game.scenes = [] # Not needed

        games = [test_game, other_game]

        # Test case 1: With an active game
        mock_console.reset_mock()
        renderer.display_games_table(games, active_game=test_game)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_active = call_args[0]

        assert "### Games" in rendered_output_active
        assert (
            "| ID | Name | Description | Acts | Scenes | Current |"
            in rendered_output_active
        )
        # Check active game row
        assert f"| `{test_game.id}`" in rendered_output_active
        assert f"| **{test_game.name}**" in rendered_output_active  # Bold
        assert f"| {test_game.description}" in rendered_output_active
        assert "| 0 | 0 | ✓ |" in rendered_output_active  # Counts and marker
        # Check other game row
        assert f"| `{other_game.id}`" in rendered_output_active
        assert f"| {other_game.name}" in rendered_output_active  # Not bold
        assert f"| {other_game.description}" in rendered_output_active
        assert "| 0 | 0 |  |" in rendered_output_active  # Counts and marker
        assert call_kwargs == {"highlight": False, "markup": False}

    # Test case 2: Without an active game
    mock_console.reset_mock()
    renderer.display_games_table(games, active_game=None)
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output_no_active = call_args[0]

    assert "### Games" in rendered_output_no_active
    assert (
        "| ID | Name | Description | Acts | Scenes | Current |"
        in rendered_output_no_active
    )
    # Check first game row (not active)
    assert f"| `{test_game.id}`" in rendered_output_no_active
    assert f"| {test_game.name}" in rendered_output_no_active  # Not bold
    assert f"| {test_game.description}" in rendered_output_no_active
    assert "| 0 | 0 |  |" in rendered_output_no_active  # Counts and marker
    # Check second game row (not active)
    assert f"| `{other_game.id}`" in rendered_output_no_active
    assert f"| {other_game.name}" in rendered_output_no_active  # Not bold
    assert f"| {other_game.description}" in rendered_output_no_active
    assert "| 0 | 0 |  |" in rendered_output_no_active  # Counts and marker
    assert call_kwargs == {"highlight": False, "markup": False}


def test_display_games_table_no_games_markdown(mock_console: MagicMock):
    """Test displaying an empty list of games as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_games_table([], active_game=None)
    expected_output = "No games found. Create one with 'sologm game create'."
    mock_console.print.assert_called_with(
        expected_output, highlight=False, markup=False
    )


# --- Test for display_scenes_table ---


def test_display_scenes_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying a list of scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        test_scene = create_test_scene(
            session,
            act_id=act.id,
            title="Active Scene",
            description="The current scene.",
            is_active=True,
            # Removed status
        )
        other_scene = create_test_scene(
            session,
            act_id=act.id,
            title="Other Scene",
            description="Another scene.",
            is_active=False,
            # Removed status
        )
        # Ensure sequences are different if needed by display logic (factory handles this)
        scenes = sorted(
            [test_scene, other_scene], key=lambda s: s.sequence
        )  # Sort by sequence for predictable table order

        # Test case 1: With an active scene ID
        mock_console.reset_mock()
        renderer.display_scenes_table(scenes, active_scene_id=test_scene.id)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_active = call_args[0]

        assert "### Scenes" in rendered_output_active
        # Updated header assertion
        assert (
            "| ID | Title | Description | Current | Sequence |"
            in rendered_output_active
        )
        # Check active scene row
        assert f"| `{test_scene.id}`" in rendered_output_active
        assert f"| **{test_scene.title}**" in rendered_output_active  # Bold
        assert f"| {test_scene.description}" in rendered_output_active
        # Removed status assertion
        # Updated row assertion
        assert f"| ✓ | {test_scene.sequence} |" in rendered_output_active
        # Check other scene row
        assert f"| `{other_scene.id}`" in rendered_output_active
        assert f"| {other_scene.title}" in rendered_output_active  # Not bold
        assert f"| {other_scene.description}" in rendered_output_active
        # Removed status assertion
        # Updated row assertion
        assert f"|  | {other_scene.sequence} |" in rendered_output_active
        assert call_kwargs == {"highlight": False, "markup": False}

    # Test case 2: Without an active scene ID
    mock_console.reset_mock()
    renderer.display_scenes_table(scenes, active_scene_id=None)
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output_no_active = call_args[0]

    assert "### Scenes" in rendered_output_no_active
    # Updated header assertion
    assert (
        "| ID | Title | Description | Current | Sequence |" in rendered_output_no_active
    )
    # Check first scene row (not active)
    assert f"| `{test_scene.id}`" in rendered_output_no_active
    assert f"| {test_scene.title}" in rendered_output_no_active  # Not bold
    assert f"| {test_scene.description}" in rendered_output_no_active
    # Removed status assertion
    # Updated row assertion
    assert f"|  | {test_scene.sequence} |" in rendered_output_no_active
    # Check second scene row (not active)
    assert f"| `{other_scene.id}`" in rendered_output_no_active
    assert f"| {other_scene.title}" in rendered_output_no_active  # Not bold
    assert f"| {other_scene.description}" in rendered_output_no_active
    # Removed status assertion
    # Updated row assertion
    assert f"|  | {other_scene.sequence} |" in rendered_output_no_active
    assert call_kwargs == {"highlight": False, "markup": False}


def test_display_scenes_table_no_scenes_markdown(mock_console: MagicMock):
    """Test displaying an empty list of scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_scenes_table([], active_scene_id=None)
    expected_output = "No scenes found. Create one with 'sologm scene create'."
    mock_console.print.assert_called_with(
        expected_output, highlight=False, markup=False
    )


# --- Test for display_game_info ---


def test_display_game_info_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying game info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        test_game = create_test_game(session)
        test_act = create_test_act(session, game_id=test_game.id)
        test_scene = create_test_scene(session, act_id=test_act.id, is_active=True)

        # Refresh game to ensure relationships are loaded for calculated properties
        session.refresh(test_game, attribute_names=["acts"])
        session.refresh(test_act, attribute_names=["scenes"])

        # Test case 1: With active scene
        mock_console.reset_mock()
        renderer.display_game_info(test_game, active_scene=test_scene)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_active = call_args[0]

        assert (
            f"## {test_game.name} (`{test_game.slug}` / `{test_game.id}`)"
            in rendered_output_active
        )
        assert test_game.description in rendered_output_active
        assert (
            f"*   **Created:** {test_game.created_at.strftime('%Y-%m-%d')}"
            in rendered_output_active
        )
        assert (
            f"*   **Modified:** {test_game.modified_at.strftime('%Y-%m-%d')}"
            in rendered_output_active
        )
        assert f"*   **Acts:** {len(test_game.acts)}" in rendered_output_active
        assert (
            f"*   **Scenes:** {sum(len(a.scenes) for a in test_game.acts)}"
            in rendered_output_active
        )
        assert f"*   **Active Scene:** {test_scene.title}" in rendered_output_active
        assert call_kwargs == {"highlight": False, "markup": False}

        # Test case 2: Without active scene
        mock_console.reset_mock()
        renderer.display_game_info(test_game, active_scene=None)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_no_active = call_args[0]

        assert (
            f"## {test_game.name} (`{test_game.slug}` / `{test_game.id}`)"
            in rendered_output_no_active
        )
        assert test_game.description in rendered_output_no_active
        assert (
            f"*   **Created:** {test_game.created_at.strftime('%Y-%m-%d')}"
            in rendered_output_no_active
        )
        assert (
            f"*   **Modified:** {test_game.modified_at.strftime('%Y-%m-%d')}"
            in rendered_output_no_active
        )
        assert f"*   **Acts:** {len(test_game.acts)}" in rendered_output_no_active
        assert (
            f"*   **Scenes:** {sum(len(a.scenes) for a in test_game.acts)}"
            in rendered_output_no_active
        )
        assert (
            "*   **Active Scene:**" not in rendered_output_no_active
        )  # Ensure line is absent
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_interpretation_set ---


def test_display_interpretation_set_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Tests the Markdown rendering of an InterpretationSet."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        test_interpretation_set = create_test_interpretation_set(
            session,
            scene_id=scene.id,
            context="Test Context",
            oracle_results="Test Results",
        )
        interp1 = create_test_interpretation(
            session, set_id=test_interpretation_set.id, title="Interp 1"
        )
        interp2 = create_test_interpretation(
            session, set_id=test_interpretation_set.id, title="Interp 2"
        )
        test_interpretations = [interp1, interp2]

        # Refresh the set to load interpretations relationship
        session.refresh(test_interpretation_set, attribute_names=["interpretations"])
        num_interpretations = len(test_interpretations)

        # --- Test case 1: Show context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(test_interpretation_set, show_context=True)

        # Expected calls: context(1) + N interpretations + N blank lines + instruction(1) = 2*N + 2
        expected_call_count_true = num_interpretations * 2 + 2
        assert mock_console.print.call_count == expected_call_count_true

        # Check context call (first call)
        context_call_args, context_call_kwargs = mock_console.print.call_args_list[0]
        rendered_context = context_call_args[0]
        assert "### Oracle Interpretations" in rendered_context
        assert f"**Context:** {test_interpretation_set.context}" in rendered_context
        assert (
            f"**Results:** {test_interpretation_set.oracle_results}" in rendered_context
        )
        assert "---" in rendered_context
        assert context_call_kwargs == {"highlight": False, "markup": False}

        # Check instruction call (last call)
        instruction_call_args, instruction_call_kwargs = (
            mock_console.print.call_args_list[-1]
        )
        rendered_instruction = instruction_call_args[0]
        assert (
            f"Interpretation Set ID: `{test_interpretation_set.id}`"
            in rendered_instruction
        )
        assert "(Use 'sologm oracle select' to choose)" in rendered_instruction
        assert instruction_call_kwargs == {"highlight": False, "markup": False}

        # We don't assert the exact interpretation calls here, as that's tested elsewhere

        # --- Test case 2: Hide context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(test_interpretation_set, show_context=False)

        # Expected calls: N interpretations + N blank lines + instruction(1) = 2*N + 1
        expected_call_count_false = num_interpretations * 2 + 1
        assert mock_console.print.call_count == expected_call_count_false

        # Ensure context header was NOT printed by checking the first call's content
        first_call_args, first_call_kwargs = mock_console.print.call_args_list[0]
        rendered_first_call = first_call_args[0]
        assert "### Oracle Interpretations" not in rendered_first_call
        assert (
            f"**Context:** {test_interpretation_set.context}" not in rendered_first_call
        )
        # The first call should now be the first interpretation
        assert f"#### Interpretation #1: {interp1.title}" in rendered_first_call

        # Check instruction print call again (last call)
        instruction_call_args_hide, instruction_call_kwargs_hide = (
            mock_console.print.call_args_list[-1]
        )
        rendered_instruction_hide = instruction_call_args_hide[0]
        assert (
            f"Interpretation Set ID: `{test_interpretation_set.id}`"
            in rendered_instruction_hide
        )
        assert "(Use 'sologm oracle select' to choose)" in rendered_instruction_hide
        assert instruction_call_kwargs_hide == {"highlight": False, "markup": False}


def test_display_scene_info_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying scene info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id, sequence=1, title="Test Act")
        test_scene = create_test_scene(
            session,
            act_id=act.id,
            title="Detailed Scene",
            description="Scene Description.",
            # Removed status
        )
        # Ensure relationships are loaded before display
        session.flush()

        renderer.display_scene_info(test_scene)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        act_title = test_scene.act.title or "Untitled Act"
        act_info = f"Act {test_scene.act.sequence}: {act_title}"

        # Updated header assertion (no status indicator)
        assert (
            f"### Scene {test_scene.sequence}: {test_scene.title} (`{test_scene.id}`)"
            in rendered_output
        )
        assert test_scene.description in rendered_output
        # Removed status assertion
        assert f"*   **Act:** {act_info}" in rendered_output
        if test_scene.created_at:
            assert (
                f"*   **Created:** {test_scene.created_at.strftime('%Y-%m-%d')}"
                in rendered_output
            )
        if test_scene.modified_at:
            assert (
                f"*   **Modified:** {test_scene.modified_at.strftime('%Y-%m-%d')}"
                in rendered_output
            )

        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_acts_table ---


def test_display_acts_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying a list of acts as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        test_act = create_test_act(
            session,
            game_id=game.id,
            title="Active Act",
            summary="The current act.",
            is_active=True,
        )
        other_act = create_test_act(
            session,
            game_id=game.id,
            title="Other Act",
            summary="Another act.",
            is_active=False,
        )
        acts = sorted([test_act, other_act], key=lambda a: a.sequence)

        # Test case 1: With an active act ID
        mock_console.reset_mock()
        renderer.display_acts_table(acts, active_act_id=test_act.id)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_active = call_args[0]

        assert "### Acts" in rendered_output_active
        assert "| ID | Seq | Title | Summary | Current |" in rendered_output_active
        # Check active act row
        assert f"| `{test_act.id}`" in rendered_output_active
        assert f"| {test_act.sequence}" in rendered_output_active
        assert f"| **{test_act.title}**" in rendered_output_active  # Bold
        assert f"| {test_act.summary}" in rendered_output_active
        assert "| ✓ |" in rendered_output_active  # Marker
        # Check other act row
        assert f"| `{other_act.id}`" in rendered_output_active
        assert f"| {other_act.sequence}" in rendered_output_active
        assert f"| {other_act.title}" in rendered_output_active  # Not bold
        assert f"| {other_act.summary}" in rendered_output_active
        assert "|  |" in rendered_output_active  # Marker (check spacing carefully)
        assert call_kwargs == {"highlight": False, "markup": False}

        # Test case 2: Without an active act ID
        mock_console.reset_mock()
        renderer.display_acts_table(acts, active_act_id=None)
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output_no_active = call_args[0]

        assert "### Acts" in rendered_output_no_active
        assert "| ID | Seq | Title | Summary | Current |" in rendered_output_no_active
        # Check first act row (not active)
        assert f"| `{test_act.id}`" in rendered_output_no_active
        assert f"| {test_act.sequence}" in rendered_output_no_active
        assert f"| {test_act.title}" in rendered_output_no_active  # Not bold
        assert f"| {test_act.summary}" in rendered_output_no_active
        assert "|  |" in rendered_output_no_active  # Marker
        # Check second act row (not active)
        assert f"| `{other_act.id}`" in rendered_output_no_active
        assert f"| {other_act.sequence}" in rendered_output_no_active
        assert f"| {other_act.title}" in rendered_output_no_active  # Not bold
        assert f"| {other_act.summary}" in rendered_output_no_active
        assert "|  |" in rendered_output_no_active  # Marker
        assert call_kwargs == {"highlight": False, "markup": False}


def test_display_acts_table_no_acts_markdown(mock_console: MagicMock):
    """Test displaying an empty list of acts as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_acts_table([], active_act_id=None)
    expected_output = "No acts found. Create one with 'sologm act create'."
    mock_console.print.assert_called_with(
        expected_output, highlight=False, markup=False
    )


# --- Test for display_act_info ---


def test_display_act_info_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying act info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        test_game = create_test_game(session, name="Act Info Game")
        test_act = create_test_act(
            session, game_id=test_game.id, title="Act With Scene", sequence=1
        )
        test_scene = create_test_scene(
            session, act_id=test_act.id, title="Scene in Act", is_active=True
        )

        # Refresh act to load scenes relationship
        session.refresh(test_act, attribute_names=["scenes"])
        # Refresh scene to load act relationship (needed by display_scenes_table)
        session.refresh(test_scene, attribute_names=["act"])

        renderer.display_act_info(test_act, test_game.name)

        # Check that the correct parts were printed in order
        calls = mock_console.print.call_args_list
        # Expected calls: Act Info, Blank Line, Scenes Table
        assert len(calls) >= 3

        # Check Act Info call (first call)
        act_info_args, act_info_kwargs = calls[0]
        rendered_act_info = act_info_args[0]
        assert (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)"
            in rendered_act_info
        )
        assert test_act.summary in rendered_act_info
        assert f"*   **Game:** {test_game.name}" in rendered_act_info
        assert (
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}"
            in rendered_act_info
        )
        assert (
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
            in rendered_act_info
        )
        assert act_info_kwargs == {"highlight": False, "markup": False}

        # Check Blank Line call (second call)
        blank_line_args, blank_line_kwargs = calls[1]
        assert blank_line_args[0] == ""
        assert blank_line_kwargs == {"highlight": False, "markup": False}

        # Check Scenes Table call (third call)
        # We rely on test_display_scenes_table_markdown to verify the *content*
        # Here, just check that *a* table-like structure was printed.
        scenes_table_args, scenes_table_kwargs = calls[2]
        rendered_scenes_table = scenes_table_args[0]
        assert "### Scenes" in rendered_scenes_table
        # Updated header check
        assert (
            "| ID | Title | Description | Current | Sequence |" in rendered_scenes_table
        )
        assert (
            f"`{test_scene.id}`" in rendered_scenes_table
        )  # Check scene ID is present
        assert scenes_table_kwargs == {"highlight": False, "markup": False}


def test_display_act_info_no_scenes_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying act info with no scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        test_game = create_test_game(session, name="No Scene Game")
        test_act = create_test_act(
            session, game_id=test_game.id, title="Act Without Scene", sequence=1
        )
        # Ensure no scenes are associated (factory default)
        session.refresh(test_act, attribute_names=["scenes"])  # Should be empty

        renderer.display_act_info(test_act, test_game.name)

        # Check the sequence of calls
        calls = mock_console.print.call_args_list
        # Expected calls: Act Info, Blank Line, Header, Blank Line, Message
        assert len(calls) == 5

        expected_kwargs = {"highlight": False, "markup": False}

        # Check Act Info call (first call)
        act_info_args, act_info_kwargs = calls[0]
        rendered_act_info = act_info_args[0]
        assert (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)"
            in rendered_act_info
        )
        assert test_act.summary in rendered_act_info
        assert f"*   **Game:** {test_game.name}" in rendered_act_info
        assert (
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}"
            in rendered_act_info
        )
        assert (
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
            in rendered_act_info
        )
        assert act_info_kwargs == expected_kwargs

        # Check Blank Line call (second call)
        assert calls[1].args[0] == ""
        assert calls[1].kwargs == expected_kwargs

        # Check "No Scenes" Header call (third call)
        assert calls[2].args[0] == f"### Scenes in Act {test_act.sequence}"
        assert calls[2].kwargs == expected_kwargs

        # Check Blank Line call (fourth call)
        assert calls[3].args[0] == ""
        assert calls[3].kwargs == expected_kwargs

        # Check "No Scenes" Message call (fifth call)
        assert calls[4].args[0] == "No scenes in this act yet."
        assert calls[4].kwargs == expected_kwargs


# --- Test for display_interpretation_sets_table ---


def test_display_interpretation_sets_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying interpretation sets table as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        test_scene = create_test_scene(session, act_id=act.id, title="Interp Scene")
        test_interpretation_set = create_test_interpretation_set(
            session,
            scene_id=test_scene.id,
            context="This is the context for the interpretation set table test.",
            oracle_results="These are the oracle results.",
        )
        interp1 = create_test_interpretation(
            session, set_id=test_interpretation_set.id, is_selected=True
        )  # Mark one as selected
        interp2 = create_test_interpretation(
            session, set_id=test_interpretation_set.id, is_selected=False
        )
        test_interpretations = [interp1, interp2]

        # Refresh relationships needed for display
        session.refresh(
            test_interpretation_set, attribute_names=["interpretations", "scene"]
        )

        interp_sets = [test_interpretation_set]

        renderer.display_interpretation_sets_table(interp_sets)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        assert "### Oracle Interpretation Sets" in rendered_output
        assert (
            "| ID | Scene | Context | Oracle Results | Created | Status | Count |"
            in rendered_output
        )
        assert "|---|---|---|---|---|---|---|" in rendered_output

        # Check row details (handle escaped pipes in original data)
        full_context = test_interpretation_set.context  # Renderer handles escaping
        full_results = (
            test_interpretation_set.oracle_results
        )  # Renderer handles escaping
        status = (
            "Resolved"
            if any(i.is_selected for i in test_interpretations)
            else "Pending"
        )
        assert f"| `{test_interpretation_set.id}`" in rendered_output
        assert f"| {test_scene.title}" in rendered_output
        # Check for escaped content if pipes were present
        assert f"| {full_context.replace('|', '\\|')}" in rendered_output
        assert f"| {full_results.replace('|', '\\|')}" in rendered_output
        assert (
            f"| {test_interpretation_set.created_at.strftime('%Y-%m-%d %H:%M')}"
            in rendered_output
        )
        assert f"| {status}" in rendered_output
        assert f"| {len(test_interpretations)} |" in rendered_output

        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_interpretation_status ---


def test_display_interpretation_status_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying interpretation status as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        test_interpretation_set = create_test_interpretation_set(
            session,
            scene_id=scene.id,
            context="Status Context",
            oracle_results="Status Results",
            retry_attempt=1,
        )
        interp1 = create_test_interpretation(
            session, set_id=test_interpretation_set.id, is_selected=True
        )
        # Refresh set to load interpretations
        session.refresh(test_interpretation_set, attribute_names=["interpretations"])

        renderer.display_interpretation_status(test_interpretation_set)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        is_resolved = any(
            i.is_selected for i in test_interpretation_set.interpretations
        )
        assert "### Current Oracle Interpretation Status" in rendered_output
        assert f"**Context:** {test_interpretation_set.context}" in rendered_output
        assert (
            f"**Results:** {test_interpretation_set.oracle_results}" in rendered_output
        )
        assert f"*   **Set ID:** `{test_interpretation_set.id}`" in rendered_output
        assert (
            f"*   **Retry Count:** {test_interpretation_set.retry_attempt}"
            in rendered_output
        )
        assert f"*   **Resolved:** {is_resolved}" in rendered_output

        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_act_ai_generation_results ---


def test_display_act_ai_generation_results_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying AI generation results for an act as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    results = {"title": "AI Title", "summary": "AI Summary"}

    with session_context as session:
        game = create_test_game(session)
        test_act = create_test_act(
            session,
            game_id=game.id,
            title="Existing Title",
            summary="Existing Summary",
        )

        renderer.display_act_ai_generation_results(results, test_act)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        assert "### AI Generation Results" in rendered_output
        assert "**AI-Generated Title:**" in rendered_output
        assert "> AI Title" in rendered_output
        assert "**Current Title:**" in rendered_output
        assert f"> {test_act.title}" in rendered_output
        assert "---" in rendered_output
        assert "**AI-Generated Summary:**" in rendered_output
        assert "> AI Summary" in rendered_output
        assert "**Current Summary:**" in rendered_output
        assert f"> {test_act.summary}" in rendered_output

        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_act_completion_success ---


def test_display_act_completion_success_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying act completion success as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        test_act = create_test_act(
            session,
            game_id=game.id,
            title="Completed Act",
            summary="This act is done.",
            sequence=2,
        )
        # Simulate completion if needed (though display only reads properties)
        # test_act.is_active = False # Example if status changed

        renderer.display_act_completion_success(test_act)

        # Capture the output
        call_args, call_kwargs = mock_console.print.call_args
        rendered_output = call_args[0]

        # Assert key components
        assert f"## Act '{test_act.title}' Completed Successfully!" in rendered_output
        assert f"*   **ID:** `{test_act.id}`" in rendered_output
        assert f"*   **Sequence:** Act {test_act.sequence}" in rendered_output
        assert "*   **Status:** Completed" in rendered_output
        assert "**Final Title:**" in rendered_output
        assert f"> {test_act.title}" in rendered_output
        assert "**Final Summary:**" in rendered_output
        assert f"> {test_act.summary}" in rendered_output

        # Assert the markdown flags
        assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_act_ai_feedback_prompt ---


def test_display_act_ai_feedback_prompt_markdown(mock_console: MagicMock):
    """Test displaying AI feedback prompt instructions as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    # The console argument is required by the base class but not used here
    renderer.display_act_ai_feedback_prompt(mock_console)

    expected_output = (
        "\n---\n"
        "**Next Step:**\n"
        "Review the generated content above.\n"
        "*   To **accept** it, run: `sologm act accept`\n"
        "*   To **edit** it, run: `sologm act edit`\n"
        "*   To **regenerate** it, run: `sologm act generate --retry`\n"
        "---"
    )
    mock_console.print.assert_called_once_with(
        expected_output, highlight=False, markup=False
    )


# --- Test for display_act_edited_content_preview ---


def test_display_act_edited_content_preview_markdown(mock_console: MagicMock):
    """Test displaying edited content preview as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}

    renderer.display_act_edited_content_preview(edited_results)

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert key components
    assert "### Preview of Edited Content:" in rendered_output
    assert "**Edited Title:**" in rendered_output
    assert "> Edited Title" in rendered_output
    assert "**Edited Summary:**" in rendered_output
    assert "> Edited Summary" in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_error ---


def test_display_error_markdown(mock_console: MagicMock):
    """Test displaying an error message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    error_message = "Something went wrong!"
    renderer.display_error(error_message)

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert key components
    assert "> **Error:**" in rendered_output
    assert error_message in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_success ---


def test_display_success_markdown(mock_console: MagicMock):
    """Test displaying a success message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    success_message = "Operation successful!"
    renderer.display_success(success_message)

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert key components
    assert "**Success:**" in rendered_output
    assert success_message in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_warning ---


def test_display_warning_markdown(mock_console: MagicMock):
    """Test displaying a warning message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    warning_message = "Something might be wrong."
    renderer.display_warning(warning_message)

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert key components
    assert "**Warning:**" in rendered_output
    assert warning_message in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}


# --- Test for display_message ---


def test_display_message_markdown(mock_console: MagicMock):
    """Test displaying a simple message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    info_message = "Just some information."
    renderer.display_message(info_message)  # Style is ignored

    # Capture the output
    call_args, call_kwargs = mock_console.print.call_args
    rendered_output = call_args[0]

    # Assert the message is present (no specific prefix expected)
    assert info_message in rendered_output

    # Assert the markdown flags
    assert call_kwargs == {"highlight": False, "markup": False}
