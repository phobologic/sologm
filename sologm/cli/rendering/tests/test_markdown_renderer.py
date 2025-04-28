"""
Unit tests for the MarkdownRenderer class.
"""

import logging
from datetime import datetime  # Import datetime for DiceRoll creation
from typing import Callable, List  # Import Callable for factory types
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
from sologm.models.scene import Scene, SceneStatus

# Import factory fixtures types if needed for hinting (Optional but good practice)
# from sologm.tests.conftest import ( # Example if you need explicit types
#     create_test_game,
#     create_test_act,
#     # ... other factories
# )

# Import truncate_text utility
from sologm.cli.utils.display import truncate_text

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
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        # scene_id=None # Optional, not needed for this display method
    )

    renderer.display_dice_roll(test_dice_roll)

    # Define the expected Markdown output
    expected_output = (
        "### Dice Roll: 2d6+1 (Reason: Test Roll)\n\n"
        "*   **Result:** `8`\n"
        "*   Rolls: `[4, 3]`\n"
        "*   Modifier: `+1`"
    )

    # Assert that console.print was called with the expected string
    # Using assert_called_once_with checks for exact match including newlines
    mock_console.print.assert_called_once_with(expected_output)


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
        renderer.display_interpretation(interp)
        expected_output_basic = (
            f"#### {interp.title}\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_basic)
    mock_console.reset_mock()

    # Test case 2: Selected interpretation with sequence
    renderer.display_interpretation(interp, selected=True, sequence=1)
    expected_output_selected = (
        f"#### Interpretation #1: {interp.title} (**Selected**)\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_selected)
    mock_console.reset_mock()

    # Test case 3: Interpretation with sequence but not selected
    renderer.display_interpretation(interp, selected=False, sequence=2)
    expected_output_sequence = (
        f"#### Interpretation #2: {interp.title}\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_sequence)


# --- Test for display_events_table ---


def test_display_events_table_markdown(
    mock_console: MagicMock,
    session_context: Callable[[], Session],
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
):
    """Test displaying a list of events as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id, title="Event Scene")
        event1 = create_test_event(
            session, scene_id=scene.id, description="First test event", source="manual"
        )
        event2 = create_test_event(
            session, scene_id=scene.id, description="Second test event", source="oracle"
        )
        test_events = [event1, event2]

        # Test with events and default truncation
        renderer.display_events_table(test_events, scene)

        # Expected output (adjust based on test_events fixture data)
        expected_output = (
            f"### Events in Scene: {scene.title}\n\n"
            f"| ID | Time | Source | Description |\n"
            f"|---|---|---|---|\n"
            f"| `{event1.id}` | {event1.created_at.strftime('%Y-%m-%d %H:%M')} | {event1.source_name} | {event1.description} |\n"
            f"| `{event2.id}` | {event2.created_at.strftime('%Y-%m-%d %H:%M')} | {event2.source_name} | {event2.description} |"
        )
        mock_console.print.assert_called_with(expected_output)
        mock_console.reset_mock()

        # Test with truncation enabled explicitly
        short_len = 10
        renderer.display_events_table(
            test_events, scene, max_description_length=short_len
        )
        truncated_desc1 = truncate_text(event1.description, short_len)
        truncated_desc2 = truncate_text(event2.description, short_len)
        expected_output_truncated = (
            f"### Events in Scene: {scene.title}\n\n"
            f"| ID | Time | Source | Description |\n"
            f"|---|---|---|---|\n"
            f"| `{event1.id}` | {event1.created_at.strftime('%Y-%m-%d %H:%M')} | {event1.source_name} | {truncated_desc1} |\n"
            f"| `{event2.id}` | {event2.created_at.strftime('%Y-%m-%d %H:%M')} | {event2.source_name} | {truncated_desc2} |"
        )
        mock_console.print.assert_called_with(expected_output_truncated)
        mock_console.reset_mock()

        # Test with truncation disabled
        renderer.display_events_table(test_events, scene, truncate_descriptions=False)
        # Expected output should be the same as the first case if descriptions are short
        expected_output_no_trunc = (
            f"### Events in Scene: {scene.title}\n\n"
            f"| ID | Time | Source | Description |\n"
            f"|---|---|---|---|\n"
            f"| `{event1.id}` | {event1.created_at.strftime('%Y-%m-%d %H:%M')} | {event1.source_name} | {event1.description} |\n"
            f"| `{event2.id}` | {event2.created_at.strftime('%Y-%m-%d %H:%M')} | {event2.source_name} | {event2.description} |"
        )
        mock_console.print.assert_called_with(expected_output_no_trunc)
        mock_console.reset_mock()


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
        mock_console.print.assert_called_with(expected_output)


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
        renderer.display_games_table(games, active_game=test_game)
        expected_output_active = (
            "### Games\n\n"
            "| ID | Name | Description | Acts | Scenes | Current |\n"
        "|---|---|---|---|---|---|\n"
        f"| `{test_game.id}` | **{test_game.name}** | {test_game.description} | 0 | 0 | ✓ |\n"
        f"| `{other_game.id}` | {other_game.name} | {other_game.description} | 0 | 0 |  |"
    )
    mock_console.print.assert_called_with(expected_output_active)
    mock_console.reset_mock()

    # Test case 2: Without an active game
    renderer.display_games_table(games, active_game=None)
    expected_output_no_active = (
        "### Games\n\n"
        "| ID | Name | Description | Acts | Scenes | Current |\n"
        "|---|---|---|---|---|---|\n"
        f"| `{test_game.id}` | {test_game.name} | {test_game.description} | 0 | 0 |  |\n"
        f"| `{other_game.id}` | {other_game.name} | {other_game.description} | 0 | 0 |  |"
    )
    mock_console.print.assert_called_with(expected_output_no_active)
    mock_console.reset_mock()


def test_display_games_table_no_games_markdown(mock_console: MagicMock):
    """Test displaying an empty list of games as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_games_table([], active_game=None)
    expected_output = "No games found. Create one with 'sologm game create'."
    mock_console.print.assert_called_with(expected_output)


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
            status=SceneStatus.ACTIVE,
        )
        other_scene = create_test_scene(
            session,
            act_id=act.id,
            title="Other Scene",
            description="Another scene.",
            is_active=False,
            status=SceneStatus.ACTIVE,
        )
        # Ensure sequences are different if needed by display logic (factory handles this)
        scenes = sorted(
            [test_scene, other_scene], key=lambda s: s.sequence
        )  # Sort by sequence for predictable table order

        # Test case 1: With an active scene ID
        renderer.display_scenes_table(scenes, active_scene_id=test_scene.id)
        expected_output_active = (
            "### Scenes\n\n"
            "| ID | Title | Description | Status | Current | Sequence |\n"
        "|---|---|---|---|---|---|\n"
        f"| `{test_scene.id}` | **{test_scene.title}** | {test_scene.description} | {test_scene.status.value} | ✓ | {test_scene.sequence} |\n"
        f"| `{other_scene.id}` | {other_scene.title} | {other_scene.description} | {other_scene.status.value} |  | {other_scene.sequence} |"
    )
    mock_console.print.assert_called_with(expected_output_active)
    mock_console.reset_mock()

    # Test case 2: Without an active scene ID
    renderer.display_scenes_table(scenes, active_scene_id=None)
    expected_output_no_active = (
        "### Scenes\n\n"
        "| ID | Title | Description | Status | Current | Sequence |\n"
        "|---|---|---|---|---|---|\n"
        f"| `{test_scene.id}` | {test_scene.title} | {test_scene.description} | {test_scene.status.value} |  | {test_scene.sequence} |\n"
        f"| `{other_scene.id}` | {other_scene.title} | {other_scene.description} | {other_scene.status.value} |  | {other_scene.sequence} |"
    )
    mock_console.print.assert_called_with(expected_output_no_active)
    mock_console.reset_mock()


def test_display_scenes_table_no_scenes_markdown(mock_console: MagicMock):
    """Test displaying an empty list of scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_scenes_table([], active_scene_id=None)
    expected_output = "No scenes found. Create one with 'sologm scene create'."
    mock_console.print.assert_called_with(expected_output)


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
        renderer.display_game_info(test_game, active_scene=test_scene)
        expected_output_active = (
            f"## {test_game.name} (`{test_game.slug}` / `{test_game.id}`)\n\n"
            f"{test_game.description}\n\n"
            f"*   **Created:** {test_game.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_game.modified_at.strftime('%Y-%m-%d')}\n"
            f"*   **Acts:** {len(test_game.acts)}\n"  # Use calculated property
            f"*   **Scenes:** {sum(len(a.scenes) for a in test_game.acts)}\n" # Use calculated property
            f"*   **Active Scene:** {test_scene.title}"
        )
        mock_console.print.assert_called_with(expected_output_active)
        mock_console.reset_mock()

        # Test case 2: Without active scene
        renderer.display_game_info(test_game, active_scene=None)
        expected_output_no_active = (
            f"## {test_game.name} (`{test_game.slug}` / `{test_game.id}`)\n\n"
            f"{test_game.description}\n\n"
            f"*   **Created:** {test_game.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_game.modified_at.strftime('%Y-%m-%d')}\n"
            f"*   **Acts:** {len(test_game.acts)}\n"
            f"*   **Scenes:** {sum(len(a.scenes) for a in test_game.acts)}"
            # No Active Scene line
        )
        mock_console.print.assert_called_with(expected_output_no_active)


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
        session.refresh(
            test_interpretation_set, attribute_names=["interpretations"]
        )
        num_interpretations = len(test_interpretations)

        # --- Test case 1: Show context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(
            test_interpretation_set, show_context=True
        )

        expected_context = (
            f"### Oracle Interpretations\n\n"
            f"**Context:** {test_interpretation_set.context}\n"
            f"**Results:** {test_interpretation_set.oracle_results}\n\n"
            f"---"
        )
        expected_instruction = (
            f"Interpretation Set ID: `{test_interpretation_set.id}`\n"
            f"(Use 'sologm oracle select' to choose)"
        )
        # Expected calls: context(1) + N interpretations + N blank lines + instruction(1) = 2*N + 2
        expected_call_count_true = num_interpretations * 2 + 2
        assert mock_console.print.call_count == expected_call_count_true
        mock_console.print.assert_any_call(expected_context)
        mock_console.print.assert_any_call(expected_instruction)
        # We don't assert the exact interpretation calls here, as that's tested elsewhere

        # --- Test case 2: Hide context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(
            test_interpretation_set, show_context=False
        )

        # Expected calls: N interpretations + N blank lines + instruction(1) = 2*N + 1
        expected_call_count_false = num_interpretations * 2 + 1
        assert mock_console.print.call_count == expected_call_count_false
        # Ensure context was NOT printed
        printed_calls = [call.args[0] for call in mock_console.print.call_args_list]
        assert expected_context not in printed_calls
        # Check instruction print call again
        mock_console.print.assert_any_call(expected_instruction)


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
            status=SceneStatus.ACTIVE,
        )
        # Refresh scene to load act relationship
        session.refresh(test_scene, attribute_names=["act"])

        renderer.display_scene_info(test_scene)

        act_title = test_scene.act.title or "Untitled Act"
        act_info = f"Act {test_scene.act.sequence}: {act_title}"
        status_indicator = (
            " ✓" if test_scene.status == SceneStatus.COMPLETED else ""
        )

        expected_output = (
            f"### Scene {test_scene.sequence}: {test_scene.title}{status_indicator} (`{test_scene.id}`)\n\n"
            f"{test_scene.description}\n\n"
            f"*   **Status:** {test_scene.status.value}\n"
            f"*   **Act:** {act_info}\n"
            f"*   **Created:** {test_scene.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_scene.modified_at.strftime('%Y-%m-%d')}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
        renderer.display_acts_table(acts, active_act_id=test_act.id)
        expected_output_active = (
            "### Acts\n\n"
            "| ID | Seq | Title | Summary | Current |\n"
            "|---|---|---|---|---|\n"
            f"| `{test_act.id}` | {test_act.sequence} | **{test_act.title}** | {test_act.summary} | ✓ |\n"
            f"| `{other_act.id}` | {other_act.sequence} | {other_act.title} | {other_act.summary} |  |"
        )
        mock_console.print.assert_called_with(expected_output_active)
        mock_console.reset_mock()

        # Test case 2: Without an active act ID
        renderer.display_acts_table(acts, active_act_id=None)
        expected_output_no_active = (
            "### Acts\n\n"
            "| ID | Seq | Title | Summary | Current |\n"
            "|---|---|---|---|---|\n"
            f"| `{test_act.id}` | {test_act.sequence} | {test_act.title} | {test_act.summary} |  |\n"
            f"| `{other_act.id}` | {other_act.sequence} | {other_act.title} | {other_act.summary} |  |"
        )
        mock_console.print.assert_called_with(expected_output_no_active)


def test_display_acts_table_no_acts_markdown(mock_console: MagicMock):
    """Test displaying an empty list of acts as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_acts_table([], active_act_id=None)
    expected_output = "No acts found. Create one with 'sologm act create'."
    mock_console.print.assert_called_with(expected_output)


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

        # Expected output for act info
        expected_act_output = (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)\n\n"
            f"{test_act.summary}\n\n"
            f"*   **Game:** {test_game.name}\n"
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
        )

        # Expected output for scenes table within act info
        active_scene_id_in_test = test_scene.id
        is_active = active_scene_id_in_test and test_scene.id == active_scene_id_in_test
        active_marker = "✓" if is_active else ""
        scene_title_display = (
            f"**{test_scene.title}**" if is_active else test_scene.title
        )
        scene_description = test_scene.description

        expected_scenes_output = (
            "### Scenes\n\n"
            "| ID | Title | Description | Status | Current | Sequence |\n"
            "|---|---|---|---|---|---|\n"
            f"| `{test_scene.id}` "
            f"| {scene_title_display} "
            f"| {scene_description} "
            f"| {test_scene.status.value} "
            f"| {active_marker} "
            f"| {test_scene.sequence} |"
        )

        # Check that both parts were printed in order with a blank line
        calls = mock_console.print.call_args_list
        assert len(calls) == 3  # Act Info, Blank Line, Scenes Table
        assert calls[0].args[0] == expected_act_output
        assert calls[1].args[0] == ""  # Check for the blank line
        assert calls[2].args[0] == expected_scenes_output


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
        session.refresh(test_act, attribute_names=["scenes"]) # Should be empty

        renderer.display_act_info(test_act, test_game.name)

        # Expected output for act info (same as before)
        expected_act_output = (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)\n\n"
            f"{test_act.summary}\n\n"
            f"*   **Game:** {test_game.name}\n"
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
        )

        # Expected outputs for the "no scenes" part
        expected_no_scenes_header = f"### Scenes in Act {test_act.sequence}"
        expected_no_scenes_message = "No scenes in this act yet."
        expected_blank_line = ""

        # Check the sequence of calls
        calls = mock_console.print.call_args_list
        assert len(calls) == 5 # Act Info, Blank Line, Header, Blank Line, Message
        assert calls[0].args[0] == expected_act_output
        assert calls[1].args[0] == expected_blank_line
        assert calls[2].args[0] == expected_no_scenes_header
        assert calls[3].args[0] == expected_blank_line
        assert calls[4].args[0] == expected_no_scenes_message


