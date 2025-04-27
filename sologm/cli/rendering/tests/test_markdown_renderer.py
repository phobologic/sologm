"""
Unit tests for the MarkdownRenderer class.
"""

import logging

# Import the renderer and models needed for tests
from typing import List  # <-- Added import
from unittest.mock import MagicMock

import pytest
from rich.console import Console  # <-- Import Console

# Import the renderer and models needed for tests
from sologm.cli.rendering.markdown_renderer import MarkdownRenderer
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus

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


def test_display_dice_roll_markdown(mock_console: MagicMock, test_dice_roll: DiceRoll):
    """Test displaying a dice roll as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Modify the test dice roll for a more complete test case
    test_dice_roll.notation = "2d6+1"
    test_dice_roll.individual_results = [4, 3]
    test_dice_roll.modifier = 1
    test_dice_roll.total = 8
    test_dice_roll.reason = "Test Roll"

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
    mock_console: MagicMock, test_interpretations: list[Interpretation]
):
    """Test displaying a single interpretation as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    interp = test_interpretations[0]  # Assuming fixture provides at least one

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
    mock_console: MagicMock, test_events: List[Event], test_scene: Scene
):
    """Test displaying a list of events as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Test with events and default truncation
    renderer.display_events_table(test_events, test_scene)

    # Expected output (adjust based on test_events fixture data)
    event1 = test_events[0]
    event2 = test_events[1]
    expected_output = (
        f"### Events in Scene: {test_scene.title}\n\n"
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
        test_events, test_scene, max_description_length=short_len
    )
    truncated_desc1 = event1.description[: short_len - 3] + "..."
    truncated_desc2 = event2.description[: short_len - 3] + "..."
    expected_output_truncated = (
        f"### Events in Scene: {test_scene.title}\n\n"
        f"| ID | Time | Source | Description |\n"
        f"|---|---|---|---|\n"
        f"| `{event1.id}` | {event1.created_at.strftime('%Y-%m-%d %H:%M')} | {event1.source_name} | {truncated_desc1} |\n"
        f"| `{event2.id}` | {event2.created_at.strftime('%Y-%m-%d %H:%M')} | {event2.source_name} | {truncated_desc2} |"
    )
    mock_console.print.assert_called_with(expected_output_truncated)
    mock_console.reset_mock()

    # Test with truncation disabled
    renderer.display_events_table(test_events, test_scene, truncate_descriptions=False)
    # Expected output should be the same as the first case if descriptions are short
    expected_output_no_trunc = (
        f"### Events in Scene: {test_scene.title}\n\n"
        f"| ID | Time | Source | Description |\n"
        f"|---|---|---|---|\n"
        f"| `{event1.id}` | {event1.created_at.strftime('%Y-%m-%d %H:%M')} | {event1.source_name} | {event1.description} |\n"
        f"| `{event2.id}` | {event2.created_at.strftime('%Y-%m-%d %H:%M')} | {event2.source_name} | {event2.description} |"
    )
    mock_console.print.assert_called_with(expected_output_no_trunc)
    mock_console.reset_mock()


def test_display_events_table_no_events_markdown(
    mock_console: MagicMock, test_scene: Scene
):
    """Test displaying an empty list of events as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_events_table([], test_scene)
    expected_output = f"\nNo events in scene '{test_scene.title}'"
    mock_console.print.assert_called_with(expected_output)


# --- Test for display_games_table ---


