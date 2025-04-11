"""Shared test fixtures for core module tests."""

import pytest
from typing import Dict, Any, List, Optional, Callable

# Import common fixtures from central conftest
from sologm.tests.conftest import (
    db_engine,
    db_session,
    database_session,
    mock_anthropic_client,
    test_game,
    test_act,
    test_scene,
    test_events,
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
    create_test_game,
    create_test_act,
    create_test_scene,
    create_test_event,
    initialize_event_sources,
)

from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.core.act import ActManager
from sologm.models.act import Act, ActStatus
from sologm.models.scene import Scene, SceneStatus


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
def test_hybrid_expressions(db_session):
    """Test fixture for SQL expressions of hybrid properties.

    This fixture provides a function that can be used to verify that hybrid property
    SQL expressions work correctly in queries.

    Example:
        def test_game_has_acts_expression(db_session, test_hybrid_expressions):
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


# Core-specific fixtures
@pytest.fixture
def game_manager(db_session):
    """Create a GameManager with a test session."""
    return GameManager(session=db_session)


@pytest.fixture
def act_manager(db_session):
    """Create an ActManager with a test session."""
    return ActManager(session=db_session)


@pytest.fixture
def scene_manager(db_session):
    """Create a SceneManager with a test session."""
    return SceneManager(session=db_session)


@pytest.fixture
def event_manager(db_session):
    """Create an EventManager with a test session."""
    return EventManager(session=db_session)


@pytest.fixture
def dice_manager(db_session):
    """Create a DiceManager with a test session."""
    return DiceManager(session=db_session)


@pytest.fixture
def oracle_manager(mock_anthropic_client, db_session):
    """Create an OracleManager with a test session."""
    return OracleManager(anthropic_client=mock_anthropic_client, session=db_session)


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
            description=f"Test act {i}",
            status=ActStatus.ACTIVE if i == 1 else ActStatus.COMPLETED,
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
            description=f"Test act {i}",
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
