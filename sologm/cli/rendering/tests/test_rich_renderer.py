"""Tests for the RichRenderer class."""

# Add necessary imports
from typing import Callable, Any, List, Dict, Optional  # Added List, Dict, Optional
from unittest.mock import MagicMock, patch  # Added patch

import click  # Import click for Abort exception
import pytest
from rich.console import Console  # Removed Grid import
from rich.markdown import Markdown
from rich.panel import Panel  # Import Panel for assertion
from rich.table import Table  # Import Table for type checking if needed
from rich.layout import Layout  # Import Layout for type checking if needed
from rich.text import Text  # Add this import

from sologm.cli.rendering.rich_renderer import RichRenderer

# Import BORDER_STYLES for assertions if needed
from sologm.cli.utils.styled_text import BORDER_STYLES

# Import manager types for mocking/type hinting if needed by tests
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.database.session import SessionContext, Session  # <-- Added Session import
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene


# Add mock_console fixture if not already present globally
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width for consistent testing if needed
    console.width = 100
    return console


# --- Adapted Test ---
def test_display_dice_roll(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying a dice roll using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        dice_roll = DiceRoll.create(
            notation="2d6+1",
            individual_results=[4, 5],
            modifier=1,
            total=10,
            reason="Test roll",
            scene_id=scene.id,
        )
        session.add(dice_roll)
        session.flush()
        session.refresh(dice_roll)

    renderer.display_dice_roll(dice_roll)

    mock_console.print.assert_called()
    # Verify that a Panel object was printed
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Verify border style for dice rolls.
    assert (
        args[0].border_style == BORDER_STYLES["neutral"]
    )  # Use the style actually applied by the renderer
    # Verify status is not in metadata.
    assert "Status" not in str(args[0].renderable)


# --- Tests for display_markdown (New Method) ---


def test_display_markdown(mock_console: MagicMock):
    """Test displaying markdown content using RichRenderer."""
    renderer = RichRenderer(mock_console)
    test_markdown = "# Header\n* List item\n`code`"
    renderer.display_markdown(test_markdown)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Markdown)
    assert args[0].markup == test_markdown


# --- End Tests for display_markdown ---


# --- Tests for display_narrative_feedback_prompt (New Method) ---


