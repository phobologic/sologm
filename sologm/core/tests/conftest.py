"""Shared test fixtures for core module tests."""

from logging import getLogger
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.database.session import DatabaseSession
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.base import Base
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

logger = getLogger(__name__)


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    logger.debug("Initializing db_session")
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    logger.debug("Yielding db session.")

    yield session

    logger.debug("Closing db session.")
    session.close()
    if transaction.is_active:
        logger.debug("Rolling back active transactions.")
        transaction.rollback()
    logger.debug("Closing db connection.")
    connection.close()


@pytest.fixture
def database_session(db_engine):
    """Create a DatabaseSession instance for testing."""
    db_session = DatabaseSession(engine=db_engine)
    old_instance = DatabaseSession._instance
    DatabaseSession._instance = db_session

    yield db_session

    DatabaseSession._instance = old_instance


@pytest.fixture
def game_manager(db_session):
    """Create a GameManager with a test session."""
    return GameManager(session=db_session)


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
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def oracle_manager(mock_anthropic_client, db_session):
    """Create an OracleManager with a test session."""
    return OracleManager(anthropic_client=mock_anthropic_client, session=db_session)


@pytest.fixture
def test_game(db_session):
    """Create a test game."""
    game = Game.create(
        name="Test Game",
        description="A test game",
    )
    game.is_active = True
    db_session.add(game)
    db_session.commit()
    return game


@pytest.fixture
def test_scene(db_session, test_game):
    """Create a test scene."""
    scene = Scene.create(
        game_id=test_game.id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
    )
    scene.is_active = True
    db_session.add(scene)
    db_session.commit()
    return scene


@pytest.fixture
def test_events(db_session, test_game, test_scene):
    """Create test events."""
    events = [
        Event.create(
            game_id=test_game.id,
            scene_id=test_scene.id,
            description=f"Test event {i}",
            source="manual",
        )
        for i in range(1, 3)
    ]
    db_session.add_all(events)
    db_session.commit()
    return events


@pytest.fixture
def test_interpretation_set(db_session, test_scene):
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
def test_interpretations(db_session, test_interpretation_set):
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
def test_dice_roll(db_session, test_scene):
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


@pytest.fixture
def test_game_with_scenes(db_session):
    """Create a test game with multiple scenes."""
    game = Game.create(
        name="Game with Scenes",
        description="A test game with multiple scenes",
    )
    game.is_active = True
    db_session.add(game)
    db_session.flush()

    scenes = []
    for i in range(1, 4):
        scene = Scene.create(
            game_id=game.id,
            title=f"Scene {i}",
            description=f"Test scene {i}",
            sequence=i,
        )
        scene.is_active = i == 2  # Make the middle scene active
        scenes.append(scene)

    db_session.add_all(scenes)
    db_session.commit()

    return game, scenes


# Factory fixtures for creating multiple test objects
@pytest.fixture
def create_test_game(db_session):
    """Factory fixture to create test games."""

    def _create_game(name="Test Game", description="A test game", is_active=True):
        game = Game.create(name=name, description=description)
        game.is_active = is_active
        db_session.add(game)
        db_session.commit()
        return game

    return _create_game


@pytest.fixture
def create_test_scene(db_session):
    """Factory fixture to create test scenes."""

    def _create_scene(
        game_id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
        is_active=True,
    ):
        scene = Scene.create(
            game_id=game_id,
            title=title,
            description=description,
            sequence=sequence,
        )
        scene.is_active = is_active
        db_session.add(scene)
        db_session.commit()
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(db_session):
    """Factory fixture to create test events."""

    def _create_event(game_id, scene_id, description="Test event", source="manual"):
        event = Event.create(
            game_id=game_id, scene_id=scene_id, description=description, source=source
        )
        db_session.add(event)
        db_session.commit()
        return event

    return _create_event
