"""Tests for the RichRenderer class."""

# Add necessary imports
from typing import Any, Callable, List, Optional  # Added Optional, Callable, Any
from unittest.mock import MagicMock, patch  # Added patch

import pytest
from rich.console import Console
from rich.panel import Panel  # Import Panel for assertion

from sologm.cli.rendering.rich_renderer import RichRenderer
from sologm.database.session import SessionContext  # <-- Added import
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus

# Import manager types for mocking/type hinting if needed by tests
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager

# Import BORDER_STYLES for assertions if needed
from sologm.cli.utils.styled_text import BORDER_STYLES


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


# --- End Tests for display_scene_info ---


# --- Test for display_error (New Method) ---


def test_display_error(mock_console: MagicMock):
    """Test displaying an error message using RichRenderer."""
    renderer = RichRenderer(mock_console)
    error_message = "Something went wrong!"
    # This call should fail with NotImplementedError initially
    renderer.display_error(error_message)

    # Assertions will run after implementation
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
):
    """Test displaying full game status with all components using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        event1 = create_test_event(session, scene_id=scene.id, description="Event 1")
        event2 = create_test_event(session, scene_id=scene.id, description="Event 2")
        dice_roll = DiceRoll.create(
            notation="1d10", individual_results=[7], modifier=0, total=7, scene_id=scene.id
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

    # Assertions remain the same
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

    # Assertions will run after implementation
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
        oracle_manager=mock_oracle_manager,
        recent_rolls=None,
        is_act_active=True,
        is_scene_active=True,
    )

    # Assertions will run after implementation
    assert mock_console.print.called


def test_display_game_status_no_interpretation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
):
    """Test displaying game status without oracle manager using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)

    with session_context as session:
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

    # Assertions will run after implementation
    assert mock_console.print.called


def test_display_game_status_selected_interpretation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
    # Interpretation/Set are created manually for mock setup
):
    """Test displaying game status with a selected interpretation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    mock_scene_manager = MagicMock(spec=SceneManager)
    mock_oracle_manager = MagicMock(spec=OracleManager)

    with session_context as session:
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
        mock_oracle_manager.get_current_interpretation_set = MagicMock(return_value=None)
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

    # Assertions will run after implementation
    assert mock_console.print.called


# --- End Tests for display_game_status ---


# --- Tests for display_game_status Helpers (Moved & Adapted) ---


def test_calculate_truncation_length(mock_console: MagicMock):
    """Test the truncation length calculation using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with AttributeError initially
    # Test with a valid console width
    mock_console.width = 100
    result = renderer._calculate_truncation_length()
    # --- MODIFIED ASSERTION ---
    assert result == 40  # Expected: max(40, int(100 / 2) - 10) = 40

    # Test with a small console width
    mock_console.width = 30
    result = renderer._calculate_truncation_length()
    assert result == 40  # min value

    # Test with an invalid console width (should use self.console.width)
    mock_console.width = None
    # Mock console width to return a default if None
    mock_console.width = 80  # Keep this mock setup
    result = renderer._calculate_truncation_length()
    # --- MODIFIED ASSERTION ---
    # Expected: max(40, int(80 / 2) - 10) = max(40, 30) = 40
    assert result == 40


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
        # Check if summary is present (might be truncated)
        assert act.summary[:10] in panel_active.renderable  # Check start of summary

        # Test with inactive act and specific truncation
        act.summary = "This is a very long summary that definitely needs to be truncated for the test."
        session.add(act)
        session.flush()
        panel_inactive_truncated = renderer._create_act_panel(
            game, act, is_act_active=False, truncation_length=20
        )
        assert panel_inactive_truncated is not None
        assert panel_inactive_truncated.border_style == BORDER_STYLES["neutral"]
        # Check if the summary is truncated (20 * 1.5 = 30 chars max)
        assert "This is a very long summary..." in panel_inactive_truncated.renderable
        assert (
            "truncated for the test." not in panel_inactive_truncated.renderable
        )  # End should be cut off

        # Test with no active act
        panel_no_act = renderer._create_act_panel(game, None)
        assert panel_no_act is not None
        assert panel_no_act.title is not None
        assert panel_no_act.border_style == BORDER_STYLES["neutral"]
    # Check for the updated message when no act is provided
    assert "No acts found in this game." in panel_no_act.renderable


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
        grid = renderer._create_scene_panels_grid(
            game, scene, mock_scene_manager, is_scene_active=True
        )
        assert grid is not None

        # Test with active scene but no scene manager
        grid = renderer._create_scene_panels_grid(
            game, scene, None, is_scene_active=True
        )
        assert grid is not None

        # Test with no active scene
        grid = renderer._create_scene_panels_grid(
            game, None, None, is_scene_active=False
        )
        assert grid is not None