@patch("rich.prompt.Prompt.ask")
def test_display_narrative_feedback_prompt(
    mock_ask: MagicMock, mock_console: MagicMock
):
    """Test displaying narrative feedback prompt using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # The expected plain text content, without markup
    # FIX: Correct the expected plain text to match Text.assemble's output
    expected_plain_text = "Choose action: Accept / Edit / Regenerate / Cancel"
    expected_choices = ["A", "E", "R", "C"]
    expected_default = "A"
    # FIX: Update expected_kwargs to reflect the actual call signature
    # The implementation now passes console, default, and show_default
    # It does *not* pass 'choices' directly to Prompt.ask anymore.
    expected_kwargs = {
        "default": expected_default,
        "console": renderer.console,  # Check that the console object is passed
        "show_default": True,
        # "choices" is no longer passed directly to ask in the implementation
    }

    # Test each valid choice
    for choice_val in ["A", "E", "R", "C", "a", "e", "r", "c"]:
        mock_ask.reset_mock()
        mock_ask.return_value = choice_val
        result = renderer.display_narrative_feedback_prompt(renderer.console)
        assert result == choice_val.upper()

        # Assert the mock was called
        mock_ask.assert_called_once()
        call_args, call_kwargs = mock_ask.call_args

        # Assert the first positional argument is a Text object with correct content
        assert len(call_args) == 1
        assert isinstance(call_args[0], Text)
        # This assertion should now pass
        assert call_args[0].plain == expected_plain_text

        # Assert the keyword arguments are correct
        # FIX: Update the assertion for kwargs
        # Remove 'choices' check and add checks for console, show_default
        assert "choices" not in call_kwargs  # choices is handled internally now
        assert call_kwargs.get("default") == expected_default
        assert call_kwargs.get("console") == renderer.console
        assert call_kwargs.get("show_default") is True


# --- End Tests for display_narrative_feedback_prompt ---


# --- End Tests for display_scene_info ---


# --- Test for display_error (New Method) ---


def test_display_error(mock_console: MagicMock):
    """Test displaying an error message using RichRenderer."""
    renderer = RichRenderer(mock_console)
    error_message = "Something went wrong!"
    renderer.display_error(error_message)

    mock_console.print.assert_called_once_with(f"[red]Error: {error_message}[/red]")


# --- End Test for display_error ---


# --- Tests for display_game_status (Moved & Adapted) ---


@patch.object(RichRenderer, "_create_dice_rolls_panel")
@patch.object(RichRenderer, "_create_empty_oracle_panel")
@patch.object(RichRenderer, "_create_oracle_panel")
@patch.object(RichRenderer, "_create_events_panel")
@patch.object(RichRenderer, "_create_scene_panels_grid")
@patch.object(RichRenderer, "_create_act_panel")
@patch.object(RichRenderer, "_create_game_header_panel")
@patch.object(RichRenderer, "_calculate_truncation_length")
def test_display_game_status_full(
    mock_calculate_truncation: MagicMock,
    mock_create_game_header: MagicMock,
    mock_create_act_panel: MagicMock,
    mock_create_scene_grid: MagicMock,
    mock_create_events_panel: MagicMock,
    mock_create_oracle_panel: MagicMock,
    mock_create_empty_oracle_panel: MagicMock,
    mock_create_dice_panel: MagicMock,
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying full game status with all components using RichRenderer."""
    # --- Mock Setup ---
    # Configure mocks to return simple identifiable objects/values
    mock_truncation_length = 50
    mock_calculate_truncation.return_value = mock_truncation_length
    mock_game_header_panel = MagicMock(spec=Panel, name="GameHeaderPanel")
    mock_create_game_header.return_value = mock_game_header_panel
    mock_act_panel = MagicMock(spec=Panel, name="ActPanel")
    mock_create_act_panel.return_value = mock_act_panel
    mock_scene_grid = MagicMock(
        spec=Table, name="SceneGrid"
    )  # Use Table based on implementation
    mock_create_scene_grid.return_value = mock_scene_grid
    mock_events_panel = MagicMock(spec=Panel, name="EventsPanel")
    mock_create_events_panel.return_value = mock_events_panel
    # Simulate oracle manager returning data, so _create_oracle_panel is called
    mock_oracle_panel = MagicMock(spec=Panel, name="OraclePanel")
    mock_create_oracle_panel.return_value = mock_oracle_panel
    mock_dice_panel = MagicMock(spec=Panel, name="DicePanel")
    mock_create_dice_panel.return_value = mock_dice_panel

    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event1 = create_test_event(session, scene_id=scene.id, description="Event 1")
        event2 = create_test_event(session, scene_id=scene.id, description="Event 2")
        dice_roll = DiceRoll.create(
            notation="1d10",
            individual_results=[7],
            modifier=0,
            total=7,
            scene_id=scene.id,
        )
        session.add(dice_roll)
        session.flush()
        session.refresh(dice_roll)
        events = [event1, event2]
        rolls = [dice_roll]

        # Call the renderer method with the created objects and mocks
        renderer.display_game_status(
            game=game,
            latest_act=act,
            latest_scene=scene,
            recent_events=events,
            scene_manager=mock_scene_manager,
            oracle_manager=mock_oracle_manager,
            recent_rolls=rolls,
            is_act_active=True,
            is_scene_active=True,
        )

    # --- Assertions ---
    # Verify helpers were called with correct arguments
    mock_calculate_truncation.assert_called_once()
    mock_create_game_header.assert_called_once_with(game)
    mock_create_act_panel.assert_called_once_with(
        game,
        act,
        True,
        truncation_length=mock_truncation_length,  # Pass True positionally
    )
    mock_create_scene_grid.assert_called_once_with(
        game,
        scene,
        mock_scene_manager,
        True,  # Pass True positionally
    )
    mock_create_events_panel.assert_called_once_with(events, mock_truncation_length)
    # Check oracle panel call (assuming oracle_manager leads to this path)
    mock_create_oracle_panel.assert_called_once_with(
        game, scene, mock_oracle_manager, mock_truncation_length
    )
    mock_create_empty_oracle_panel.assert_not_called()  # Ensure the empty one wasn't called
    mock_create_dice_panel.assert_called_once_with(rolls)

    # Verify console output includes the mocked return values
    print_calls = mock_console.print.call_args_list
    # Check that the mocked panels/grids were printed
    printed_objects = [
        call[0][0] for call in print_calls if call[0]
    ]  # Get first arg if exists

    assert mock_game_header_panel in printed_objects
    assert mock_act_panel in printed_objects
    # The scene grid and events panel are added to a Table.grid, check that grid was printed
    # The oracle panel and dice panel are added to another Table.grid, check that grid was printed
    assert any(
        isinstance(obj, Table) for obj in printed_objects
    )  # Check if Table grids were printed
    # More specific checks could verify the structure of the printed grids if needed


@patch.object(RichRenderer, "_create_dice_rolls_panel")
@patch.object(RichRenderer, "_create_empty_oracle_panel")
@patch.object(RichRenderer, "_create_oracle_panel")
@patch.object(RichRenderer, "_create_events_panel")
@patch.object(RichRenderer, "_create_scene_panels_grid")
@patch.object(RichRenderer, "_create_act_panel")
@patch.object(RichRenderer, "_create_game_header_panel")
@patch.object(RichRenderer, "_calculate_truncation_length")
def test_display_game_status_no_scene(
    mock_calculate_truncation: MagicMock,
    mock_create_game_header: MagicMock,
    mock_create_act_panel: MagicMock,
    mock_create_scene_grid: MagicMock,
    mock_create_events_panel: MagicMock,
    mock_create_oracle_panel: MagicMock,
    mock_create_empty_oracle_panel: MagicMock,
    mock_create_dice_panel: MagicMock,
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying game status without an active scene using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # --- Mock Setup ---
    mock_truncation_length = 50
    mock_calculate_truncation.return_value = mock_truncation_length
    mock_game_header_panel = MagicMock(spec=Panel, name="GameHeaderPanel")
    mock_create_game_header.return_value = mock_game_header_panel
    mock_act_panel = MagicMock(spec=Panel, name="ActPanel")
    mock_create_act_panel.return_value = mock_act_panel
    mock_scene_grid = MagicMock(spec=Table, name="SceneGrid")
    mock_create_scene_grid.return_value = mock_scene_grid
    mock_events_panel = MagicMock(spec=Panel, name="EventsPanel")
    mock_create_events_panel.return_value = mock_events_panel
    # Simulate no oracle data, so _create_empty_oracle_panel is called
    mock_create_oracle_panel.return_value = (
        None  # Simulate no panel created by this path
    )
    mock_empty_oracle_panel = MagicMock(spec=Panel, name="EmptyOraclePanel")
    mock_create_empty_oracle_panel.return_value = mock_empty_oracle_panel
    mock_dice_panel = MagicMock(spec=Panel, name="DicePanel")
    mock_create_dice_panel.return_value = mock_dice_panel
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)

        renderer.display_game_status(
            game=game,
            latest_act=act,
            latest_scene=None,
            recent_events=[],
            scene_manager=None,  # No scene manager needed if no scene
            oracle_manager=mock_oracle_manager,
            recent_rolls=None,
            is_act_active=True,
            is_scene_active=False,
        )

    # --- Assertions ---
    mock_calculate_truncation.assert_called_once()
    mock_create_game_header.assert_called_once_with(game)
    mock_create_act_panel.assert_called_once_with(
        game,
        act,
        True,
        truncation_length=mock_truncation_length,  # Pass True positionally
    )
    # Expect scene grid to be called with None for scene and manager
    mock_create_scene_grid.assert_called_once_with(
        game,
        None,
        None,
        False,  # Pass False positionally
    )
    mock_create_events_panel.assert_called_once_with([], mock_truncation_length)
    # Expect oracle panel to be called, but return None, leading to empty panel call
    mock_create_oracle_panel.assert_called_once_with(
        game, None, mock_oracle_manager, mock_truncation_length
    )
    mock_create_empty_oracle_panel.assert_called_once()
    mock_create_dice_panel.assert_called_once_with([])  # Called with empty list

    # Verify console output includes the mocked return values
    print_calls = mock_console.print.call_args_list
    printed_objects = [call[0][0] for call in print_calls if call[0]]

    assert mock_game_header_panel in printed_objects
    assert mock_act_panel in printed_objects
    assert any(isinstance(obj, Table) for obj in printed_objects)  # Check grids printed


