"""Common test fixtures for all sologm tests."""

import logging
from typing import Any, List # Added List
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session # Ensure Session is imported
from sqlalchemy import create_engine

from sologm.core.act import ActManager
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.base import Base
from sologm.models.dice import DiceRoll
from sologm.models.event import Event # Import Event model
from sologm.models.event_source import EventSource
from sologm.models.game import Game # Import Game model
from sologm.models.act import Act # Import Act model
from sologm.models.scene import Scene # Import Scene model
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import SceneStatus
from sologm.utils.config import Config

logger = logging.getLogger(__name__)


# Renamed fixture, removed autouse=True and the 'with patch(...)' block
@pytest.fixture
def mock_config_no_api_key():
    """
    Creates a mock Config object that simulates the anthropic_api_key
    not being set (returns None when get() is called for that key).
    """
    logger.debug("[Fixture mock_config_no_api_key] Creating mock Config object")
    mock_config = MagicMock(spec=Config)

    # Define the behavior for the mock's get method
    def mock_get(key: str, default: Any = None) -> Any:
        logger.debug(
            f"[Fixture mock_config_no_api_key] Mock config.get called with key: {key}"
        )
        if key == "anthropic_api_key":
            logger.debug(
                f"[Fixture mock_config_no_api_key] Mock config returning None for key: {key}"
            )
            return None
        # For other keys, maybe return default or raise an error if unexpected
        logger.debug(
            f"[Fixture mock_config_no_api_key] Mock config returning default for key: {key}"
        )
        return default

    mock_config.get.side_effect = mock_get
    logger.debug("[Fixture mock_config_no_api_key] Returning configured mock object")
    return mock_config


# Database fixtures
@pytest.fixture
def db_engine():
    """Create a new in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(database_manager):
    """Get a SQLAlchemy session for testing.

    This is primarily used for initializing managers in tests.
    For most test operations, prefer using session_context.
    """
    logger.debug("Initializing db_session")
    session = database_manager.get_session()
    logger.debug("Yielding db session.")
    yield session
    logger.debug("Closing db session.")
    session.close()
    database_manager.close_session()


@pytest.fixture(scope="function", autouse=True)
def database_manager(db_engine):
    """Create a DatabaseManager instance for testing.

    This fixture replaces the singleton DatabaseManager instance with a test-specific
    instance that uses an in-memory SQLite database. This approach ensures:

    1. Test isolation: Each test gets its own clean database
    2. No side effects: Tests don't affect the real application database
    3. Singleton pattern preservation: The pattern is maintained during testing

    The original singleton instance is saved before the test and restored afterward,
    ensuring that tests don't permanently modify the application's database connection.
    This is critical for test isolation and preventing test order dependencies.

    Args:
        db_engine: SQLite in-memory engine for testing

    Yields:
        A test-specific DatabaseManager instance
    """
    from sologm.database.session import DatabaseManager

    # Save original instance to restore it after the test
    # This prevents tests from affecting each other or the real application
    old_instance = DatabaseManager._instance

    # Create new instance with test engine
    db_manager = DatabaseManager(engine=db_engine)
    DatabaseManager._instance = db_manager

    yield db_manager

    # Restore original instance to prevent test pollution
    DatabaseManager._instance = old_instance


# Mock fixtures
@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def cli_test():
    """Helper for testing CLI command patterns.

    This fixture provides a function that executes test code within a session context,
    mimicking how CLI commands work in production.

    Example:
        def test_cli_pattern(cli_test):
            def test_func(session):
                game_manager = GameManager(session=session)
                return game_manager.create_game("Test Game", "Description")

            game = cli_test(test_func)
            assert game.name == "Test Game"
    """

    def run_with_context(test_func):
        from sologm.database.session import get_db_context

        with get_db_context() as session:
            return test_func(session)

    return run_with_context


# Session context fixture
@pytest.fixture
def session_context():
    """Create a SessionContext for testing.

    This fixture provides the same session context that application code uses,
    ensuring tests mirror real usage patterns. Use this as the primary way to
    access the database in tests.

    Example:
        def test_something(session_context):
            with session_context as session:
                # Test code using session
    """
    from sologm.database.session import get_db_context

    return get_db_context()


# Manager fixtures
# Removed redundant setup_database_manager fixture
# The database_manager fixture now has autouse=True


@pytest.fixture
def game_manager(db_session):
    """Create a GameManager with test session."""
    return GameManager(session=db_session)


@pytest.fixture
def act_manager(db_session, game_manager):
    """Create an ActManager with test session."""
    return ActManager(session=db_session, game_manager=game_manager)


@pytest.fixture
def scene_manager(db_session, act_manager):
    """Create a SceneManager with test session."""
    return SceneManager(session=db_session, act_manager=act_manager)


@pytest.fixture
def event_manager(db_session, scene_manager):
    """Create an EventManager with test session."""
    return EventManager(session=db_session, scene_manager=scene_manager)


@pytest.fixture
def dice_manager(db_session, scene_manager):
    """Create a DiceManager with test session."""
    # Corrected: Pass scene_manager to DiceManager constructor if needed,
    # or remove if not. Assuming it might be needed for context.
    return DiceManager(session=db_session, scene_manager=scene_manager)


@pytest.fixture
def oracle_manager(scene_manager, mock_anthropic_client):
    """Create an OracleManager with a scene manager and mock client."""
    # Note: OracleManager might need db_session too, adjust if necessary
    # Assuming scene_manager provides the session implicitly or it's passed separately
    return OracleManager(
        scene_manager=scene_manager,
        anthropic_client=mock_anthropic_client,
        # session=db_session # Add this if OracleManager needs session directly
    )


# Model factory fixtures
@pytest.fixture
def create_test_game(game_manager, db_session: Session): # Inject db_session
    """Factory fixture to create test games attached to the test's session."""

    def _create_game(name="Test Game", description="A test game", is_active=True):
        game = game_manager.create_game(name, description, is_active=is_active)
        merged_game = db_session.merge(game)
        try:
            # Eagerly load relationships commonly needed
            db_session.refresh(merged_game, attribute_names=["acts"])
        except Exception as e:
            logger.warning(f"Warning: Error refreshing relationships in create_test_game factory: {e}")
        return merged_game # Return the merged, refreshed object

    return _create_game