def test_display_games_table_markdown(mock_console: MagicMock, test_game: Game):
    """Test displaying a list of games as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    other_game = Game(
        id="game-other",
        name="Other Game",
        description="Another game.",
        slug="other-game",
        is_active=False,
        # Add created_at/modified_at if needed by the method
        created_at=test_game.created_at,
        modified_at=test_game.modified_at,
    )
    # Mock relationships if needed by the display method (e.g., act/scene counts)
    test_game.acts = []
    test_game.scenes = []
    other_game.acts = []
    other_game.scenes = []

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


def test_display_scenes_table_markdown(mock_console: MagicMock, test_scene: Scene):
    """Test displaying a list of scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    other_scene = Scene(
        id="scene-other",
        act_id=test_scene.act_id,
        title="Other Scene",
        description="Another scene.",
        sequence=test_scene.sequence + 1,
        status=test_scene.status,
        is_active=False,
        # Add created_at/modified_at if needed by the method
        created_at=test_scene.created_at,
        modified_at=test_scene.modified_at,
    )
    scenes = [test_scene, other_scene]

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
    mock_console: MagicMock, test_game: Game, test_scene: Scene
):
    """Test displaying game info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Mock relationships needed by the display method
    # Ensure the act object itself has the scene associated
    if test_scene.act:  # Make sure the act exists from the fixture
        test_scene.act.scenes = [test_scene]
        test_game.acts = [test_scene.act]
    else:
        # Handle case where test_scene might not have an act (though fixture should provide it)
        pytest.fail(
            "Test setup error: test_scene fixture did not provide an associated act."
        )
        test_game.acts = []  # Or handle appropriately

    # Remove the direct assignment to game.scenes as it's not used by the calculation logic being tested
    # test_game.scenes = [test_scene] # This line is removed/commented out

    # Test case 1: With active scene
    renderer.display_game_info(test_game, active_scene=test_scene)
    expected_output_active = (
        f"## {test_game.name} (`{test_game.slug}` / `{test_game.id}`)\n\n"
        f"{test_game.description}\n\n"
        f"*   **Created:** {test_game.created_at.strftime('%Y-%m-%d')}\n"
        f"*   **Modified:** {test_game.modified_at.strftime('%Y-%m-%d')}\n"
        f"*   **Acts:** 1\n"  # Based on mocked relationship
        f"*   **Scenes:** 1\n"  # Based on mocked relationship
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
        f"*   **Acts:** 1\n"
        f"*   **Scenes:** 1"
        # No Active Scene line
    )
    mock_console.print.assert_called_with(expected_output_no_active)


# --- Test for display_interpretation_set ---


def test_display_interpretation_set_markdown(
    mock_console: MagicMock,
    test_interpretation_set: InterpretationSet,
    test_interpretations: List[Interpretation],
):
    """Tests the Markdown rendering of an InterpretationSet.

    This test verifies that the `display_interpretation_set` method of the
    `MarkdownRenderer` produces the correct Markdown output for an
    `InterpretationSet` object.

    It specifically checks:
    - The rendering of the context section (header, context text, results text)
      when `show_context` is True.
    - That the context section is *not* rendered when `show_context` is False.
    - The rendering of the instruction footer containing the set ID and usage hint.
    - That the correct number of `console.print` calls are made, implying that
      `display_interpretation` is invoked for each interpretation within the set
      (though the exact output of `display_interpretation` is tested separately).

    Args:
        mock_console: The mocked Rich Console fixture.
        test_interpretation_set: Fixture providing an InterpretationSet instance.
        test_interpretations: Fixture providing a list of Interpretation instances.
    """
    renderer = MarkdownRenderer(mock_console)
    # Ensure the set has the interpretations linked for the test
    test_interpretation_set.interpretations = test_interpretations
    num_interpretations = len(test_interpretations)

    # --- Test case 1: Show context ---
    mock_console.reset_mock()  # Ensure clean state before this case

    renderer.display_interpretation_set(test_interpretation_set, show_context=True)

    for i, call in enumerate(mock_console.print.call_args_list):
        # Truncate long call args for readability in debug output
        args_repr = repr(call.args)
        if len(args_repr) > 100:
            args_repr = args_repr[:97] + "..."

    # Expected output (simplified, relies on display_interpretation output)
    expected_context = (
        f"### Oracle Interpretations\n\n"
        f"**Context:** {test_interpretation_set.context}\n"
        f"**Results:** {test_interpretation_set.oracle_results}\n\n"
        f"---"
    )
    # Expected calls: context(1) + N interpretations + N blank lines + instruction(1) = 2*N + 2
    expected_call_count_true = num_interpretations * 2 + 2
    assert (
        mock_console.print.call_count == expected_call_count_true
    )  # <-- ADJUSTED EXPECTED COUNT

    # Check context print call
    mock_console.print.assert_any_call(expected_context)
    # Check instruction print call
    expected_instruction = (
        f"Interpretation Set ID: `{test_interpretation_set.id}`\n"
        f"(Use 'sologm oracle select' to choose)"
    )
    mock_console.print.assert_any_call(expected_instruction)
    mock_console.reset_mock()

    # --- Test case 2: Hide context ---
    mock_console.reset_mock()  # Ensure clean state before this case

    renderer.display_interpretation_set(test_interpretation_set, show_context=False)

    for i, call in enumerate(mock_console.print.call_args_list):
        args_repr = repr(call.args)
        if len(args_repr) > 100:
            args_repr = args_repr[:97] + "..."

    # Expected calls: N interpretations + N blank lines + instruction(1) = 2*N + 1
    expected_call_count_false = num_interpretations * 2 + 1
    assert (
        mock_console.print.call_count == expected_call_count_false
    )  # <-- ADJUSTED EXPECTED COUNT

    # Ensure context was NOT printed
    with pytest.raises(
        AssertionError,
        match="call not found",  # Match the actual error message
    ):
        mock_console.print.assert_any_call(expected_context)

    # Check instruction print call again
    mock_console.print.assert_any_call(expected_instruction)


def test_display_scene_info_markdown(mock_console: MagicMock, test_scene: Scene):
    """Test displaying scene info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Ensure act relationship is loaded for the test
    if not hasattr(test_scene, "act") or not test_scene.act:
        # Mock the act if necessary for testing display logic
        test_scene.act = MagicMock(spec=Act)
        test_scene.act.sequence = 1
        test_scene.act.title = "Mock Act Title"

    renderer.display_scene_info(test_scene)

    act_title = test_scene.act.title or "Untitled Act"
    act_info = f"Act {test_scene.act.sequence}: {act_title}"
    status_indicator = " ✓" if test_scene.status == SceneStatus.COMPLETED else ""

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


