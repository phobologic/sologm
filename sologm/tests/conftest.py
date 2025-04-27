"""Common test fixtures for all sologm tests."""

import logging
from typing import Any, List  # Added List
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import the factory function
from sologm.core.factory import create_all_managers
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.base import Base
from sologm.models.dice import DiceRoll
from sologm.models.event import Event  # Added Event import
from sologm.models.event_source import EventSource
from sologm.models.game import Game  # Added Game import
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus  # Added Scene import
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


# Step 4.1: Remove db_session Fixture


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
# Step 4.2: Remove Individual Manager Fixtures


# Step 4.4: Refactor Factory Fixtures (`create_test_*`)
@pytest.fixture
def create_test_game():
    """Factory fixture to create test games using the GameManager."""

    def _create_game(
        session: Session, name="Test Game", description="A test game", is_active=True
    ) -> Game:
        managers = create_all_managers(session)
        game = managers.game.create_game(name, description, is_active=is_active)
        # No merge needed, object is already session-bound
        try:
            # Refresh relationships using the passed-in session
            session.refresh(game, attribute_names=["acts"])
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_game factory: {e}"
            )
        return game  # Return the session-bound, refreshed object

    return _create_game


@pytest.fixture
def create_test_act():
    """Factory fixture to create test acts using the ActManager."""

    def _create_act(
        session: Session,
        game_id: str,
        title="Test Act",
        summary="A test act",
        is_active=True,
        sequence=None,
    ):
        managers = create_all_managers(session)
        act = managers.act.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )
        # If sequence was specified, update it directly using the correct session
        if sequence is not None:
            act.sequence = sequence
            session.add(act)
            session.flush()

        # No merge needed
        try:
            # Refresh relationships using the passed-in session
            session.refresh(act, attribute_names=["scenes", "game"])
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_act factory: {e}"
            )
        return act

    return _create_act


@pytest.fixture
def create_test_scene():
    """Factory fixture to create test scenes using the SceneManager."""

    def _create_scene(
        session: Session,
        act_id: str,
        title="Test Scene",
        description="A test scene",
        is_active=True,
        status=SceneStatus.ACTIVE,
    ) -> Scene:
        managers = create_all_managers(session)
        scene = managers.scene.create_scene(
            act_id=act_id,
            title=title,
            description=description,
            make_active=is_active,
        )
        if status == SceneStatus.COMPLETED:
            # Use manager for completion logic (it uses the correct session)
            managers.scene.complete_scene(scene.id)
            # Re-fetch the scene to get updated state
            scene = managers.scene.get_scene(scene.id)

        # No merge needed
        try:
            # Refresh relationships using the passed-in session
            session.refresh(
                scene,
                attribute_names=["act", "events", "interpretations", "dice_rolls"],
            )
            if scene.act:
                session.refresh(scene.act, attribute_names=["game"])
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_scene factory: {e}"
            )
        return scene

    return _create_scene


@pytest.fixture
def create_test_event():
    """Factory fixture to create test events using the EventManager."""

    def _create_event(
        session: Session,
        scene_id: str,
        description="Test event",
        source="manual",
        interpretation_id=None,
    ) -> Event:
        managers = create_all_managers(session)
        event = managers.event.add_event(
            description=description,
            scene_id=scene_id,
            source=source,
            interpretation_id=interpretation_id,
        )
        # No merge needed
        try:
            # Refresh relationships using the passed-in session
            session.refresh(
                event, attribute_names=["scene", "source", "interpretation"]
            )
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_event factory: {e}"
            )
        return event

    return _create_event


# Step 4.5: Remove Object Fixtures (test_game, test_act, test_scene, test_events, etc.)
# Tests should now create these objects directly using the refactored factory fixtures
# within a `with session_context as session:` block.


# Step 4.5: Remove Complex Fixtures (test_game_with_scenes, etc.)
# Tests requiring complex setups should build them using the refactored factory fixtures
# within their own `with session_context as session:` block.


# Fixtures that remain valid or are updated
@pytest.fixture(autouse=True)
def initialize_event_sources(session_context):
    """Initialize event sources for testing using the session_context."""
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
    create_test_game,
    create_test_act,
    create_test_scene,
    # Remove db_session injection
):
    """Create a test game with multiple scenes, attached to the test's session."""
    # Use factories which now return session-bound, refreshed objects
    game = create_test_game(
        name="Game with Scenes", description="A test game with multiple scenes"
    )
    act = create_test_act(
        game_id=game.id,
        title="Act with Scenes",
        summary="Test act with scenes",
    )
    scenes = []
    for i in range(1, 4):
        scene = create_test_scene(
            act_id=act.id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            is_active=(i == 2),
        )
        scenes.append(scene)

    # No explicit refresh needed here, component fixtures handle it
    return game, scenes


@pytest.fixture
def test_game_with_complete_hierarchy(
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources,  # Keep this
    # Remove db_session injection
):
    """Create a complete game hierarchy, attached to the test's session."""
    # Use factories which now return session-bound, refreshed objects
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

    # No explicit refresh needed here, component fixtures handle it
    return game, acts, scenes, events


@pytest.fixture
def test_hybrid_property_game(
    create_test_game,
    create_test_act,
    create_test_scene,
    # Remove db_session injection
):
    """Create a game for testing hybrid properties, attached to the test's session."""
    # Use factories which now return session-bound, refreshed objects
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

    # No explicit refresh needed here, component fixtures handle it
    # Expected properties remain the same
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
# The duplicate factory fixtures and object fixtures below this line have been removed
# as part of the cleanup in Step 4.5.


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


# Complex test fixtures like test_game_with_scenes, test_game_with_complete_hierarchy,
# and test_hybrid_property_game have been removed.
# Tests requiring these setups should now build them within the test function
# using the refactored factory fixtures and the session_context.