@pytest.fixture
def create_test_act(act_manager, db_session: Session): # Inject db_session
    """Factory fixture to create test acts attached to the test's session."""

    def _create_act(
        game_id,
        title="Test Act",
        summary="A test act",
        is_active=True,
        sequence=None, # Add sequence parameter
    ):
        act = act_manager.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )
        # If sequence was specified, update it directly before merging
        if sequence is not None:
             # Use the manager's session temporarily for the update before merge
             act_manager_session = act_manager._session
             act.sequence = sequence
             act_manager_session.add(act)
             act_manager_session.flush()

        merged_act = db_session.merge(act)
        try:
            # Eagerly load relationships commonly needed
            db_session.refresh(merged_act, attribute_names=["scenes", "game"])
        except Exception as e:
            logger.warning(f"Warning: Error refreshing relationships in create_test_act factory: {e}")
        return merged_act

    return _create_act


@pytest.fixture
def create_test_scene(scene_manager, db_session: Session): # Inject db_session
    """Factory fixture to create test scenes attached to the test's session."""

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        is_active=True,
        status=SceneStatus.ACTIVE,
    ):
        scene = scene_manager.create_scene(
            act_id=act_id,
            title=title,
            description=description,
            make_active=is_active,
        )
        if status == SceneStatus.COMPLETED:
            # Use manager's session for completion logic before merge
            scene_manager.complete_scene(scene.id)
            # Re-fetch the scene from manager's session to get updated state
            scene = scene_manager.get_scene(scene.id)


        merged_scene = db_session.merge(scene)
        try:
            # Eagerly load relationships commonly needed
            db_session.refresh(merged_scene, attribute_names=["act", "events", "interpretations", "dice_rolls"])
            if merged_scene.act:
                 db_session.refresh(merged_scene.act, attribute_names=["game"])
        except Exception as e:
            logger.warning(f"Warning: Error refreshing relationships in create_test_scene factory: {e}")
        return merged_scene

    return _create_scene


@pytest.fixture
def create_test_event(event_manager, db_session: Session): # Inject db_session
    """Factory fixture to create test events attached to the test's session."""

    def _create_event(
        scene_id, description="Test event", source="manual", interpretation_id=None
    ):
        event = event_manager.add_event(
            description=description,
            scene_id=scene_id,
            source=source,
            interpretation_id=interpretation_id,
        )
        merged_event = db_session.merge(event)
        try:
            # Eagerly load relationships commonly needed
            db_session.refresh(merged_event, attribute_names=["scene", "source", "interpretation"])
        except Exception as e:
            logger.warning(f"Warning: Error refreshing relationships in create_test_event factory: {e}")
        return merged_event

    return _create_event