def test_display_acts_table_markdown(mock_console: MagicMock, test_act: Act):
    """Test displaying a list of acts as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    other_act = Act(
        id="act-other",
        game_id=test_act.game_id,
        sequence=test_act.sequence + 1,
        title="Other Act",
        summary="Another act.",
        is_active=False,
        created_at=test_act.created_at,
        modified_at=test_act.modified_at,
    )
    acts = [test_act, other_act]

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
    mock_console: MagicMock, test_act: Act, test_game: Game, test_scene: Scene
):
    """Test displaying act info as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Mock relationships for the test
    test_act.scenes = [test_scene]
    test_scene.act = test_act  # Ensure back-reference if needed by display logic

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
    # This should match the output of display_scenes_table called with the active scene
    # Determine active status based on how display_scenes_table is called
    # display_act_info finds the active scene ID and passes it.
    active_scene_id_in_test = test_scene.id  # Assuming fixture sets is_active=True
    is_active = active_scene_id_in_test and test_scene.id == active_scene_id_in_test
    active_marker = "✓" if is_active else ""
    scene_title_display = f"**{test_scene.title}**" if is_active else test_scene.title
    scene_description = test_scene.description  # display_scenes_table doesn't truncate

    expected_scenes_output = (
        "### Scenes\n\n"  # Header from display_scenes_table
        "| ID | Title | Description | Status | Current | Sequence |\n"  # Columns from display_scenes_table
        "|---|---|---|---|---|---|\n"
        f"| `{test_scene.id}` "
        f"| {scene_title_display} "  # Correct title formatting (bold if active)
        f"| {scene_description} "  # Correct description (no truncation)
        f"| {test_scene.status.value} "
        f"| {active_marker} "  # Correct active marker
        f"| {test_scene.sequence} |"  # Correct sequence position
    )

    # Check that both parts were printed
    # Need to check the calls in order or use assert_any_call carefully
    # The blank line print call happens between act info and scenes table
    calls = mock_console.print.call_args_list
    assert len(calls) == 3  # Act Info, Blank Line, Scenes Table
    assert calls[0].args[0] == expected_act_output
    assert calls[1].args[0] == ""  # Check for the blank line
    assert calls[2].args[0] == expected_scenes_output

    # Alternative using assert_any_call (less strict about order/intermediate calls)
    # mock_console.print.assert_any_call(expected_act_output)
    # mock_console.print.assert_any_call(expected_scenes_output)
    # assert mock_console.print.call_count >= 2 # Check at least two calls were made

    # Sticking with the more precise check above based on implementation details