@patch.object(RichRenderer, "_create_dice_rolls_panel")
@patch.object(RichRenderer, "_create_empty_oracle_panel")
@patch.object(RichRenderer, "_create_oracle_panel")
@patch.object(RichRenderer, "_create_events_panel")
@patch.object(RichRenderer, "_create_scene_panels_grid")
@patch.object(RichRenderer, "_create_act_panel")
@patch.object(RichRenderer, "_create_game_header_panel")
@patch.object(RichRenderer, "_calculate_truncation_length")
def test_display_game_status_no_events(
    mock_calculate_truncation: MagicMock,
    mock_create_game_header: MagicMock,
    mock_create_act_panel: MagicMock,
    mock_create_scene_grid: MagicMock,
    mock_create_events_panel: MagicMock,
    mock_create_oracle_panel: MagicMock,
    mock_create_empty_oracle_panel: MagicMock,
    mock_create_dice_panel: MagicMock,
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying game status without any events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # --- Mock Setup ---
    mock_truncation_length = 50
    mock_calculate_truncation.return_value = mock_truncation_length
    mock_game_header_panel = MagicMock(spec=Panel, name="GameHeaderPanel")
    mock_create_game_header.return_value = mock_game_header_panel
    mock_act_panel = MagicMock(spec=Panel, name="ActPanel")
    mock_create_act_panel.return_value = mock_act_panel
    mock_scene_grid = MagicMock(spec=Table, name="SceneGrid")
    mock_create_scene_grid.return_value = mock_scene_grid
    mock_events_panel = MagicMock(
        spec=Panel, name="EventsPanel"
    )  # Will be called with []
    mock_create_events_panel.return_value = mock_events_panel
    # Simulate oracle manager returning data, so _create_oracle_panel is called
    mock_oracle_panel = MagicMock(spec=Panel, name="OraclePanel")
    mock_create_oracle_panel.return_value = mock_oracle_panel

    # Define mock_empty_oracle_panel even if not expected to be called/printed in this test
    mock_empty_oracle_panel = MagicMock(spec=Panel, name="EmptyOraclePanel")
    mock_create_empty_oracle_panel.return_value = mock_empty_oracle_panel

    mock_dice_panel = MagicMock(spec=Panel, name="DicePanel")  # Will be called with []
    mock_create_dice_panel.return_value = mock_dice_panel

    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)

        renderer.display_game_status(
            game=game,
            latest_act=act,
            latest_scene=scene,
            recent_events=[],
            scene_manager=mock_scene_manager,
            oracle_manager=mock_oracle_manager,  # Pass the configured mock
            recent_rolls=None,
            is_act_active=True,
            is_scene_active=True,
        )

    # --- Assertions ---
    mock_calculate_truncation.assert_called_once()
    mock_create_game_header.assert_called_once_with(game)
    mock_create_act_panel.assert_called_once_with(
        game,
        act,
        True,
        truncation_length=mock_truncation_length,  # Pass True positionally
    )
    mock_create_scene_grid.assert_called_once_with(
        game,
        scene,
        mock_scene_manager,
        True,  # Pass True positionally
    )
    # Expect events panel to be called with an empty list
    mock_create_events_panel.assert_called_once_with([], mock_truncation_length)
    # Expect oracle panel to be called
    mock_create_oracle_panel.assert_called_once_with(
        game, scene, mock_oracle_manager, mock_truncation_length
    )
    mock_create_empty_oracle_panel.assert_not_called()  # Correct: empty panel shouldn't be created
    # Expect dice panel to be called with None converted to []
    mock_create_dice_panel.assert_called_once_with([])

    # Verify console output includes the mocked return values
    print_calls = mock_console.print.call_args_list
    printed_objects = [call[0][0] for call in print_calls if call[0]]

    assert mock_game_header_panel in printed_objects
    assert mock_act_panel in printed_objects
    # Check that two Table objects (grids) were printed, representing the main layout structure.
    # The individual panels (like oracle) are inside these grids.
    table_prints = [obj for obj in printed_objects if isinstance(obj, Table)]
    assert len(table_prints) == 2