# Common test objects
@pytest.fixture
def test_game(game_manager, db_session: Session): # Inject db_session
    """Create a test game, ensuring it's attached to the test's session."""
    # Create the game using the manager (which uses its own session instance)
    game = game_manager.create_game("Test Game", "A test game", is_active=True)

    # Merge the created game into the session that the test function will use
    merged_game = db_session.merge(game)

    # Eagerly load relationships commonly needed to avoid lazy load errors
    # Adjust attribute_names based on common usage patterns
    try:
        # Refreshing 'acts' is often needed when accessing game details
        db_session.refresh(merged_game, attribute_names=["acts"])
        # Optionally load deeper relationships if frequently needed right after game creation
        # for act in merged_game.acts:
        #     db_session.refresh(act, attribute_names=["scenes"])
    except Exception as e:
         # Log potential issues during refresh, but proceed
         logger.warning(f"Warning: Error refreshing relationships for test_game fixture: {e}")

    # Return the object attached to the db_session the test will use
    return merged_game


@pytest.fixture
def create_test_act(act_manager):
    """Factory fixture to create test acts using the ActManager.

    This uses the ActManager to create acts, which better reflects
    how the application code would create acts.
    """

    def _create_act(
        game_id,
        title="Test Act",
        summary="A test act",
        is_active=True,
        sequence=None,  # Add sequence parameter
    ):
        act = act_manager.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )

        # If sequence was specified, update it directly
        if sequence is not None:
            session = act_manager._session
            act.sequence = sequence
            session.add(act)
            session.flush()

        return act

    return _create_act


@pytest.fixture
def create_test_scene(scene_manager):
    """Factory fixture to create test scenes using the SceneManager.

    This uses the SceneManager to create scenes, which better reflects
    how the application code would create scenes.
    """

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        is_active=True,
        status=SceneStatus.ACTIVE,
    ):
        scene = scene_manager.create_scene(
            act_id=act_id,
            title=title,
            description=description,
            make_active=is_active,
        )
        if status == SceneStatus.COMPLETED:
            scene_manager.complete_scene(scene.id)
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(event_manager):
    """Factory fixture to create test events using the EventManager.

    This uses the EventManager to create events, which better reflects
    how the application code would create events.
    """

    def _create_event(
        scene_id, description="Test event", source="manual", interpretation_id=None
    ):
        event = event_manager.add_event(
            description=description,
            scene_id=scene_id,
            source=source,
            interpretation_id=interpretation_id,
        )
        return event

    return _create_event


# Common test objects
@pytest.fixture
def test_game(game_manager):
    """Create a test game using the GameManager."""
    return game_manager.create_game("Test Game", "A test game", is_active=True)


@pytest.fixture
def create_test_act(act_manager):
    """Factory fixture to create test acts using the ActManager.

    This uses the ActManager to create acts, which better reflects
    how the application code would create acts.
    """

    def _create_act(
        game_id,
        title="Test Act",
        summary="A test act",
        is_active=True,
        sequence=None,  # Add sequence parameter
    ):
        act = act_manager.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )

        # If sequence was specified, update it directly
        if sequence is not None:
            session = act_manager._session
            act.sequence = sequence
            session.add(act)
            session.flush()

        return act

    return _create_act


@pytest.fixture
def create_test_scene(scene_manager):
    """Factory fixture to create test scenes using the SceneManager.

    This uses the SceneManager to create scenes, which better reflects
    how the application code would create scenes.
    """

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        is_active=True,
        status=SceneStatus.ACTIVE,
    ):
        scene = scene_manager.create_scene(
            act_id=act_id,
            title=title,
            description=description,
            make_active=is_active,
        )
        if status == SceneStatus.COMPLETED:
            scene_manager.complete_scene(scene.id)
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(event_manager):
    """Factory fixture to create test events using the EventManager.

    This uses the EventManager to create events, which better reflects
    how the application code would create events.
    """

    def _create_event(
        scene_id, description="Test event", source="manual", interpretation_id=None
    ):
        event = event_manager.add_event(
            description=description,
            scene_id=scene_id,
            source=source,
            interpretation_id=interpretation_id,
        )
        return event

    return _create_event


# Common test objects
@pytest.fixture
def test_game(game_manager):
    """Create a test game using the GameManager."""
    return game_manager.create_game("Test Game", "A test game", is_active=True)


