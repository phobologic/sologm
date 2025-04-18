"""Common test fixtures for all sologm tests."""

import logging
from unittest.mock import MagicMock, patch

import pytest
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
from sologm.models.event_source import EventSource
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import SceneStatus

from sologm.utils.config import Config  # Import for type hinting
from typing import Any  # Add Any if not already imported

logger = logging.getLogger(__name__)


# Config mocking fixture
@pytest.fixture(autouse=True)
def mock_global_config():
    """
    Mocks get_config where it's used in the anthropic module to prevent
    reading real user config and provide predictable config for tests.

    The mocked config.get() will return None when asked for 'anthropic_api_key'.
    """
    logger.debug("[Fixture mock_global_config] Setting up mock Config object")
    # Create a mock Config instance
    mock_config = MagicMock(spec=Config)

    # Define the behavior for the mock's get method
    def mock_get(key: str, default: Any = None) -> Any:
        logger.debug(
            f"[Fixture mock_global_config] Mock config.get called with key: {key}"
        )
        # Simulate the key not being found in the config file source
        if key == "anthropic_api_key":
            logger.debug(
                f"[Fixture mock_global_config] Mock config returning None for key: {key}"
            )
            return None
        # For any other key requested from the mock config, return default
        logger.debug(
            f"[Fixture mock_global_config] Mock config returning default for key: {key}"
        )
        return default

    mock_config.get.side_effect = mock_get

    # Patch get_config where it's LOOKED UP in the anthropic module
    patch_target = "sologm.integrations.anthropic.get_config"
    logger.debug(f"[Fixture mock_global_config] Applying patch to: {patch_target}")
    with patch(patch_target, return_value=mock_config, autospec=True) as mock_getter:
        logger.debug(
            f"[Fixture mock_global_config] Patch applied. Yielding mock: {mock_getter}"
        )
        yield mock_getter  # Yield the mock getter for potential inspection
    logger.debug("[Fixture mock_global_config] Patch finished.")


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
    return DiceManager(session=db_session, scene_manager=scene_manager)


@pytest.fixture
def oracle_manager(scene_manager, mock_anthropic_client):
    """Create an OracleManager with a scene manager and mock client."""
    return OracleManager(
        scene_manager=scene_manager,
        anthropic_client=mock_anthropic_client,
    )


# Model factory fixtures
@pytest.fixture
def create_test_game(game_manager):
    """Factory fixture to create test games using the GameManager.

    This uses the GameManager to create games, which better reflects
    how the application code would create games.
    """

    def _create_game(name="Test Game", description="A test game", is_active=True):
        game = game_manager.create_game(name, description, is_active=is_active)
        return game

    return _create_game


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
def test_act(act_manager, test_game):
    """Create a test act for the test game using the ActManager."""
    return act_manager.create_act(
        game_id=test_game.id,
        title="Test Act",
        summary="A test act",
        make_active=True,
    )


@pytest.fixture
def test_scene(scene_manager, test_act):
    """Create a test scene for the test act using the SceneManager."""
    return scene_manager.create_scene(
        act_id=test_act.id,
        title="Test Scene",
        description="A test scene",
        make_active=True,
    )


@pytest.fixture
def test_events(event_manager, test_scene):
    """Create test events using the EventManager."""
    events = [
        event_manager.add_event(
            description=f"Test event {i}",
            scene_id=test_scene.id,
            source="manual",
        )
        for i in range(1, 3)
    ]
    return events


@pytest.fixture
def test_interpretation_set(session_context, test_scene):
    """Create a test interpretation set."""
    with session_context as session:
        interp_set = InterpretationSet.create(
            scene_id=test_scene.id,
            context="Test context",
            oracle_results="Test results",
            is_current=True,
        )
        session.add(interp_set)
        session.flush()

        # Force loading of the interpretations relationship before session closes
        session.refresh(interp_set)
        # Explicitly load the relationship
        _ = list(interp_set.interpretations)
        _ = interp_set.scene

        return interp_set


