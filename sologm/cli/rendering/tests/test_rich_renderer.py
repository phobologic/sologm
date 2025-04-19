"""Tests for the RichRenderer class."""

# Add necessary imports
from typing import List  # Added for Interpretation list type hint
from unittest.mock import MagicMock

import pytest
from rich.console import Console
from rich.panel import Panel  # Import Panel for assertion

from sologm.cli.rendering.rich_renderer import RichRenderer
from sologm.models.act import Act  # <-- Added import
from sologm.models.dice import DiceRoll
from sologm.models.event import Event  # <-- Added import
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet  # <-- Added import
from sologm.models.scene import Scene


# Add mock_console fixture if not already present globally
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width for consistent testing if needed
    console.width = 100
    return console


# --- Adapted Test (Red Phase - Expecting Failure) ---
def test_display_dice_roll(mock_console: MagicMock, test_dice_roll: DiceRoll):
    """Test displaying a dice roll using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call will raise NotImplementedError initially, causing the test to fail.
    renderer.display_dice_roll(test_dice_roll)

    # This assertion will only be reached once the implementation is added (Green Phase).
    mock_console.print.assert_called()
    # Verify that a Panel object was printed
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- End Tests for display_scene_info ---


# --- Tests for display_interpretation_set (Moved & Adapted) ---


def test_display_interpretation_set(
    mock_console: MagicMock, test_interpretation_set: InterpretationSet
):
    """Test displaying an interpretation set using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation_set(test_interpretation_set)

    # Assertions will run after implementation
    # Expect calls for context panel (if show_context=True), each interpretation, and instruction panel
    assert (
        mock_console.print.call_count
        >= len(test_interpretation_set.interpretations) + 2
    )


def test_display_interpretation_set_no_context(
    mock_console: MagicMock, test_interpretation_set: InterpretationSet
):
    """Test displaying an interpretation set without context using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation_set(test_interpretation_set, show_context=False)

    # Assertions will run after implementation
    # Expect calls for each interpretation and instruction panel
    assert (
        mock_console.print.call_count
        == len(test_interpretation_set.interpretations) + 1
    )


# --- End Tests for display_interpretation_set ---


# --- Tests for display_interpretation_status (Moved & Adapted) ---


def test_display_interpretation_status(
    mock_console: MagicMock, test_interpretation_set: InterpretationSet
):
    """Test displaying interpretation status using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation_status(test_interpretation_set)

    # Assertions will run after implementation
    # Expecting two prints: one for the panel, one for the trailing newline
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert len(args2) == 0  # Second call is just print()


# --- End Tests for display_interpretation_status ---


# --- Tests for display_interpretation_sets_table (Moved & Adapted) ---


def test_display_interpretation_sets_table(
    mock_console: MagicMock, test_interpretation_set: InterpretationSet
):
    """Test displaying interpretation sets table using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # Create a list with just the test interpretation set
    interp_sets = [test_interpretation_set]

    # This call should fail with NotImplementedError initially
    renderer.display_interpretation_sets_table(interp_sets)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


# --- End Tests for display_interpretation_sets_table ---


# --- Tests for display_acts_table (Moved & Adapted) ---


def test_display_acts_table_with_acts(mock_console: MagicMock, test_act: Act):
    """Test displaying acts table with acts using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_acts_table([test_act], test_act.id)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


def test_display_acts_table_no_acts(mock_console: MagicMock):
    """Test displaying acts table with no acts using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_acts_table([], None)

    # Assertions will run after implementation
    mock_console.print.assert_called_once_with(
        "No acts found. Create one with 'sologm act create'."
    )


# --- End Tests for display_acts_table ---


# --- Tests for display_scenes_table (Moved & Adapted) ---


def test_display_scenes_table_with_scenes(mock_console: MagicMock, test_scene: Scene):
    """Test displaying scenes table with scenes using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_scenes_table([test_scene], test_scene.id)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