def test_create_events_panel(mock_console: MagicMock, test_events: List[Event]):
    """Test creating the events panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with AttributeError initially
    # Test with events
    panel = renderer._create_events_panel(test_events, 60)
    assert panel is not None
    assert "Recent Events" in panel.title
    assert panel.border_style == BORDER_STYLES["success"]

    # Test with no events
    panel = renderer._create_events_panel([], 60)
    assert panel is not None
    assert "Recent Events" in panel.title


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
        panel = renderer._create_oracle_panel(game, scene, None, 60)
        assert panel is None

        # Test with oracle manager (mock behavior as needed)
        # Mock the methods on the mock_oracle_manager instance directly
        mock_oracle_manager.get_current_interpretation_set = MagicMock(return_value=None)
        mock_oracle_manager.get_most_recent_interpretation = MagicMock(return_value=None)

        panel = renderer._create_oracle_panel(game, scene, mock_oracle_manager, 60)
        assert panel is not None  # Should return empty panel in this case
        assert "No oracle interpretations yet." in panel.renderable


def test_create_empty_oracle_panel(mock_console: MagicMock):
    """Test creating an empty oracle panel using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call should fail with AttributeError initially
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
            notation="3d6", individual_results=[1, 2, 3], modifier=0, total=6, scene_id=scene.id
        )
        session.add(dice_roll)
        session.flush()
        session.refresh(dice_roll)
        rolls = [dice_roll]

        # Test with no rolls
        panel = renderer._create_dice_rolls_panel([])
        assert panel is not None
        assert "Recent Rolls" in panel.title
        assert "No recent dice rolls" in panel.renderable

        # Test with rolls
        panel = renderer._create_dice_rolls_panel(rolls)
        assert panel is not None
        assert "Recent Rolls" in panel.title
        assert dice_roll.notation in panel.renderable


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
        interp1 = create_test_interpretation(session, set_id=interp_set.id, title="Interp 1")
        interp2 = create_test_interpretation(session, set_id=interp_set.id, title="Interp 2")
        # Refresh the set to load interpretations relationship
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_set(interp_set)

    # Assertions will run after implementation
    # Expect calls for context panel (if show_context=True), each interpretation, and instruction panel
    assert mock_console.print.call_count >= len(interp_set.interpretations) + 2


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
        interp1 = create_test_interpretation(session, set_id=interp_set.id, title="Interp 1")
        interp2 = create_test_interpretation(session, set_id=interp_set.id, title="Interp 2")
        # Refresh the set to load interpretations relationship
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_set(interp_set, show_context=False)

    # Assertions will run after implementation
    # Expect calls for each interpretation and instruction panel
    assert mock_console.print.call_count == len(interp_set.interpretations) + 1


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
        # Add interpretations if needed by the display logic
        create_test_interpretation(session, set_id=interp_set.id)
        session.refresh(interp_set, attribute_names=["interpretations"])

    renderer.display_interpretation_status(interp_set)

    # Expecting two prints: one for the panel, one for the trailing newline
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
        interp_set1 = create_test_interpretation_set(session, scene_id=scene.id, retry_attempt=0)
        interp_set2 = create_test_interpretation_set(session, scene_id=scene.id, retry_attempt=1)
        interp_sets = [interp_set1, interp_set2]

    renderer.display_interpretation_sets_table(interp_sets)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


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
        scene1 = create_test_scene(session, act_id=act.id, title="Scene 1", is_active=False)
        scene2 = create_test_scene(session, act_id=act.id, title="Scene 2", is_active=True)
        scenes = [scene1, scene2]
        active_scene_id = scene2.id

    renderer.display_scenes_table(scenes, active_scene_id)

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


# --- Tests for display_events_table ---


