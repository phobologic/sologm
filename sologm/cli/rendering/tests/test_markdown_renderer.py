"""
Unit tests for the MarkdownRenderer class.
"""

from unittest.mock import MagicMock

import pytest
from rich.console import Console  # <-- Import Console

# Import the renderer and models needed for tests
from typing import List  # <-- Added import

# Import the renderer and models needed for tests
from sologm.cli.rendering.markdown_renderer import MarkdownRenderer
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game  # <-- Added import
from sologm.models.oracle import Interpretation
from sologm.models.scene import Scene


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
    test_game.acts = [test_scene.act]  # Assuming test_scene has an act
    test_game.scenes = [test_scene]

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


# --- Add other tests below ---
