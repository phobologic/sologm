"""Common test fixtures for all sologm tests."""

import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.database.session import DatabaseSession
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.act import Act
from sologm.models.base import Base
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus

logger = logging.getLogger(__name__)


# Database fixtures
@pytest.fixture
def db_engine():
    """Create a new in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    logger.debug("Initializing db_session")
    session = Session(bind=db_engine)
    logger.debug("Yielding db session.")
    yield session
    logger.debug("Closing db session.")
    session.close()


@pytest.fixture
def database_session(db_engine):
    """Create a DatabaseSession instance for testing."""
    db_session = DatabaseSession(engine=db_engine)
    old_instance = DatabaseSession._instance
    DatabaseSession._instance = db_session
    yield db_session
    DatabaseSession._instance = old_instance


# Mock fixtures
@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


# Manager fixtures
@pytest.fixture(autouse=True)
def setup_database_session(db_engine):
    """Configure DatabaseSession singleton for testing."""
    # Create a new DatabaseSession with the test engine
    test_db_session = DatabaseSession(engine=db_engine)

    # Save and replace the singleton instance
    old_instance = DatabaseSession._instance
    DatabaseSession._instance = test_db_session

    yield

    # Restore the original singleton
    DatabaseSession._instance = old_instance


@pytest.fixture
def game_manager():
    """Create a GameManager for testing."""
    return GameManager()


@pytest.fixture
def act_manager(game_manager):
    """Create an ActManager with a game manager."""
    return ActManager(game_manager=game_manager)


@pytest.fixture
def scene_manager(act_manager):
    """Create a SceneManager with an act manager."""
    return SceneManager(act_manager=act_manager)


@pytest.fixture
def event_manager(scene_manager):
    """Create an EventManager with a scene manager."""
    return EventManager(scene_manager=scene_manager)


@pytest.fixture
def dice_manager(scene_manager):
    """Create a DiceManager with a scene manager."""
    return DiceManager(scene_manager=scene_manager)


@pytest.fixture
def oracle_manager(scene_manager, mock_anthropic_client):
    """Create an OracleManager with a scene manager and mock client."""
    return OracleManager(
        scene_manager=scene_manager,
        anthropic_client=mock_anthropic_client,
    )


# Model factory fixtures
@pytest.fixture
def create_test_game(database_session):
    """Factory fixture to create test games."""

    def _create_game(name="Test Game", description="A test game", is_active=True):
        game = Game.create(name=name, description=description)
        game.is_active = is_active
        db_session.add(game)
        db_session.commit()
        return game

    return _create_game


@pytest.fixture
def create_test_act(database_session):
    """Factory fixture to create test acts."""

    def _create_act(
        game_id,
        title="Test Act",
        summary="A test act",
        sequence=1,
        is_active=True,
    ):
        # If creating an active act, deactivate all other acts for this game first
        if is_active:
            db_session.query(Act).filter(Act.game_id == game_id).update(
                {Act.is_active: False}
            )
        act = Act.create(
            game_id=game_id,
            title=title,
            summary=summary,
            sequence=sequence,
        )
        act.is_active = is_active
        db_session.add(act)
        db_session.commit()
        return act

    return _create_act


@pytest.fixture
def create_test_scene(database_session):
    """Factory fixture to create test scenes."""

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
        is_active=True,
        status=SceneStatus.ACTIVE,
    ):
        # If creating an active scene, deactivate all other scenes for this act first
        if is_active:
            db_session.query(Scene).filter(Scene.act_id == act_id).update(
                {Scene.is_active: False}
            )
        scene = Scene.create(
            act_id=act_id,
            title=title,
            description=description,
            sequence=sequence,
        )
        scene.is_active = is_active
        scene.status = status
        db_session.add(scene)
        db_session.commit()
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(database_session):
    """Factory fixture to create test events."""

    def _create_event(
        scene_id, description="Test event", source_id=1, interpretation_id=None
    ):
        event = Event.create(
            scene_id=scene_id,
            description=description,
            source_id=source_id,
            interpretation_id=interpretation_id,
        )
        db_session.add(event)
        db_session.commit()
        return event

    return _create_event


# Common test objects
@pytest.fixture
def test_game(create_test_game):
    """Create a test game."""
    return create_test_game()


@pytest.fixture
def test_act(database_session, test_game):
    """Create a test act for the test game."""
    act = Act.create(
        game_id=test_game.id,
        title="Test Act",
        summary="A test act",
        sequence=1,
    )
    act.is_active = True
    db_session.add(act)
    db_session.commit()
    return act


@pytest.fixture
def test_scene(database_session, test_act):
    """Create a test scene for the test act."""
    scene = Scene.create(
        act_id=test_act.id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
    )
    scene.is_active = True
    db_session.add(scene)
    db_session.commit()
    return scene


@pytest.fixture
def test_events(database_session, test_scene):
    """Create test events."""
    # Get the source ID for "manual"
    source_obj = (
        db_session.query(EventSource).filter(EventSource.name == "manual").first()
    )
    if not source_obj:
        # Create it if it doesn't exist
        source_obj = EventSource.create(name="manual")
        db_session.add(source_obj)
        db_session.commit()

    events = [
        Event.create(
            scene_id=test_scene.id,
            description=f"Test event {i}",
            source_id=source_obj.id,
        )
        for i in range(1, 3)
    ]
    db_session.add_all(events)
    db_session.commit()
    return events


@pytest.fixture
def test_interpretation_set(database_session, test_scene):
    """Create a test interpretation set."""
    interp_set = InterpretationSet.create(
        scene_id=test_scene.id,
        context="Test context",
        oracle_results="Test results",
        is_current=True,
    )
    db_session.add(interp_set)
    db_session.commit()
    return interp_set


@pytest.fixture
def test_interpretations(database_session, test_interpretation_set):
    """Create test interpretations."""
    interpretations = [
        Interpretation.create(
            set_id=test_interpretation_set.id,
            title=f"Test Interpretation {i}",
            description=f"Test description {i}",
            is_selected=(i == 1),  # First one is selected
        )
        for i in range(1, 3)
    ]
    db_session.add_all(interpretations)
    db_session.commit()
    return interpretations


@pytest.fixture
def test_dice_roll(database_session, test_scene):
    """Create a test dice roll."""
    dice_roll = DiceRoll.create(
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
        total=12,
        reason="Test roll",
        scene_id=test_scene.id,
    )
    db_session.add(dice_roll)
    db_session.commit()
    return dice_roll


@pytest.fixture(autouse=True)
def initialize_event_sources(database_session):
    """Initialize event sources for testing."""
    sources = ["manual", "oracle", "dice"]
    for source_name in sources:
        existing = (
            db_session.query(EventSource)
            .filter(EventSource.name == source_name)
            .first()
        )
        if not existing:
            source = EventSource.create(name=source_name)
            db_session.add(source)
    db_session.commit()


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
def test_hybrid_expressions(database_session):
    """Test fixture for SQL expressions of hybrid properties.

    This fixture provides a function that can be used to verify that hybrid property
    SQL expressions work correctly in queries.

    Example:
        def test_game_has_acts_expression(database_session, test_hybrid_expressions):
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
        property_expr = getattr(model_class, property_name)
        query = db_session.query(model_class).filter(property_expr == filter_condition)
        result_count = query.count()
        assert result_count == expected_count, (
            f"Expected {expected_count} results for {model_class.__name__}.{property_name} == {filter_condition}, "
            f"got {result_count}"
        )

    return _test_expression