def test_display_act_info_no_scenes_markdown(
    mock_console: MagicMock, test_act: Act, test_game: Game
):
    """Test displaying act info with no scenes as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    test_act.scenes = []  # Ensure no scenes

    renderer.display_act_info(test_act, test_game.name)

    # Expected output for act info (same as before)
    expected_act_output = (
        f"## Act {test_act.sequence}: {test_act.title} (`{test_act.id}`)\n\n"
        f"{test_act.summary}\n\n"
        f"*   **Game:** {test_game.name}\n"
        f"*   **Created:** {test_act.created_at.strftime('%Y-%m-%d')}\n"
        f"*   **Modified:** {test_act.modified_at.strftime('%Y-%m-%d')}"
    )

    # Expected outputs for the "no scenes" part (now separate)
    expected_no_scenes_header = f"### Scenes in Act {test_act.sequence}"
    expected_no_scenes_message = "No scenes in this act yet."
    expected_blank_line = "" # For the blank lines printed

    # Check the sequence of calls
    calls = mock_console.print.call_args_list

    # Expected calls: Act Info, Blank Line, Header, Blank Line, Message
    assert len(calls) == 5

    # Assert each call in the sequence
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
    test_interpretation_set: InterpretationSet,
    test_interpretations: List[Interpretation],
    test_scene: Scene,
):
    """Test displaying interpretation sets table as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    # Link interpretations and scene for the test
    test_interpretation_set.interpretations = test_interpretations
    test_interpretation_set.scene = test_scene
    # Ensure one interpretation is selected
    test_interpretations[0].is_selected = True
    test_interpretations[1].is_selected = False

    interp_sets = [test_interpretation_set]

    renderer.display_interpretation_sets_table(interp_sets)

    # Use the actual values from the fixture, truncate_text handles ellipsis if needed
    truncated_context = truncate_text(test_interpretation_set.context, max_length=40)
    truncated_results = truncate_text(
        test_interpretation_set.oracle_results, max_length=40
    )

    expected_output = (
        "### Oracle Interpretation Sets\n\n"
        "| ID | Scene | Context | Oracle Results | Created | Status | Count |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| `{test_interpretation_set.id}` "
        f"| {test_scene.title} "
        f"| {truncated_context} "
        f"| {truncated_results} "
        f"| {test_interpretation_set.created_at.strftime('%Y-%m-%d %H:%M')} "
        f"| Resolved "
        f"| {len(test_interpretations)} |"
    )
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_interpretation_status ---


def test_display_interpretation_status_markdown(
    mock_console: MagicMock,
    test_interpretation_set: InterpretationSet,
    test_interpretations: List[Interpretation],
):
    """Test displaying interpretation status as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    # Link interpretations for the test
    test_interpretation_set.interpretations = test_interpretations
    test_interpretations[0].is_selected = True  # Mark one as selected

    renderer.display_interpretation_status(test_interpretation_set)

    expected_output = (
        f"### Current Oracle Interpretation Status\n\n"
        f"**Context:** {test_interpretation_set.context}\n"
        f"**Results:** {test_interpretation_set.oracle_results}\n\n"
        f"*   **Set ID:** `{test_interpretation_set.id}`\n"
        f"*   **Retry Count:** {test_interpretation_set.retry_attempt}\n"
        f"*   **Resolved:** True"
    )
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_act_ai_generation_results ---


def test_display_act_ai_generation_results_markdown(
    mock_console: MagicMock, test_act: Act
):
    """Test displaying AI generation results for an act as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    results = {"title": "AI Title", "summary": "AI Summary"}
    test_act.title = "Existing Title"
    test_act.summary = "Existing Summary"

    renderer.display_act_ai_generation_results(results, test_act)

    expected_output = (
        "### AI Generation Results\n\n"
        "**AI-Generated Title:**\n"
        "> AI Title\n\n"
        "**Current Title:**\n"
        "> Existing Title\n\n"
        "---\n\n"
        "**AI-Generated Summary:**\n"
        "> AI Summary\n\n"
        "**Current Summary:**\n"
        "> Existing Summary\n"
    )
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_act_completion_success ---


def test_display_act_completion_success_markdown(
    mock_console: MagicMock, test_act: Act
):
    """Test displaying act completion success as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    renderer.display_act_completion_success(test_act)

    expected_output = (
        f"## Act '{test_act.title}' Completed Successfully!\n\n"
        f"*   **ID:** `{test_act.id}`\n"
        f"*   **Sequence:** Act {test_act.sequence}\n"
        f"*   **Status:** Completed\n\n"
        f"**Final Title:**\n> {test_act.title}\n\n"
        f"**Final Summary:**\n> {test_act.summary}"  # Removed trailing \n due to .strip()
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
        "### Preview of Edited Content:\n\n"  # Removed leading \n due to .strip()
        "**Edited Title:**\n"
        "> Edited Title\n\n"
        "**Edited Summary:**\n"
        "> Edited Summary"  # Removed trailing \n due to .strip()
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