# Import truncate_text utility
from sologm.cli.utils.display import truncate_text

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
        ) # Mark one as selected
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

        truncated_context = truncate_text(
            test_interpretation_set.context, max_length=40
        )
        truncated_results = truncate_text(
            test_interpretation_set.oracle_results, max_length=40
        )
        status = "Resolved" if any(i.is_selected for i in test_interpretations) else "Pending"

        expected_output = (
            "### Oracle Interpretation Sets\n\n"
            "| ID | Scene | Context | Oracle Results | Created | Status | Count |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| `{test_interpretation_set.id}` "
            f"| {test_scene.title} "
            f"| {truncated_context} "
            f"| {truncated_results} "
            f"| {test_interpretation_set.created_at.strftime('%Y-%m-%d %H:%M')} "
            f"| {status} "
            f"| {len(test_interpretations)} |"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
        session.refresh(
            test_interpretation_set, attribute_names=["interpretations"]
        )

        renderer.display_interpretation_status(test_interpretation_set)

        is_resolved = any(i.is_selected for i in test_interpretation_set.interpretations)

        expected_output = (
            f"### Current Oracle Interpretation Status\n\n"
            f"**Context:** {test_interpretation_set.context}\n"
            f"**Results:** {test_interpretation_set.oracle_results}\n\n"
            f"*   **Set ID:** `{test_interpretation_set.id}`\n"
            f"*   **Retry Count:** {test_interpretation_set.retry_attempt}\n"
            f"*   **Resolved:** {is_resolved}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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

        expected_output = (
            "### AI Generation Results\n\n"
            "**AI-Generated Title:**\n"
            "> AI Title\n\n"
            "**Current Title:**\n"
            f"> {test_act.title}\n\n"
            "---\n\n"
            "**AI-Generated Summary:**\n"
            "> AI Summary\n\n"
            "**Current Summary:**\n"
            f"> {test_act.summary}\n"
        )
        mock_console.print.assert_called_once_with(expected_output)


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

        expected_output = (
            f"## Act '{test_act.title}' Completed Successfully!\n\n"
            f"*   **ID:** `{test_act.id}`\n"
            f"*   **Sequence:** Act {test_act.sequence}\n"
            f"*   **Status:** Completed\n\n" # Assumes display method implies completion
            f"**Final Title:**\n> {test_act.title}\n\n"
            f"**Final Summary:**\n> {test_act.summary}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_act_edited_content_preview ---


def test_display_act_edited_content_preview_markdown(mock_console: MagicMock):
    """Test displaying edited content preview as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}

    renderer.display_act_edited_content_preview(edited_results)

    expected_output = (
        "### Preview of Edited Content:\n\n"
        "**Edited Title:**\n"
        "> Edited Title\n\n"
        "**Edited Summary:**\n"
        "> Edited Summary"
    )
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_error ---


def test_display_error_markdown(mock_console: MagicMock):
    """Test displaying an error message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    error_message = "Something went wrong!"
    renderer.display_error(error_message)

    expected_output = f"> **Error:** {error_message}"
    mock_console.print.assert_called_once_with(expected_output)


# --- Add other tests below ---
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
        session.refresh(
            test_interpretation_set, attribute_names=["interpretations"]
        )
        num_interpretations = len(test_interpretations)

        # --- Test case 1: Show context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(
            test_interpretation_set, show_context=True
        )

        expected_context = (
            f"### Oracle Interpretations\n\n"
            f"**Context:** {test_interpretation_set.context}\n"
            f"**Results:** {test_interpretation_set.oracle_results}\n\n"
            f"---"
        )
        expected_instruction = (
            f"Interpretation Set ID: `{test_interpretation_set.id}`\n"
            f"(Use 'sologm oracle select' to choose)"
        )
        # Expected calls: context(1) + N interpretations + N blank lines + instruction(1) = 2*N + 2
        expected_call_count_true = num_interpretations * 2 + 2
        assert mock_console.print.call_count == expected_call_count_true
        mock_console.print.assert_any_call(expected_context)
        mock_console.print.assert_any_call(expected_instruction)
        # We don't assert the exact interpretation calls here, as that's tested elsewhere

        # --- Test case 2: Hide context ---
        mock_console.reset_mock()
        renderer.display_interpretation_set(
            test_interpretation_set, show_context=False
        )

        # Expected calls: N interpretations + N blank lines + instruction(1) = 2*N + 1
        expected_call_count_false = num_interpretations * 2 + 1
        assert mock_console.print.call_count == expected_call_count_false
        # Ensure context was NOT printed
        printed_calls = [call.args[0] for call in mock_console.print.call_args_list]
        assert expected_context not in printed_calls
        # Check instruction print call again
        mock_console.print.assert_any_call(expected_instruction)


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
            status=SceneStatus.ACTIVE,
        )
        # Refresh scene to load act relationship
        session.refresh(test_scene, attribute_names=["act"])

        renderer.display_scene_info(test_scene)

        act_title = test_scene.act.title or "Untitled Act"
        act_info = f"Act {test_scene.act.sequence}: {act_title}"
        status_indicator = (
            " ✓" if test_scene.status == SceneStatus.COMPLETED else ""
        )

        expected_output = (
            f"### Scene {test_scene.sequence}: {test_scene.title}{status_indicator} (`{test_scene.id}`)\n\n"
            f"{test_scene.description}\n\n"
            f"*   **Status:** {test_scene.status.value}\n"
            f"*   **Act:** {act_info}\n"
            f"*   **Created:** {test_scene.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_scene.modified_at.strftime('%Y-%m-%d')}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
        renderer.display_acts_table(acts, active_act_id=test_act.id)
        expected_output_active = (
            "### Acts\n\n"
            "| ID | Seq | Title | Summary | Current |\n"
            "|---|---|---|---|---|\n"
            f"| `{test_act.id}` | {test_act.sequence} | **{test_act.title}** | {test_act.summary} | ✓ |\n"
            f"| `{other_act.id}` | {other_act.sequence} | {other_act.title} | {other_act.summary} |  |"
        )
        mock_console.print.assert_called_with(expected_output_active)
        mock_console.reset_mock()

        # Test case 2: Without an active act ID
        renderer.display_acts_table(acts, active_act_id=None)
        expected_output_no_active = (
            "### Acts\n\n"
            "| ID | Seq | Title | Summary | Current |\n"
            "|---|---|---|---|---|\n"
            f"| `{test_act.id}` | {test_act.sequence} | {test_act.title} | {test_act.summary} |  |\n"
            f"| `{other_act.id}` | {other_act.sequence} | {other_act.title} | {other_act.summary} |  |"
        )
        mock_console.print.assert_called_with(expected_output_no_active)


def test_display_acts_table_no_acts_markdown(mock_console: MagicMock):
    """Test displaying an empty list of acts as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_acts_table([], active_act_id=None)
    expected_output = "No acts found. Create one with 'sologm act create'."
    mock_console.print.assert_called_with(expected_output)


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

        # Expected output for act info
        expected_act_output = (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)\n\n"
            f"{test_act.summary}\n\n"
            f"*   **Game:** {test_game.name}\n"
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
        )

        # Expected output for scenes table within act info
        active_scene_id_in_test = test_scene.id
        is_active = active_scene_id_in_test and test_scene.id == active_scene_id_in_test
        active_marker = "✓" if is_active else ""
        scene_title_display = (
            f"**{test_scene.title}**" if is_active else test_scene.title
        )
        scene_description = test_scene.description

        expected_scenes_output = (
            "### Scenes\n\n"
            "| ID | Title | Description | Status | Current | Sequence |\n"
            "|---|---|---|---|---|---|\n"
            f"| `{test_scene.id}` "
            f"| {scene_title_display} "
            f"| {scene_description} "
            f"| {test_scene.status.value} "
            f"| {active_marker} "
            f"| {test_scene.sequence} |"
        )

        # Check that both parts were printed in order with a blank line
        calls = mock_console.print.call_args_list
        assert len(calls) == 3  # Act Info, Blank Line, Scenes Table
        assert calls[0].args[0] == expected_act_output
        assert calls[1].args[0] == ""  # Check for the blank line
        assert calls[2].args[0] == expected_scenes_output


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
        session.refresh(test_act, attribute_names=["scenes"]) # Should be empty

        renderer.display_act_info(test_act, test_game.name)

        # Expected output for act info (same as before)
        expected_act_output = (
            f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)\n\n"
            f"{test_act.summary}\n\n"
            f"*   **Game:** {test_game.name}\n"
            f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}\n"
            f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
        )

        # Expected outputs for the "no scenes" part
        expected_no_scenes_header = f"### Scenes in Act {test_act.sequence}"
        expected_no_scenes_message = "No scenes in this act yet."
        expected_blank_line = ""

        # Check the sequence of calls
        calls = mock_console.print.call_args_list
        assert len(calls) == 5 # Act Info, Blank Line, Header, Blank Line, Message
        assert calls[0].args[0] == expected_act_output
        assert calls[1].args[0] == expected_blank_line
        assert calls[2].args[0] == expected_no_scenes_header
        assert calls[3].args[0] == expected_blank_line
        assert calls[4].args[0] == expected_no_scenes_message


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
        ) # Mark one as selected
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

        truncated_context = truncate_text(
            test_interpretation_set.context, max_length=40
        )
        truncated_results = truncate_text(
            test_interpretation_set.oracle_results, max_length=40
        )
        status = "Resolved" if any(i.is_selected for i in test_interpretations) else "Pending"

        expected_output = (
            "### Oracle Interpretation Sets\n\n"
            "| ID | Scene | Context | Oracle Results | Created | Status | Count |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| `{test_interpretation_set.id}` "
            f"| {test_scene.title} "
            f"| {truncated_context} "
            f"| {truncated_results} "
            f"| {test_interpretation_set.created_at.strftime('%Y-%m-%d %H:%M')} "
            f"| {status} "
            f"| {len(test_interpretations)} |"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
        session.refresh(
            test_interpretation_set, attribute_names=["interpretations"]
        )

        renderer.display_interpretation_status(test_interpretation_set)

        is_resolved = any(i.is_selected for i in test_interpretation_set.interpretations)

        expected_output = (
            f"### Current Oracle Interpretation Status\n\n"
            f"**Context:** {test_interpretation_set.context}\n"
            f"**Results:** {test_interpretation_set.oracle_results}\n\n"
            f"*   **Set ID:** `{test_interpretation_set.id}`\n"
            f"*   **Retry Count:** {test_interpretation_set.retry_attempt}\n"
            f"*   **Resolved:** {is_resolved}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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

        expected_output = (
            "### AI Generation Results\n\n"
            "**AI-Generated Title:**\n"
            "> AI Title\n\n"
            "**Current Title:**\n"
            f"> {test_act.title}\n\n"
            "---\n\n"
            "**AI-Generated Summary:**\n"
            "> AI Summary\n\n"
            "**Current Summary:**\n"
            f"> {test_act.summary}\n"
        )
        mock_console.print.assert_called_once_with(expected_output)


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

        expected_output = (
            f"## Act '{test_act.title}' Completed Successfully!\n\n"
            f"*   **ID:** `{test_act.id}`\n"
            f"*   **Sequence:** Act {test_act.sequence}\n"
            f"*   **Status:** Completed\n\n" # Assumes display method implies completion
            f"**Final Title:**\n> {test_act.title}\n\n"
            f"**Final Summary:**\n> {test_act.summary}"
        )
        mock_console.print.assert_called_once_with(expected_output)


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
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_act_edited_content_preview ---


def test_display_act_edited_content_preview_markdown(mock_console: MagicMock):
    """Test displaying edited content preview as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}

    renderer.display_act_edited_content_preview(edited_results)

    expected_output = (
        "### Preview of Edited Content:\n\n"
        "**Edited Title:**\n"
        "> Edited Title\n\n"
        "**Edited Summary:**\n"
        "> Edited Summary"
    )
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_error ---


def test_display_error_markdown(mock_console: MagicMock):
    """Test displaying an error message as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    error_message = "Something went wrong!"
    renderer.display_error(error_message)

    expected_output = f"> **Error:** {error_message}"
    mock_console.print.assert_called_once_with(expected_output)


# --- Add other tests below ---