@pytest.fixture
def test_act(act_manager, test_game, db_session: Session): # Inject db_session and test_game
    """Create a test act, ensuring it's attached to the test's session."""
    # test_game fixture already returns a session-bound object
    act = act_manager.create_act(
        game_id=test_game.id,
        title="Test Act",
        summary="A test act",
        make_active=True,
    )
    merged_act = db_session.merge(act)
    try:
        db_session.refresh(merged_act, attribute_names=["scenes", "game"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_act fixture: {e}")
    return merged_act

@pytest.fixture
def test_scene(scene_manager, test_act, db_session: Session): # Inject db_session and test_act
    """Create a test scene, ensuring it's attached to the test's session."""
    # test_act fixture already returns a session-bound object
    scene = scene_manager.create_scene(
        act_id=test_act.id,
        title="Test Scene",
        description="A test scene",
        make_active=True,
    )
    merged_scene = db_session.merge(scene)
    try:
        # Refresh relationships needed by display_game_status and others
        db_session.refresh(merged_scene, attribute_names=["act", "events", "interpretations", "dice_rolls"])
        if merged_scene.act:
             db_session.refresh(merged_scene.act, attribute_names=["game"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_scene fixture: {e}")
    return merged_scene

@pytest.fixture
def test_events(event_manager, test_scene, db_session: Session): # Inject db_session and test_scene
    """Create test events, ensuring they are attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    events_data = []
    for i in range(1, 3):
         event = event_manager.add_event(
             description=f"Test event {i}",
             scene_id=test_scene.id,
            source="manual",
         )
         merged_event = db_session.merge(event)
         try:
             # Refresh relationships needed by display_game_status (_create_events_panel)
             db_session.refresh(merged_event, attribute_names=["scene", "source", "interpretation"])
         except Exception as e:
             logger.warning(f"Warning: Error refreshing relationships for event {i} in test_events fixture: {e}")
         events_data.append(merged_event)
    return events_data


@pytest.fixture
def test_interpretation_set(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create a test interpretation set attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    interp_set = InterpretationSet.create(
        scene_id=test_scene.id,
        context="Test context",
            oracle_results="Test results",
            is_current=True,
        )
    # Add directly to db_session used by the test
    db_session.add(interp_set)
    db_session.flush() # Assign ID

    try:
        # Refresh relationships needed by display methods
        db_session.refresh(interp_set, attribute_names=["interpretations", "scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_interpretation_set fixture: {e}")

    return interp_set


@pytest.fixture
def test_interpretations(test_interpretation_set, db_session: Session): # Inject db_session and test_interpretation_set
    """Create test interpretations attached to the test's session."""
    # test_interpretation_set fixture already returns a session-bound object
    interpretations_data = []
    for i in range(1, 3):
        interp = Interpretation.create(
            set_id=test_interpretation_set.id, # Use the ID from the session-bound set
            title=f"Test Interpretation {i}",
            description=f"Test description {i}",
                is_selected=(i == 1),  # First one is selected
            )
        # Add directly to db_session
        db_session.add(interp)
        db_session.flush() # Assign ID
        try:
             # Refresh relationships needed by display methods
             db_session.refresh(interp, attribute_names=["interpretation_set"])
        except Exception as e:
             logger.warning(f"Warning: Error refreshing relationships for interpretation {i} in test_interpretations fixture: {e}")
        interpretations_data.append(interp)

    # Crucially, refresh the parent set's collection *after* adding children
    try:
        db_session.refresh(test_interpretation_set, attribute_names=["interpretations"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing interpretation_set relationship in test_interpretations fixture: {e}")

    return interpretations_data


@pytest.fixture
def empty_interpretation_set(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create an empty interpretation set for testing, attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    interp_set = InterpretationSet.create(
        scene_id=test_scene.id,
        context="Empty set context",
        oracle_results="Empty set results",
            is_current=True,
        )
    # Add directly to db_session
    db_session.add(interp_set)
    db_session.flush()
    try:
        # Refresh relationships
        db_session.refresh(interp_set, attribute_names=["interpretations", "scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for empty_interpretation_set fixture: {e}")
    return interp_set


@pytest.fixture
def test_dice_roll(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create a test dice roll attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    dice_roll = DiceRoll.create(
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
            total=12,
            reason="Test roll",
            scene_id=test_scene.id,
        )
    # Add directly to db_session
    db_session.add(dice_roll)
    db_session.flush() # Assign ID
    try:
        # Refresh relationships needed by display_game_status (_create_dice_rolls_panel)
        db_session.refresh(dice_roll, attribute_names=["scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_dice_roll fixture: {e}")
    return dice_roll


@pytest.fixture(autouse=True)
def initialize_event_sources(session_context):
    """Initialize event sources for testing."""
    sources = ["manual", "oracle", "dice"]
    with session_context as session:
        for source_name in sources:
            existing = (
                session.query(EventSource)
                .filter(EventSource.name == source_name)
                .first()
            )
            if not existing:
                source = EventSource.create(name=source_name)
                session.add(source)
        # Session is committed automatically when context exits


# Helper fixtures for testing model properties
@pytest.fixture
def assert_model_properties():
    """Helper fixture to assert model properties work correctly.

    This fixture provides a function that can be used to verify that model properties
    and hybrid properties return the expected values.

    Example:
        def test_game_properties(test_game, assert_model_properties):
            expected = {
                'has_acts': True,
                'act_count': 2,
                'has_active_act': True
            }
            assert_model_properties(test_game, expected)
    """

    def _assert_properties(model, expected_properties):
        """Assert that model properties match expected values.

        Args:
            model: The model instance to check
            expected_properties: Dict of property_name: expected_value
        """
        for prop_name, expected_value in expected_properties.items():
            assert hasattr(model, prop_name), (
                f"Model {model.__class__.__name__} has no property {prop_name}"
            )
            actual_value = getattr(model, prop_name)
            assert actual_value == expected_value, (
                f"Property {prop_name} doesn't match expected value. "
                f"Expected: {expected_value}, Got: {actual_value}"
            )

    return _assert_properties


@pytest.fixture
def test_hybrid_expressions():
    """Test fixture for SQL expressions of hybrid properties.

    This fixture provides a function that can be used to verify that hybrid property
    SQL expressions work correctly in queries.

    Example:
        def test_game_has_acts_expression(test_hybrid_expressions):
            test_hybrid_expressions(Game, 'has_acts', True, 1)  # Expect 1 game with acts
    """

    def _test_expression(model_class, property_name, filter_condition, expected_count):
        """Test that a hybrid property's SQL expression works correctly.

        Args:
            model_class: The model class to query
            property_name: The name of the hybrid property
            filter_condition: The condition to filter by (True/False)
            expected_count: The expected count of results
        """
        from sologm.database.session import get_db_context

        with get_db_context() as session:
            property_expr = getattr(model_class, property_name)
            query = session.query(model_class).filter(property_expr == filter_condition)
            result_count = query.count()
            assert result_count == expected_count, (
                f"Expected {expected_count} results for {model_class.__name__}.{property_name} == {filter_condition}, "
                f"got {result_count}"
            )

    return _test_expression


# Complex test fixtures
@pytest.fixture
def test_game_with_scenes(
    create_test_game, create_test_act, create_test_scene, db_session: Session # Inject db_session
):
    """Create a test game with multiple scenes, attached to the test's session."""
    # Use factories which now return session-bound objects
    game = create_test_game(
        name="Game with Scenes", description="A test game with multiple scenes"
    )
    act = create_test_act(
        game_id=game.id, title="Act with Scenes", summary="Test act with scenes" # Corrected description->summary
    )
    scenes = []
    for i in range(1, 4):
        scene = create_test_scene(
            act_id=act.id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 2),  # Make the middle scene active
        )
        scenes.append(scene)

    # Refreshing might still be needed if factories don't load everything
    try:
        db_session.refresh(game, attribute_names=["acts"])
        db_session.refresh(act, attribute_names=["scenes", "game"])
        for scene in scenes:
            db_session.refresh(scene, attribute_names=["act"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_game_with_scenes fixture: {e}")

    return game, scenes


@pytest.fixture
def test_game_with_complete_hierarchy(
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources, # Ensure this runs
    db_session: Session # Inject db_session
):
    """Create a complete game hierarchy, attached to the test's session."""
    game = create_test_game(
        name="Complete Game", description="A test game with complete hierarchy"
    )
    acts = [
        create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        for i in range(1, 3)
    ]

    scenes = []
    events = []
    for i, act in enumerate(acts):
        for j in range(1, 3):
            scene = create_test_scene(
                act_id=act.id,
                title=f"Scene {j} in Act {i + 1}",
                description=f"Test scene {j} in act {i + 1}",
                status=SceneStatus.ACTIVE if j == 1 else SceneStatus.COMPLETED,
                is_active=(j == 1),
            )
            scenes.append(scene)
            for k in range(1, 3):
                event = create_test_event(
                    scene_id=scene.id,
                    description=f"Event {k} in Scene {j} of Act {i + 1}",
                    source="manual",
                )
                events.append(event)

    # Refresh objects to ensure relationships are loaded after creation
    try:
        db_session.refresh(game, attribute_names=["acts"])
        for act_obj in acts:
            db_session.refresh(act_obj, attribute_names=["scenes", "game"])
        for scene_obj in scenes:
            db_session.refresh(scene_obj, attribute_names=["act", "events"])
        for event_obj in events:
            db_session.refresh(event_obj, attribute_names=["scene", "source"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_game_with_complete_hierarchy fixture: {e}")

    return game, acts, scenes, events


@pytest.fixture
def test_hybrid_property_game(
    create_test_game, create_test_act, create_test_scene, db_session: Session # Inject db_session
):
    """Create a game for testing hybrid properties, attached to the test's session."""
    game = create_test_game(
        name="Hybrid Property Test Game",
        description="Game for testing hybrid properties",
    )
    acts = [
        create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        for i in range(1, 3)
    ]
    scenes = [
        create_test_scene(
            act_id=acts[0].id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 1),
        )
        for i in range(1, 4)
    ]

    # Refresh objects after creation
    try:
        db_session.refresh(game, attribute_names=["acts"])
        for act_obj in acts:
            db_session.refresh(act_obj, attribute_names=["scenes", "game"])
        for scene_obj in scenes:
            db_session.refresh(scene_obj, attribute_names=["act"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_hybrid_property_game fixture: {e}")

    return {
        "game": game,
        "acts": acts,
        "scenes": scenes,
        "expected_properties": {
            "game": {
                "has_acts": True,
                "act_count": 2,
                "has_active_act": True,
            },
            "act": {
                "has_scenes": True,
                "scene_count": 3,
                "has_active_scene": True,
            },
        },
    }


@pytest.fixture
def create_test_act(act_manager):
    """Factory fixture to create test acts using the ActManager.

    This uses the ActManager to create acts, which better reflects
    how the application code would create acts.
    """

    def _create_act(
        game_id,
        title="Test Act",
        summary="A test act",
        is_active=True,
        sequence=None,  # Add sequence parameter
    ):
        act = act_manager.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )

        # If sequence was specified, update it directly
        if sequence is not None:
            session = act_manager._session
            act.sequence = sequence
            session.add(act)
            session.flush()

        return act

    return _create_act


@pytest.fixture
def create_test_scene(scene_manager):
    """Factory fixture to create test scenes using the SceneManager.

    This uses the SceneManager to create scenes, which better reflects
    how the application code would create scenes.
    """

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        is_active=True,
        status=SceneStatus.ACTIVE,
    ):
        scene = scene_manager.create_scene(
            act_id=act_id,
            title=title,
            description=description,
            make_active=is_active,
        )
        if status == SceneStatus.COMPLETED:
            scene_manager.complete_scene(scene.id)
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(event_manager):
    """Factory fixture to create test events using the EventManager.

    This uses the EventManager to create events, which better reflects
    how the application code would create events.
    """

    def _create_event(
        scene_id, description="Test event", source="manual", interpretation_id=None
    ):
        event = event_manager.add_event(
            description=description,
            scene_id=scene_id,
            source=source,
            interpretation_id=interpretation_id,
        )
        return event

    return _create_event


# Common test objects
@pytest.fixture
def test_game(game_manager):
    """Create a test game using the GameManager."""
    return game_manager.create_game("Test Game", "A test game", is_active=True)


@pytest.fixture
def test_act(act_manager, test_game, db_session: Session): # Inject db_session and test_game
    """Create a test act, ensuring it's attached to the test's session."""
    # test_game fixture already returns a session-bound object
    act = act_manager.create_act(
        game_id=test_game.id,
        title="Test Act",
        summary="A test act",
        make_active=True,
    )
    merged_act = db_session.merge(act)
    try:
        db_session.refresh(merged_act, attribute_names=["scenes", "game"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_act fixture: {e}")
    return merged_act

@pytest.fixture
def test_scene(scene_manager, test_act, db_session: Session): # Inject db_session and test_act
    """Create a test scene, ensuring it's attached to the test's session."""
    # test_act fixture already returns a session-bound object
    scene = scene_manager.create_scene(
        act_id=test_act.id,
        title="Test Scene",
        description="A test scene",
        make_active=True,
    )
    merged_scene = db_session.merge(scene)
    try:
        # Refresh relationships needed by display_game_status and others
        db_session.refresh(merged_scene, attribute_names=["act", "events", "interpretations", "dice_rolls"])
        if merged_scene.act:
             db_session.refresh(merged_scene.act, attribute_names=["game"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_scene fixture: {e}")
    return merged_scene

@pytest.fixture
def test_events(event_manager, test_scene, db_session: Session): # Inject db_session and test_scene
    """Create test events, ensuring they are attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    events_data = []
    for i in range(1, 3):
         event = event_manager.add_event(
             description=f"Test event {i}",
             scene_id=test_scene.id,
            source="manual",
         )
         merged_event = db_session.merge(event)
         try:
             # Refresh relationships needed by display_game_status (_create_events_panel)
             db_session.refresh(merged_event, attribute_names=["scene", "source", "interpretation"])
         except Exception as e:
             logger.warning(f"Warning: Error refreshing relationships for event {i} in test_events fixture: {e}")
         events_data.append(merged_event)
    return events_data


@pytest.fixture
def test_interpretation_set(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create a test interpretation set attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    interp_set = InterpretationSet.create(
        scene_id=test_scene.id,
        context="Test context",
            oracle_results="Test results",
            is_current=True,
        )
    # Add directly to db_session used by the test
    db_session.add(interp_set)
    db_session.flush() # Assign ID

    try:
        # Refresh relationships needed by display methods
        db_session.refresh(interp_set, attribute_names=["interpretations", "scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_interpretation_set fixture: {e}")

    return interp_set


@pytest.fixture
def test_interpretations(test_interpretation_set, db_session: Session): # Inject db_session and test_interpretation_set
    """Create test interpretations attached to the test's session."""
    # test_interpretation_set fixture already returns a session-bound object
    interpretations_data = []
    for i in range(1, 3):
        interp = Interpretation.create(
            set_id=test_interpretation_set.id, # Use the ID from the session-bound set
            title=f"Test Interpretation {i}",
            description=f"Test description {i}",
                is_selected=(i == 1),  # First one is selected
            )
        # Add directly to db_session
        db_session.add(interp)
        db_session.flush() # Assign ID
        try:
             # Refresh relationships needed by display methods
             db_session.refresh(interp, attribute_names=["interpretation_set"])
        except Exception as e:
             logger.warning(f"Warning: Error refreshing relationships for interpretation {i} in test_interpretations fixture: {e}")
        interpretations_data.append(interp)

    # Crucially, refresh the parent set's collection *after* adding children
    try:
        db_session.refresh(test_interpretation_set, attribute_names=["interpretations"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing interpretation_set relationship in test_interpretations fixture: {e}")

    return interpretations_data


@pytest.fixture
def empty_interpretation_set(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create an empty interpretation set for testing, attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    interp_set = InterpretationSet.create(
        scene_id=test_scene.id,
        context="Empty set context",
        oracle_results="Empty set results",
            is_current=True,
        )
    # Add directly to db_session
    db_session.add(interp_set)
    db_session.flush()
    try:
        # Refresh relationships
        db_session.refresh(interp_set, attribute_names=["interpretations", "scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for empty_interpretation_set fixture: {e}")
    return interp_set


@pytest.fixture
def test_dice_roll(test_scene, db_session: Session): # Inject db_session and test_scene
    """Create a test dice roll attached to the test's session."""
    # test_scene fixture already returns a session-bound object
    dice_roll = DiceRoll.create(
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
            total=12,
            reason="Test roll",
            scene_id=test_scene.id,
        )
    # Add directly to db_session
    db_session.add(dice_roll)
    db_session.flush() # Assign ID
    try:
        # Refresh relationships needed by display_game_status (_create_dice_rolls_panel)
        db_session.refresh(dice_roll, attribute_names=["scene"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships for test_dice_roll fixture: {e}")
    return dice_roll


@pytest.fixture(autouse=True)
def initialize_event_sources(session_context):
    """Initialize event sources for testing."""
    sources = ["manual", "oracle", "dice"]
    with session_context as session:
        for source_name in sources:
            existing = (
                session.query(EventSource)
                .filter(EventSource.name == source_name)
                .first()
            )
            if not existing:
                source = EventSource.create(name=source_name)
                session.add(source)
        # Session is committed automatically when context exits


# Helper fixtures for testing model properties
@pytest.fixture
def assert_model_properties():
    """Helper fixture to assert model properties work correctly.

    This fixture provides a function that can be used to verify that model properties
    and hybrid properties return the expected values.

    Example:
        def test_game_properties(test_game, assert_model_properties):
            expected = {
                'has_acts': True,
                'act_count': 2,
                'has_active_act': True
            }
            assert_model_properties(test_game, expected)
    """

    def _assert_properties(model, expected_properties):
        """Assert that model properties match expected values.

        Args:
            model: The model instance to check
            expected_properties: Dict of property_name: expected_value
        """
        for prop_name, expected_value in expected_properties.items():
            assert hasattr(model, prop_name), (
                f"Model {model.__class__.__name__} has no property {prop_name}"
            )
            actual_value = getattr(model, prop_name)
            assert actual_value == expected_value, (
                f"Property {prop_name} doesn't match expected value. "
                f"Expected: {expected_value}, Got: {actual_value}"
            )

    return _assert_properties


@pytest.fixture
def test_hybrid_expressions():
    """Test fixture for SQL expressions of hybrid properties.

    This fixture provides a function that can be used to verify that hybrid property
    SQL expressions work correctly in queries.

    Example:
        def test_game_has_acts_expression(test_hybrid_expressions):
            test_hybrid_expressions(Game, 'has_acts', True, 1)  # Expect 1 game with acts
    """

    def _test_expression(model_class, property_name, filter_condition, expected_count):
        """Test that a hybrid property's SQL expression works correctly.

        Args:
            model_class: The model class to query
            property_name: The name of the hybrid property
            filter_condition: The condition to filter by (True/False)
            expected_count: The expected count of results
        """
        from sologm.database.session import get_db_context

        with get_db_context() as session:
            property_expr = getattr(model_class, property_name)
            query = session.query(model_class).filter(property_expr == filter_condition)
            result_count = query.count()
            assert result_count == expected_count, (
                f"Expected {expected_count} results for {model_class.__name__}.{property_name} == {filter_condition}, "
                f"got {result_count}"
            )

    return _test_expression


# Complex test fixtures
@pytest.fixture
def test_game_with_scenes(
    create_test_game, create_test_act, create_test_scene, db_session: Session # Inject db_session
):
    """Create a test game with multiple scenes, attached to the test's session."""
    # Use factories which now return session-bound objects
    game = create_test_game(
        name="Game with Scenes", description="A test game with multiple scenes"
    )
    act = create_test_act(
        game_id=game.id, title="Act with Scenes", summary="Test act with scenes" # Corrected description->summary
    )
    scenes = []
    for i in range(1, 4):
        scene = create_test_scene(
            act_id=act.id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 2),  # Make the middle scene active
        )
        scenes.append(scene)

    # Refreshing might still be needed if factories don't load everything
    try:
        db_session.refresh(game, attribute_names=["acts"])
        db_session.refresh(act, attribute_names=["scenes", "game"])
        for scene in scenes:
            db_session.refresh(scene, attribute_names=["act"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_game_with_scenes fixture: {e}")

    return game, scenes


@pytest.fixture
def test_game_with_complete_hierarchy(
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources, # Ensure this runs
    db_session: Session # Inject db_session
):
    """Create a complete game hierarchy, attached to the test's session."""
    game = create_test_game(
        name="Complete Game", description="A test game with complete hierarchy"
    )
    acts = [
        create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        for i in range(1, 3)
    ]

    scenes = []
    events = []
    for i, act in enumerate(acts):
        for j in range(1, 3):
            scene = create_test_scene(
                act_id=act.id,
                title=f"Scene {j} in Act {i + 1}",
                description=f"Test scene {j} in act {i + 1}",
                status=SceneStatus.ACTIVE if j == 1 else SceneStatus.COMPLETED,
                is_active=(j == 1),
            )
            scenes.append(scene)
            for k in range(1, 3):
                event = create_test_event(
                    scene_id=scene.id,
                    description=f"Event {k} in Scene {j} of Act {i + 1}",
                    source="manual",
                )
                events.append(event)

    # Refresh objects to ensure relationships are loaded after creation
    try:
        db_session.refresh(game, attribute_names=["acts"])
        for act_obj in acts:
            db_session.refresh(act_obj, attribute_names=["scenes", "game"])
        for scene_obj in scenes:
            db_session.refresh(scene_obj, attribute_names=["act", "events"])
        for event_obj in events:
            db_session.refresh(event_obj, attribute_names=["scene", "source"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_game_with_complete_hierarchy fixture: {e}")

    return game, acts, scenes, events


@pytest.fixture
def test_hybrid_property_game(
    create_test_game, create_test_act, create_test_scene, db_session: Session # Inject db_session
):
    """Create a game for testing hybrid properties, attached to the test's session."""
    game = create_test_game(
        name="Hybrid Property Test Game",
        description="Game for testing hybrid properties",
    )
    acts = [
        create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        for i in range(1, 3)
    ]
    scenes = [
        create_test_scene(
            act_id=acts[0].id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 1),
        )
        for i in range(1, 4)
    ]

    # Refresh objects after creation
    try:
        db_session.refresh(game, attribute_names=["acts"])
        for act_obj in acts:
            db_session.refresh(act_obj, attribute_names=["scenes", "game"])
        for scene_obj in scenes:
            db_session.refresh(scene_obj, attribute_names=["act"])
    except Exception as e:
        logger.warning(f"Warning: Error refreshing relationships in test_hybrid_property_game fixture: {e}")

    return {
        "game": game,
        "acts": acts,
        "scenes": scenes,
        "expected_properties": {
            "game": {
                "has_acts": True,
                "act_count": 2,
                "has_active_act": True,
            },
            "act": {
                "has_scenes": True,
                "scene_count": 3,
                "has_active_scene": True,
            },
        },
    }