def test_display_scenes_table_no_scenes(mock_console: MagicMock):
    """Test displaying scenes table with no scenes using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_scenes_table([], None)

    # Assertions will run after implementation
    mock_console.print.assert_called_once_with(
        "No scenes found. Create one with 'sologm scene create'."
    )


# --- End Tests for display_scenes_table ---


# --- Tests for display_events_table (Moved & Adapted) ---


def test_display_events_table_with_events(
    mock_console: MagicMock, test_events: List[Event], test_scene: Scene
):
    """Test displaying events table with events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_events_table(test_events, test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


def test_display_events_table_with_truncation(
    mock_console: MagicMock, test_events: List[Event], test_scene: Scene
):
    """Test displaying events table with truncated descriptions using RichRenderer."""
    renderer = RichRenderer(mock_console)

    # Test with truncation enabled (default)
    renderer.display_events_table(
        test_events, test_scene, max_description_length=20
    )  # Pass max_length
    mock_console.print.assert_called_once()
    args1, _ = mock_console.print.call_args
    assert isinstance(args1[0], Panel)
    mock_console.reset_mock()  # Reset for the next call

    # Test with truncation disabled
    renderer.display_events_table(test_events, test_scene, truncate_descriptions=False)
    mock_console.print.assert_called_once()
    args2, _ = mock_console.print.call_args
    assert isinstance(args2[0], Panel)


def test_display_events_table_no_events(mock_console: MagicMock, test_scene: Scene):
    """Test displaying events table with no events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_events_table([], test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once_with(
        f"\nNo events in scene '{test_scene.title}'"
    )


# --- End Tests for display_events_table ---


# --- Tests for display_interpretation (Moved & Adapted) ---


def test_display_interpretation(
    mock_console: MagicMock, test_interpretations: List[Interpretation]
):
    """Test displaying an interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation(test_interpretations[0])

    # Assertions will run after implementation
    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


def test_display_interpretation_selected(
    mock_console: MagicMock, test_interpretations: List[Interpretation]
):
    """Test displaying a selected interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_interpretation(test_interpretations[0], selected=True)

    # Assertions will run after implementation
    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


# --- Add other tests below ---


# --- Tests for display_act_ai_generation_results (Moved & Adapted) ---

def test_display_act_ai_generation_results(mock_console: MagicMock, test_act: Act):
    """Test displaying AI generation results for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)

    # Test with both title and summary
    results_both = {"title": "AI Generated Title", "summary": "AI Generated Summary"}
    # This call should fail with NotImplementedError initially
    renderer.display_act_ai_generation_results(results_both, test_act)
    # Assertions will run after implementation
    assert mock_console.print.call_count >= 2 # At least title and summary panels
    mock_console.reset_mock()

    # Test with only title
    results_title = {"title": "AI Generated Title"}
    renderer.display_act_ai_generation_results(results_title, test_act)
    assert mock_console.print.call_count >= 1 # At least title panel
    mock_console.reset_mock()

    # Test with only summary
    results_summary = {"summary": "AI Generated Summary"}
    renderer.display_act_ai_generation_results(results_summary, test_act)
    assert mock_console.print.call_count >= 1 # At least summary panel
    mock_console.reset_mock()

    # Test with empty results
    results_empty = {}
    renderer.display_act_ai_generation_results(results_empty, test_act)
    # No panels should be printed if results are empty
    assert mock_console.print.call_count == 0
    mock_console.reset_mock()

    # Test with existing content for comparison
    test_act.title = "Existing Title"
    test_act.summary = "Existing Summary"
    results_compare = {"title": "AI Generated Title", "summary": "AI Generated Summary"}
    renderer.display_act_ai_generation_results(results_compare, test_act)
    # Expect 4 panels: AI title, existing title, AI summary, existing summary
    assert mock_console.print.call_count == 4
    args_list = mock_console.print.call_args_list
    assert isinstance(args_list[0][0][0], Panel) # AI Title
    assert isinstance(args_list[1][0][0], Panel) # Existing Title
    assert isinstance(args_list[2][0][0], Panel) # AI Summary
    assert isinstance(args_list[3][0][0], Panel) # Existing Summary