# Complex test fixtures
@pytest.fixture
def test_game_with_scenes(
    db_session, create_test_game, create_test_act, create_test_scene
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
            sequence=i,
            is_active=(i == 2),  # Make the middle scene active
        )
        scenes.append(scene)

    # Refresh objects to ensure relationships are loaded
    db_session.refresh(game)
    db_session.refresh(act)

    return game, scenes


@pytest.fixture
def test_game_with_complete_hierarchy(
    db_session,
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
    initialize_event_sources()

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
                sequence=j,
                status=SceneStatus.ACTIVE if j == 1 else SceneStatus.COMPLETED,
                is_active=(j == 1),
            )
            scenes.append(scene)

            # Add events to each scene
            for k in range(1, 3):
                event = create_test_event(
                    scene_id=scene.id,
                    description=f"Event {k} in Scene {j} of Act {i + 1}",
                    source_id=1,  # Manual source
                )
                events.append(event)

    # Refresh objects to ensure relationships are loaded
    db_session.refresh(game)
    for act in acts:
        db_session.refresh(act)
    for scene in scenes:
        db_session.refresh(scene)

    return game, acts, scenes, events


@pytest.fixture
def test_hybrid_property_game(
    db_session, create_test_game, create_test_act, create_test_scene
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
            sequence=i,
            is_active=(i == 1),
        )
        for i in range(1, 4)
    ]

    # Refresh the objects to ensure relationships are loaded
    db_session.refresh(game)
    for act in acts:
        db_session.refresh(act)

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
