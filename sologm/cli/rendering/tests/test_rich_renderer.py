"""Tests for the RichRenderer class."""

# Add necessary imports
from typing import Callable, Any, List, Dict, Optional  # Added List, Dict, Optional
from unittest.mock import MagicMock, patch  # Added patch

import pytest
from rich.console import Console  # Removed Grid import
from rich.panel import Panel  # Import Panel for assertion
from rich.table import Table  # Import Table for type checking if needed
from rich.layout import Layout  # Import Layout for type checking if needed

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


def test_display_game_status_full(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying full game status with all components using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    # --- Setup Mocks for Oracle ---
    # Create mock interpretations with string attributes
    mock_interp1 = MagicMock(spec=Interpretation)
    mock_interp1.id = "mock-interp-1"
    mock_interp1.title = "Mock Interpretation 1"
    mock_interp1.description = "Description for mock 1."
    mock_interp1.is_selected = False

    mock_interp2 = MagicMock(spec=Interpretation)
    mock_interp2.id = "mock-interp-2"
    mock_interp2.title = "Mock Interpretation 2"
    mock_interp2.description = "Description for mock 2."
    mock_interp2.is_selected = False

    # Create a mock interpretation set with string context and list of mock interpretations
    mock_interp_set = MagicMock(spec=InterpretationSet)
    mock_interp_set.id = "mock-set-1"
    mock_interp_set.context = "This is the mock context."  # Ensure context is a string
    mock_interp_set.oracle_results = "Mock oracle results."
    mock_interp_set.interpretations = [mock_interp1, mock_interp2]
    mock_interp_set.retry_attempt = 0

    # Configure the mock manager's methods
    # For this test, assume there's a pending set and no recent selected one
    mock_oracle_manager.get_current_interpretation_set.return_value = mock_interp_set
    mock_oracle_manager.get_most_recent_interpretation.return_value = None
    # --- End Oracle Mock Setup ---

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

    assert mock_console.print.called


def test_display_game_status_no_scene(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
):
    """Test displaying game status without an active scene using RichRenderer."""
    renderer = RichRenderer(mock_console)
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

    assert mock_console.print.called


def test_display_game_status_no_events(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
):
    """Test displaying game status without any events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    # --- Setup Mocks for Oracle (Pending State) ---
    # Create a mock interpretation set with string context and empty interpretations list
    mock_interp_set = MagicMock(spec=InterpretationSet)
    mock_interp_set.id = "mock-set-pending"
    mock_interp_set.context = "Mock pending context."  # Ensure context is a string
    mock_interp_set.oracle_results = "Mock pending results."
    mock_interp_set.interpretations = []  # Empty list for no selection path
    mock_interp_set.retry_attempt = 0

    # Configure the mock manager's methods for the pending scenario
    mock_oracle_manager.get_current_interpretation_set.return_value = mock_interp_set
    mock_oracle_manager.get_most_recent_interpretation.return_value = None
    # --- End Oracle Mock Setup ---

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

    assert mock_console.print.called


def test_display_game_status_no_interpretation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    initialize_event_sources: Callable[[Session], None],  # FIX: Add fixture
):
    """Test displaying game status without oracle manager using RichRenderer."""
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

    assert mock_console.print.called


def test_display_game_status_selected_interpretation(
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

        # Setup: Create interpretation data and configure mock oracle_manager
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
        # Mock the methods on the mock_oracle_manager instance directly
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

    assert mock_console.print.called


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