# --- End Tests for display_act_ai_generation_results ---


# --- Tests for display_act_completion_success (Moved & Adapted) ---

def test_display_act_completion_success(mock_console: MagicMock, test_act: Act):
    """Test displaying act completion success using RichRenderer."""
    renderer = RichRenderer(mock_console)

    # Test with title and summary
    # This call should fail with NotImplementedError initially
    renderer.display_act_completion_success(test_act)
    # Assertions will run after implementation
    assert mock_console.print.call_count >= 3 # Title message, metadata, title, summary

    mock_console.reset_mock()
    # Test with untitled act
    test_act_untitled = Act(
        id="act-untitled",
        game_id=test_act.game_id,
        sequence=test_act.sequence,
        title=None, # No title
        summary="Summary only",
        is_active=False,
        # Add created_at and modified_at if needed by the method
        created_at=test_act.created_at,
        modified_at=test_act.modified_at,
    )
    renderer.display_act_completion_success(test_act_untitled)
    assert mock_console.print.call_count >= 2 # Title message, metadata, summary (no title print)


# --- End Tests for display_act_completion_success ---


# --- Tests for display_act_ai_feedback_prompt (Moved & Adapted) ---

from unittest.mock import patch # Import patch

@patch('rich.prompt.Prompt.ask') # Patch Prompt.ask
def test_display_act_ai_feedback_prompt(mock_ask: MagicMock, mock_console: MagicMock):
    """Test displaying AI feedback prompt for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)

    # Mock the Prompt.ask method to return a fixed value
    mock_ask.return_value = "A"

    # This call should fail with NotImplementedError initially
    # Note: The original function took console, the Renderer method doesn't need it
    # in the signature as it uses self.console, but the base class requires it.
    # We pass self.console here to match the base class signature for now.
    # This might be refined later if the base class signature changes.
    result = renderer.display_act_ai_feedback_prompt(renderer.console)

    # Assertions will run after implementation
    assert result == "A"
    mock_ask.assert_called_once() # Verify Prompt.ask was called


# --- End Tests for display_act_ai_feedback_prompt ---


# --- Tests for display_game_info (Moved & Adapted) ---


def test_display_game_info(mock_console: MagicMock, test_game: Game, test_scene: Scene):
    """Test displaying game info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_game_info(test_game, test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


def test_display_game_info_no_scene(mock_console: MagicMock, test_game: Game):
    """Test displaying game info without active scene using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_game_info(test_game, None)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- End Tests for display_game_info ---


# --- Tests for display_act_info (Moved & Adapted) ---


def test_display_act_info(mock_console: MagicMock, test_act: Act, test_game: Game):
    """Test displaying act info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_act_info(test_act, test_game.name)

    # Assertions will run after implementation
    # Expecting two prints: one for the main act panel, one for the scenes panel/table
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert isinstance(args2[0], Panel)


# --- End Tests for display_act_info ---


# --- Tests for display_games_table (Moved & Adapted) ---


def test_display_games_table_with_games(mock_console: MagicMock, test_game: Game):
    """Test displaying games table with games using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_games_table([test_game], test_game)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


def test_display_games_table_no_games(mock_console: MagicMock):
    """Test displaying games table with no games using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_games_table([], None)

    # Assertions will run after implementation
    mock_console.print.assert_called_once_with(
        "No games found. Create one with 'sologm game create'."
    )


# --- End Tests for display_games_table ---


# --- Tests for display_scene_info (Moved & Adapted) ---


def test_display_scene_info(mock_console: MagicMock, test_scene: Scene):
    """Test displaying scene info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with NotImplementedError initially
    renderer.display_scene_info(test_scene)

    # Assertions will run after implementation
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