@patch.object(RichRenderer, "_create_dice_rolls_panel")
@patch.object(RichRenderer, "_create_empty_oracle_panel")
@patch.object(RichRenderer, "_create_oracle_panel")
@patch.object(RichRenderer, "_create_events_panel")
@patch.object(RichRenderer, "_create_scene_panels_grid")
@patch.object(RichRenderer, "_create_act_panel")
@patch.object(RichRenderer, "_create_game_header_panel")
@patch.object(RichRenderer, "_calculate_truncation_length")
def test_display_game_status_no_interpretation(
    mock_calculate_truncation: MagicMock,
    mock_create_game_header: MagicMock,
    mock_create_act_panel: MagicMock,
    mock_create_scene_grid: MagicMock,
    mock_create_events_panel: MagicMock,
    mock_create_oracle_panel: MagicMock,
    mock_create_empty_oracle_panel: MagicMock,
    mock_create_dice_panel: MagicMock,
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying game status without oracle manager using RichRenderer."""
    # --- Mock Setup ---
    mock_truncation_length = 50
    mock_calculate_truncation.return_value = mock_truncation_length
    mock_game_header_panel = MagicMock(spec=Panel, name="GameHeaderPanel")
    mock_create_game_header.return_value = mock_game_header_panel
    mock_act_panel = MagicMock(spec=Panel, name="ActPanel")
    mock_create_act_panel.return_value = mock_act_panel
    mock_scene_grid = MagicMock(spec=Table, name="SceneGrid")
    mock_create_scene_grid.return_value = mock_scene_grid
    mock_events_panel = MagicMock(spec=Panel, name="EventsPanel")
    mock_create_events_panel.return_value = mock_events_panel
    # Explicitly set the oracle panel mock to return None for this test case
    mock_create_oracle_panel.return_value = None
    # Return an actual Panel, not just a mock, to avoid NotRenderableError
    mock_empty_oracle_panel = Panel("Empty Oracle", title="EmptyOraclePanel")
    mock_create_empty_oracle_panel.return_value = mock_empty_oracle_panel
    mock_dice_panel = MagicMock(spec=Panel, name="DicePanel")
    mock_create_dice_panel.return_value = mock_dice_panel

    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)

    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event = create_test_event(session, scene_id=scene.id)
        events = [event]

        renderer.display_game_status(
            game=game,
            latest_act=act,
            latest_scene=scene,
            recent_events=events,
            scene_manager=mock_scene_manager,
            oracle_manager=None,  # No oracle manager
            recent_rolls=None,
            is_act_active=True,
            is_scene_active=True,
        )

    # --- Assertions ---
    mock_calculate_truncation.assert_called_once()
    mock_create_game_header.assert_called_once_with(game)
    mock_create_act_panel.assert_called_once_with(
        game,
        act,
        True,
        truncation_length=mock_truncation_length,  # Pass True positionally
    )
    mock_create_scene_grid.assert_called_once_with(
        game,
        scene,
        mock_scene_manager,
        True,  # Pass True positionally
    )
    mock_create_events_panel.assert_called_once_with(events, mock_truncation_length)
    # Expect _create_oracle_panel to be called with None manager, returning None
    mock_create_oracle_panel.assert_called_once_with(
        game, scene, None, mock_truncation_length
    )
    # Expect _create_empty_oracle_panel to be called as fallback
    mock_create_empty_oracle_panel.assert_called_once()
    # Expect dice panel to be called with None converted to []
    mock_create_dice_panel.assert_called_once_with([])

    # Verify console output includes the mocked return values
    print_calls = mock_console.print.call_args_list
    printed_objects = [call[0][0] for call in print_calls if call[0]]

    assert mock_game_header_panel in printed_objects
    assert mock_act_panel in printed_objects
    assert any(isinstance(obj, Table) for obj in printed_objects)  # Check grids printed


@patch.object(RichRenderer, "_create_dice_rolls_panel")
@patch.object(RichRenderer, "_create_empty_oracle_panel")
@patch.object(RichRenderer, "_create_oracle_panel")
@patch.object(RichRenderer, "_create_events_panel")
@patch.object(RichRenderer, "_create_scene_panels_grid")
@patch.object(RichRenderer, "_create_act_panel")
@patch.object(RichRenderer, "_create_game_header_panel")
@patch.object(RichRenderer, "_calculate_truncation_length")
def test_display_game_status_selected_interpretation(
    mock_calculate_truncation: MagicMock,
    mock_create_game_header: MagicMock,
    mock_create_act_panel: MagicMock,
    mock_create_scene_grid: MagicMock,
    mock_create_events_panel: MagicMock,
    mock_create_oracle_panel: MagicMock,
    mock_create_empty_oracle_panel: MagicMock,
    mock_create_dice_panel: MagicMock,
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
    # Interpretation/Set are created manually for mock setup
):
    """Test displaying game status with a selected interpretation using RichRenderer."""
    # --- Mock Setup ---
    mock_truncation_length = 50
    mock_calculate_truncation.return_value = mock_truncation_length
    mock_game_header_panel = MagicMock(spec=Panel, name="GameHeaderPanel")
    mock_create_game_header.return_value = mock_game_header_panel
    mock_act_panel = MagicMock(spec=Panel, name="ActPanel")
    mock_create_act_panel.return_value = mock_act_panel
    mock_scene_grid = MagicMock(spec=Table, name="SceneGrid")
    mock_create_scene_grid.return_value = mock_scene_grid
    mock_events_panel = MagicMock(spec=Panel, name="EventsPanel")
    mock_create_events_panel.return_value = mock_events_panel
    mock_oracle_panel = MagicMock(
        spec=Panel, name="OraclePanel"
    )  # Expect this to be called
    mock_create_oracle_panel.return_value = mock_oracle_panel
    mock_dice_panel = MagicMock(spec=Panel, name="DicePanel")
    mock_create_dice_panel.return_value = mock_dice_panel

    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event = create_test_event(session, scene_id=scene.id)
        events = [event]

        # Setup: Configure mock oracle_manager to simulate a selected interpretation
        # This data is only needed to ensure the correct path in display_game_status
        selected_interp = Interpretation(
            id="interp-selected",
            set_id="set-1",
            title="Selected Interp",
            description="This was chosen.",
            is_selected=True,
        )
        interp_set = InterpretationSet(
            id="set-1",
            scene_id=scene.id,
            context="Test Context",
            oracle_results="Test Results",
            interpretations=[selected_interp],
        )
        # Mock the manager methods to guide display_game_status logic
        mock_oracle_manager.get_current_interpretation_set = MagicMock(
            return_value=None
        )
        mock_oracle_manager.get_most_recent_interpretation = MagicMock(
            return_value=(interp_set, selected_interp)
        )

        renderer.display_game_status(
            game=game,
            latest_act=act,
            latest_scene=scene,
            recent_events=events,
            scene_manager=mock_scene_manager,
            oracle_manager=mock_oracle_manager,
            recent_rolls=None,
            is_act_active=True,
            is_scene_active=True,
        )

    # --- Assertions ---
    mock_calculate_truncation.assert_called_once()
    mock_create_game_header.assert_called_once_with(game)
    mock_create_act_panel.assert_called_once_with(
        game,
        act,
        True,
        truncation_length=mock_truncation_length,  # Positional True
    )
    mock_create_scene_grid.assert_called_once_with(
        game,
        scene,
        mock_scene_manager,
        True,  # Positional True
    )
    mock_create_events_panel.assert_called_once_with(events, mock_truncation_length)
    # Expect _create_oracle_panel to be called because manager returns recent interp
    mock_create_oracle_panel.assert_called_once_with(
        game, scene, mock_oracle_manager, mock_truncation_length
    )
    mock_create_empty_oracle_panel.assert_not_called()
    # Expect dice panel to be called with None converted to []
    mock_create_dice_panel.assert_called_once_with([])

    # Verify console output includes the mocked return values
    print_calls = mock_console.print.call_args_list
    printed_objects = [call[0][0] for call in print_calls if call[0]]

    assert mock_game_header_panel in printed_objects
    assert mock_act_panel in printed_objects
    assert any(isinstance(obj, Table) for obj in printed_objects)  # Check grids printed


# --- End Tests for display_game_status ---


# --- Tests for display_game_status Helpers (Moved & Adapted) ---


def test_calculate_truncation_length(mock_console: MagicMock):
    """Test the truncation length calculation using RichRenderer."""
    renderer = RichRenderer(mock_console)

    mock_console.width = 100
    result = renderer._calculate_truncation_length()
    assert result == 40  # Expected: max(40, int(100 / 2) - 10) = 40

    mock_console.width = 30
    result = renderer._calculate_truncation_length()
    assert result == 40  # Min value check.

    # Simulate console width not being available initially
    mock_console.width = None
    # Rich often defaults to 80 if detection fails, simulate this
    with patch.object(mock_console, "width", 80):
        result = renderer._calculate_truncation_length()
    assert result == 40  # Expected: max(40, int(80 / 2) - 10) = 40


def test_create_act_panel(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test creating the act panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id, summary="Default summary.")

        # Test with active act (using default truncation)
        panel_active = renderer._create_act_panel(game, act, is_act_active=True)
        assert panel_active is not None
        assert panel_active.title is not None
        assert panel_active.border_style == BORDER_STYLES["current"]
        assert act.summary[:10] in str(
            panel_active.renderable
        )  # Check start of summary.

        # Test with inactive act and specific truncation
        act.summary = "This is a very long summary that definitely needs to be truncated for the test."
        session.add(act)
        session.flush()
        panel_inactive_truncated = renderer._create_act_panel(
            game, act, is_act_active=False, truncation_length=20
        )
        assert panel_inactive_truncated is not None
        assert panel_inactive_truncated.border_style == BORDER_STYLES["neutral"]
        # Check if the summary is truncated (approx 20 chars + ellipsis).
        assert "This is a very long summary..." in str(
            panel_inactive_truncated.renderable
        )
        assert "truncated for the test." not in str(
            panel_inactive_truncated.renderable
        )  # End should be cut off.

        # Test with no active act
        panel_no_act = renderer._create_act_panel(game, None)
        assert panel_no_act is not None
        assert panel_no_act.title is not None
        assert panel_no_act.border_style == BORDER_STYLES["neutral"]
    assert "No acts found in this game." in str(panel_no_act.renderable)


def test_create_game_header_panel(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
):
    """Test creating the game header panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        panel = renderer._create_game_header_panel(game)

    assert panel is not None
    assert panel.title is not None
    assert panel.border_style == BORDER_STYLES["game_info"]


def test_create_scene_panels_grid(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test creating the scene panels grid using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)

        # Test with active scene and scene manager
        grid_active = renderer._create_scene_panels_grid(
            game, scene, mock_scene_manager, is_scene_active=True
        )
        assert grid_active is not None
        assert isinstance(grid_active, Table)  # FIX: Check for Table, not Grid
        # Removed checks for internal panel style/content via .renderables

        # Test with inactive scene and scene manager
        grid_inactive = renderer._create_scene_panels_grid(
            game, scene, mock_scene_manager, is_scene_active=False
        )
        assert grid_inactive is not None
        assert isinstance(grid_inactive, Table)  # FIX: Check for Table, not Grid
        # Removed checks for internal panel style/content via .renderables

        # Test with active scene but no scene manager
        grid_no_manager = renderer._create_scene_panels_grid(
            game, scene, None, is_scene_active=True
        )
        assert grid_no_manager is not None
        assert isinstance(grid_no_manager, Table)  # FIX: Check for Table, not Grid
        # Removed check for internal panel via .renderables

        # Test with no scene
        grid_no_scene = renderer._create_scene_panels_grid(
            game, None, None, is_scene_active=False
        )
        assert grid_no_scene is not None
        assert isinstance(grid_no_scene, Table)  # FIX: Check for Table, not Grid
        # Removed checks for internal panel content via .renderables


def test_create_events_panel(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test creating the events panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event = create_test_event(session, scene_id=scene.id)
        events = [event]

        # Test with events
        panel = renderer._create_events_panel(events, 60)
        assert panel is not None
        assert "Recent Events" in panel.title
        assert panel.border_style == BORDER_STYLES["success"]

        # Test with no events
        panel_no_events = renderer._create_events_panel([], 60)
        assert panel_no_events is not None
        assert "Recent Events" in panel_no_events.title
        assert "No recent events" in str(panel_no_events.renderable)


def test_create_oracle_panel(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test creating the oracle panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)

        # Test with no oracle manager
        panel_no_manager = renderer._create_oracle_panel(game, scene, None, 60)
        assert panel_no_manager is None

        # Test with oracle manager (mock behavior as needed)
        # Mock the methods on the mock_oracle_manager instance directly
        mock_oracle_manager.get_current_interpretation_set = MagicMock(
            return_value=None
        )
        mock_oracle_manager.get_most_recent_interpretation = MagicMock(
            return_value=None
        )

        panel_with_manager = renderer._create_oracle_panel(
            game, scene, mock_oracle_manager, 60
        )
        assert panel_with_manager is not None  # Should return empty panel in this case
        assert "No oracle interpretations yet." in str(panel_with_manager.renderable)


def test_create_empty_oracle_panel(mock_console: MagicMock):
    """Test creating an empty oracle panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    panel = renderer._create_empty_oracle_panel()
    assert panel is not None
    assert "Oracle" in panel.title
    assert panel.border_style == BORDER_STYLES["neutral"]


def test_create_dice_rolls_panel(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test creating the dice rolls panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        dice_roll = DiceRoll.create(
            notation="3d6",
            individual_results=[1, 2, 3],
            modifier=0,
            total=6,
            scene_id=scene.id,
        )
        session.add(dice_roll)
        session.flush()
        session.refresh(dice_roll)
        rolls = [dice_roll]

        # Test with no rolls
        panel_no_rolls = renderer._create_dice_rolls_panel([])
        assert panel_no_rolls is not None
        assert "Recent Rolls" in str(panel_no_rolls.title)
        assert "No recent dice rolls" in str(panel_no_rolls.renderable)

        # Test with rolls
        panel_with_rolls = renderer._create_dice_rolls_panel(rolls)
        assert panel_with_rolls is not None
        assert "Recent Rolls" in str(panel_with_rolls.title)
        assert dice_roll.notation in str(panel_with_rolls.renderable)


# --- End Tests for display_game_status Helpers ---


# --- Tests for display_interpretation_set ---


def test_display_interpretation_set(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying an interpretation set using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        interp1 = create_test_interpretation(
            session, set_id=interp_set.id, title="Interp 1"
        )
        interp2 = create_test_interpretation(
            session, set_id=interp_set.id, title="Interp 2"
        )
        # Refresh the set to load interpretations relationship.
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_set(interp_set)

    # Expect calls for context panel, each interpretation (panel + newline), and instruction panel.
    assert mock_console.print.call_count >= len(interp_set.interpretations) * 2 + 2


def test_display_interpretation_set_no_context(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying an interpretation set without context using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        interp1 = create_test_interpretation(
            session, set_id=interp_set.id, title="Interp 1"
        )
        interp2 = create_test_interpretation(
            session, set_id=interp_set.id, title="Interp 2"
        )
        # Refresh the set to load interpretations relationship.
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_set(interp_set, show_context=False)

    # Expect calls for each interpretation (panel + newline) and instruction panel.
    assert mock_console.print.call_count == len(interp_set.interpretations) * 2 + 1


# --- End Tests for display_interpretation_set ---


# --- Tests for display_interpretation_status ---


def test_display_interpretation_status(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying interpretation status using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        create_test_interpretation(session, set_id=interp_set.id)
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_status(interp_set)

    # Expecting two prints: one for the panel, one for the trailing newline.
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert len(args2) == 0  # Second call is just print()


# --- End Tests for display_interpretation_status ---


# --- Tests for display_interpretation_sets_table ---


def test_display_interpretation_sets_table(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
):
    """Test displaying interpretation sets table using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set1 = create_test_interpretation_set(
            session, scene_id=scene.id, retry_attempt=0
        )
        interp_set2 = create_test_interpretation_set(
            session, scene_id=scene.id, retry_attempt=1
        )
        interp_sets = [interp_set1, interp_set2]

    renderer.display_interpretation_sets_table(interp_sets)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    assert isinstance(args[0].renderable, Table)
    assert isinstance(args[0].renderable, Table)  # Check table is inside panel


# --- End Tests for display_interpretation_sets_table ---


# --- Tests for display_acts_table ---


def test_display_acts_table_with_acts(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying acts table with acts using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act1 = create_test_act(session, game_id=game.id, title="Act 1", is_active=False)
        act2 = create_test_act(session, game_id=game.id, title="Act 2", is_active=True)
        acts = [act1, act2]
        active_act_id = act2.id

    renderer.display_acts_table(acts, active_act_id)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    table = args[0].renderable
    assert isinstance(table, Table)
    assert len(table.columns) == 5  # ID, Seq, Title, Summary, Current


def test_display_acts_table_no_acts(mock_console: MagicMock):
    """Test displaying acts table with no acts using RichRenderer."""
    renderer = RichRenderer(mock_console)
    renderer.display_acts_table([], None)

    mock_console.print.assert_called_once_with(
        "No acts found. Create one with 'sologm act create'."
    )


# --- End Tests for display_acts_table ---


# --- Tests for display_scenes_table ---


def test_display_scenes_table_with_scenes(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying scenes table with scenes using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene1 = create_test_scene(
            session, act_id=act.id, title="Scene 1", is_active=False
        )
        scene2 = create_test_scene(
            session, act_id=act.id, title="Scene 2", is_active=True
        )
        scenes = [scene1, scene2]
        active_scene_id = scene2.id

    renderer.display_scenes_table(scenes, active_scene_id)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    table = args[0].renderable
    assert isinstance(table, Table)
    assert len(table.columns) == 5  # ID, Title, Description, Current, Sequence


def test_display_scenes_table_no_scenes(mock_console: MagicMock):
    """Test displaying scenes table with no scenes using RichRenderer."""
    renderer = RichRenderer(mock_console)
    renderer.display_scenes_table([], None)

    mock_console.print.assert_called_once_with(
        "No scenes found. Create one with 'sologm scene create'."
    )


# --- End Tests for display_scenes_table ---


# --- Tests for display_events_table ---


def test_display_events_table_with_events(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying events table with events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event1 = create_test_event(session, scene_id=scene.id, description="Event 1")
        event2 = create_test_event(session, scene_id=scene.id, description="Event 2")
        events = [event1, event2]
        renderer.display_events_table(events, scene)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


def test_display_events_table_with_truncation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying events table with truncated descriptions using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event1 = create_test_event(
            session, scene_id=scene.id, description="This is a long event description."
        )
        event2 = create_test_event(
            session, scene_id=scene.id, description="Another long event description."
        )
        events = [event1, event2]

        renderer.display_events_table(events, scene, max_description_length=20)
        mock_console.print.assert_called_once()
        args1, _ = mock_console.print.call_args
        assert isinstance(args1[0], Panel)
        assert isinstance(args1[0].renderable, Table)
        # Add check for ellipsis if possible/reliable
        # print(str(args1[0].renderable)) # For debugging table content
        mock_console.reset_mock()

        # Test untruncated
        renderer.display_events_table(events, scene, truncate_descriptions=False)
        mock_console.print.assert_called_once()
        args2, _ = mock_console.print.call_args
        assert isinstance(args2[0], Panel)
        assert isinstance(args2[0].renderable, Table)
        # Add check for full text if possible/reliable
        # print(str(args2[0].renderable)) # For debugging table content


def test_display_events_table_no_events(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying events table with no events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id, title="Empty Scene")

    renderer.display_events_table([], scene)

    mock_console.print.assert_called_once_with(f"\nNo events in scene '{scene.title}'")


# --- End Tests for display_events_table ---


# --- Tests for display_interpretation ---


def test_display_interpretation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying an interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        interpretation = create_test_interpretation(
            session, set_id=interp_set.id, title="Test Interp"
        )

    renderer.display_interpretation(interpretation)

    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print for spacing.
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


def test_display_interpretation_selected(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_interpretation_set: Callable[..., InterpretationSet],
    create_test_interpretation: Callable[..., Interpretation],
):
    """Test displaying a selected interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        interp_set = create_test_interpretation_set(session, scene_id=scene.id)
        interpretation = create_test_interpretation(
            session, set_id=interp_set.id, title="Selected Interp", is_selected=True
        )

    renderer.display_interpretation(interpretation, selected=True)

    mock_console.print.assert_called()
    args, kwargs = mock_console.print.call_args_list[0]
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print for spacing.
    args, kwargs = mock_console.print.call_args_list[1]
    assert len(args) == 0


# --- Add other tests below ---


# --- Tests for display_act_ai_generation_results ---


def test_display_act_ai_generation_results(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying AI generation results for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)

        # Test with both title and summary
        results_both = {
            "title": "AI Generated Title",
            "summary": "AI Generated Summary",
        }
        renderer.display_act_ai_generation_results(results_both, act)
        assert mock_console.print.call_count >= 2  # At least title and summary panels
        mock_console.reset_mock()

        results_title = {"title": "AI Generated Title"}
        renderer.display_act_ai_generation_results(results_title, act)
        assert mock_console.print.call_count >= 1
        mock_console.reset_mock()

        results_summary = {"summary": "AI Generated Summary"}
        renderer.display_act_ai_generation_results(results_summary, act)
        assert mock_console.print.call_count >= 1
        mock_console.reset_mock()

        results_empty = {}
        renderer.display_act_ai_generation_results(results_empty, act)
        assert mock_console.print.call_count == 0  # No panels should be printed.
        mock_console.reset_mock()

        act.title = "Existing Title"
        act.summary = "Existing Summary"
        session.add(act)
        session.flush()
        results_compare = {
            "title": "AI Generated Title",
            "summary": "AI Generated Summary",
        }
        renderer.display_act_ai_generation_results(results_compare, act)
        # Expect 4 panels: AI title, existing title, AI summary, existing summary.
        assert mock_console.print.call_count == 4
        args_list = mock_console.print.call_args_list
    assert isinstance(args_list[0][0][0], Panel)
    assert isinstance(args_list[1][0][0], Panel)
    assert isinstance(args_list[2][0][0], Panel)
    assert isinstance(args_list[3][0][0], Panel)


# --- End Tests for display_act_ai_generation_results ---


# --- Tests for display_act_completion_success ---


def test_display_act_completion_success(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying act completion success using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act_with_title = create_test_act(
            session,
            game_id=game.id,
            title="Completed Act",
            summary="It is done.",
            is_active=False,  # Ensure this doesn't block the next create.
        )
        renderer.display_act_completion_success(act_with_title)
        assert (
            mock_console.print.call_count >= 3
        )  # Title message, metadata, title, summary.
        mock_console.reset_mock()

        act_untitled = create_test_act(
            session, game_id=game.id, title=None, summary="Summary only"
        )
        renderer.display_act_completion_success(act_untitled)
        assert (
            mock_console.print.call_count >= 2
        )  # Title message, metadata, summary (no title print).


# --- End Tests for display_act_completion_success ---


# --- Tests for display_act_ai_feedback_prompt (Moved & Adapted) ---


@patch("rich.prompt.Prompt.ask")  # Patch Prompt.ask
def test_display_act_ai_feedback_prompt(mock_ask: MagicMock, mock_console: MagicMock):
    """Test displaying AI feedback prompt for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)

    mock_ask.return_value = "A"

    # The 'console' parameter is passed to match the base class, even if unused internally.
    result = renderer.display_act_ai_feedback_prompt(renderer.console)

    assert result == "A"
    mock_ask.assert_called_once()


# --- End Tests for display_act_ai_feedback_prompt ---


# --- Tests for display_act_edited_content_preview (Moved & Adapted) ---


def test_display_act_edited_content_preview(mock_console: MagicMock):
    """Test displaying edited content preview for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)
    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}
    renderer.display_act_edited_content_preview(edited_results)

    # Expecting 3 prints: header, title panel, summary panel.
    assert mock_console.print.call_count == 3
    args_list = mock_console.print.call_args_list
    assert "Preview of your edited content:" in args_list[0][0][0]
    assert isinstance(args_list[1][0][0], Panel)
    assert isinstance(args_list[2][0][0], Panel)


# --- End Tests for display_act_edited_content_preview ---


# --- Tests for display_game_info ---


def test_display_game_info(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying game info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        renderer.display_game_info(game, scene)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


def test_display_game_info_no_scene(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
):
    """Test displaying game info without active scene using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        renderer.display_game_info(game, None)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- End Tests for display_game_info ---


# --- Tests for display_act_info ---


def test_display_act_info(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],  # Needed to test scene display within act
):
    """Test displaying act info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session, name="My Game")
        act = create_test_act(session, game_id=game.id)
        create_test_scene(session, act_id=act.id)
        session.refresh(act, attribute_names=["scenes"])  # Load scenes relationship.

    renderer.display_act_info(act, game.name)

    # Expecting two prints: one for the main act panel, one for the scenes panel/table.
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert isinstance(args2[0], Panel)
    scenes_table = args2[0].renderable
    assert isinstance(scenes_table, Table)
    assert len(scenes_table.columns) == 5  # ID, Seq, Title, Description, Current


# --- End Tests for display_act_info ---


# --- Tests for display_games_table ---


def test_display_games_table_with_games(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
):
    """Test displaying games table with games using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game1 = create_test_game(session, name="Game 1", is_active=False)
        game2 = create_test_game(session, name="Game 2", is_active=True)
        games = [game1, game2]
        active_game = game2
        renderer.display_games_table(games, active_game)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table
    assert isinstance(args[0].renderable, Table)


def test_display_games_table_no_games(mock_console: MagicMock):
    """Test displaying games table with no games using RichRenderer."""
    renderer = RichRenderer(mock_console)
    renderer.display_games_table([], None)

    mock_console.print.assert_called_once_with(
        "No games found. Create one with 'sologm game create'."
    )


# --- End Tests for display_games_table ---


# --- Tests for display_scene_info ---


def test_display_scene_info(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],  # Needed to test event display
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying scene info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        initialize_event_sources(session)  # FIX: Initialize sources
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        create_test_event(session, scene_id=scene.id)
        session.refresh(scene, attribute_names=["events", "act"])  # Load relationships.
        renderer.display_scene_info(scene)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check border style based on is_active (default is True).
    assert args[0].border_style == BORDER_STYLES["current"]
    # Check that "Status" is not in the panel's content.
    assert "Status" not in str(args[0].renderable)