@pytest.fixture
def test_interpretations(session_context, test_interpretation_set):
    """Create test interpretations."""
    with session_context as session:
        # First, merge the interpretation set into the current session
        # This makes the object part of the current session
        merged_set = session.merge(test_interpretation_set)

        interpretations = [
            Interpretation.create(
                set_id=merged_set.id,  # Use the ID from the merged object
                title=f"Test Interpretation {i}",
                description=f"Test description {i}",
                is_selected=(i == 1),  # First one is selected
            )
            for i in range(1, 3)
        ]
        session.add_all(interpretations)
        session.flush()

        # Refresh the merged object, not the original
        session.refresh(merged_set)

        # Force loading of the relationship
        _ = list(merged_set.interpretations)

        return interpretations


@pytest.fixture
def empty_interpretation_set(session_context, test_scene):
    """Create an empty interpretation set for testing."""
    with session_context as session:
        interp_set = InterpretationSet.create(
            scene_id=test_scene.id,
            context="Empty set context",
            oracle_results="Empty set results",
            is_current=True,
        )
        session.add(interp_set)
        return interp_set


@pytest.fixture
def test_dice_roll(session_context, test_scene):
    """Create a test dice roll."""
    with session_context as session:
        dice_roll = DiceRoll.create(
            notation="2d6+3",
            individual_results=[4, 5],
            modifier=3,
            total=12,
            reason="Test roll",
            scene_id=test_scene.id,
        )
        session.add(dice_roll)
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
    session_context, create_test_game, create_test_act, create_test_scene
):
    """Create a test game with multiple scenes."""
    game = create_test_game(
        name="Game with Scenes", description="A test game with multiple scenes"
    )

    # Create an act for the game
    act = create_test_act(
        game_id=game.id, title="Act with Scenes", description="Test act with scenes"
    )

    # Create scenes for the act
    scenes = []
    for i in range(1, 4):
        scene = create_test_scene(
            act_id=act.id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 2),  # Make the middle scene active
        )
        scenes.append(scene)

    # Refresh objects to ensure relationships are loaded
    with session_context as session:
        session.refresh(game)
        session.refresh(act)

    return game, scenes


@pytest.fixture
def test_game_with_complete_hierarchy(
    session_context,
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources,
):
    """Create a complete game hierarchy with acts, scenes, events, and interpretations.

    This fixture creates a comprehensive test game with multiple acts, scenes, and events
    to test complex relationships and hybrid properties.

    Returns:
        Tuple containing:
        - game: The created game
        - acts: List of created acts
        - scenes: List of created scenes
        - events: List of created events
    """
    # Initialize event sources if needed
    # initialize_event_sources()

    game = create_test_game(
        name="Complete Game", description="A test game with complete hierarchy"
    )

    # Create acts with varying statuses
    acts = []
    for i in range(1, 3):
        act = create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        acts.append(act)

    # Create scenes with varying statuses
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

            # Add events to each scene
            for k in range(1, 3):
                event = create_test_event(
                    scene_id=scene.id,
                    description=f"Event {k} in Scene {j} of Act {i + 1}",
                    source="manual",  # Use source name instead of ID
                )
                events.append(event)

    # Refresh objects to ensure relationships are loaded
    with session_context as session:
        session.refresh(game)
        for act in acts:
            session.refresh(act)
        for scene in scenes:
            session.refresh(scene)

    return game, acts, scenes, events


@pytest.fixture
def test_hybrid_property_game(
    session_context, create_test_game, create_test_act, create_test_scene
):
    """Create a game with specific properties for testing hybrid properties.

    This fixture creates a game with a specific structure designed to test
    hybrid properties and their SQL expressions.

    Returns:
        Dict containing:
        - game: The created game
        - acts: List of created acts
        - scenes: List of created scenes
        - expected_properties: Dict of expected property values for testing
    """
    game = create_test_game(
        name="Hybrid Property Test Game",
        description="Game for testing hybrid properties",
    )

    # Create acts to test has_acts and act_count
    acts = [
        create_test_act(
            game_id=game.id,
            title=f"Act {i}",
            summary=f"Test act {i}",
            is_active=(i == 1),
        )
        for i in range(1, 3)
    ]

    # Create scenes to test has_scenes and scene_count
    scenes = [
        create_test_scene(
            act_id=acts[0].id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 1),
        )
        for i in range(1, 4)
    ]

    # Refresh the objects to ensure relationships are loaded
    with session_context as session:
        session.refresh(game)
        for act in acts:
            session.refresh(act)

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
