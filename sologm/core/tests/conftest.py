"""Shared test fixtures for core module tests."""

import pytest

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

    return game, scenes