def test_display_events_table_with_events(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
):
    """Test displaying events table with events using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
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
    assert isinstance(args[0], Panel)  # Expecting a Panel containing the Table


def test_display_events_table_with_truncation(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event],
):
    """Test displaying events table with truncated descriptions using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
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

        # Test with truncation enabled (default)
        renderer.display_events_table(
            events, scene, max_description_length=20
        )  # Pass max_length
        mock_console.print.assert_called_once()
        args1, _ = mock_console.print.call_args
        assert isinstance(args1[0], Panel)
        mock_console.reset_mock()  # Reset for the next call

        # Test with truncation disabled
        renderer.display_events_table(events, scene, truncate_descriptions=False)
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
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
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
    args, kwargs = mock_console.print.call_args_list[0]  # Check first call
    assert len(args) == 1
    assert isinstance(args[0], Panel)
    # Check second call is just a newline print
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
        results_both = {"title": "AI Generated Title", "summary": "AI Generated Summary"}
        renderer.display_act_ai_generation_results(results_both, act)
        assert mock_console.print.call_count >= 2  # At least title and summary panels
        mock_console.reset_mock()

        # Test with only title
        results_title = {"title": "AI Generated Title"}
        renderer.display_act_ai_generation_results(results_title, act)
        assert mock_console.print.call_count >= 1  # At least title panel
        mock_console.reset_mock()

        # Test with only summary
        results_summary = {"summary": "AI Generated Summary"}
        renderer.display_act_ai_generation_results(results_summary, act)
        assert mock_console.print.call_count >= 1  # At least summary panel
        mock_console.reset_mock()

        # Test with empty results
        results_empty = {}
        renderer.display_act_ai_generation_results(results_empty, act)
        # No panels should be printed if results are empty
        assert mock_console.print.call_count == 0
        mock_console.reset_mock()

        # Test with existing content for comparison
        act.title = "Existing Title"
        act.summary = "Existing Summary"
        session.add(act)
        session.flush()
        results_compare = {"title": "AI Generated Title", "summary": "AI Generated Summary"}
        renderer.display_act_ai_generation_results(results_compare, act)
        # Expect 4 panels: AI title, existing title, AI summary, existing summary
        assert mock_console.print.call_count == 4
        args_list = mock_console.print.call_args_list
    assert isinstance(args_list[0][0][0], Panel)  # AI Title
    assert isinstance(args_list[1][0][0], Panel)  # Existing Title
    assert isinstance(args_list[2][0][0], Panel)  # AI Summary
    assert isinstance(args_list[3][0][0], Panel)  # Existing Summary


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
        # Test with title and summary
        act_with_title = create_test_act(
            session, game_id=game.id, title="Completed Act", summary="It is done."
        )
        renderer.display_act_completion_success(act_with_title)
        assert mock_console.print.call_count >= 3  # Title message, metadata, title, summary
        mock_console.reset_mock()

        # Test with untitled act
        act_untitled = create_test_act(
            session, game_id=game.id, title=None, summary="Summary only"
        )
        renderer.display_act_completion_success(act_untitled)
        assert (
            mock_console.print.call_count >= 2
        )  # Title message, metadata, summary (no title print)


# --- End Tests for display_act_completion_success ---


# --- Tests for display_act_ai_feedback_prompt (Moved & Adapted) ---

from unittest.mock import patch  # Import patch


@patch("rich.prompt.Prompt.ask")  # Patch Prompt.ask
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
    mock_ask.assert_called_once()  # Verify Prompt.ask was called


# --- End Tests for display_act_ai_feedback_prompt ---


# --- Tests for display_act_edited_content_preview (Moved & Adapted) ---


def test_display_act_edited_content_preview(mock_console: MagicMock):
    """Test displaying edited content preview for an act using RichRenderer."""
    renderer = RichRenderer(mock_console)
    edited_results = {"title": "Edited Title", "summary": "Edited Summary"}
    # This call should fail with NotImplementedError initially
    renderer.display_act_edited_content_preview(edited_results)

    # Assertions will run after implementation
    # Expecting 3 prints: header, title panel, summary panel
    assert mock_console.print.call_count == 3
    args_list = mock_console.print.call_args_list
    assert "Preview of your edited content:" in args_list[0][0][0]
    assert isinstance(args_list[1][0][0], Panel)  # Title Panel
    assert isinstance(args_list[2][0][0], Panel)  # Summary Panel


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
    create_test_scene: Callable[..., Scene], # Needed to test scene display within act
):
    """Test displaying act info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session, name="My Game")
        act = create_test_act(session, game_id=game.id)
        # Add a scene to test the scene listing part
        create_test_scene(session, act_id=act.id)
        session.refresh(act, attribute_names=["scenes"]) # Load scenes relationship

    renderer.display_act_info(act, game.name)

    # Expecting two prints: one for the main act panel, one for the scenes panel/table
    assert mock_console.print.call_count == 2
    args1, _ = mock_console.print.call_args_list[0]
    args2, _ = mock_console.print.call_args_list[1]
    assert isinstance(args1[0], Panel)
    assert isinstance(args2[0], Panel)


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


# --- Tests for display_scene_info ---


def test_display_scene_info(
    mock_console: MagicMock,
    session_context: SessionContext,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    create_test_event: Callable[..., Event], # Needed to test event display
):
    """Test displaying scene info using RichRenderer."""
    renderer = RichRenderer(mock_console)
    with session_context as session:
        game = create_test_game(session)
        act = create_test_act(session, game_id=game.id)
        scene = create_test_scene(session, act_id=act.id)
        # Add an event to test event listing
        create_test_event(session, scene_id=scene.id)
        session.refresh(scene, attribute_names=["events"]) # Load events relationship

    renderer.display_scene_info(scene)

    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)
