"""Common test fixtures for all sologm tests."""

import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sologm.database.session import DatabaseSession
from sologm.models.base import Base
from sologm.models.game import Game
from sologm.models.act import Act
from sologm.models.scene import Scene
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.dice import DiceRoll
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.integrations.anthropic import AnthropicClient

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


# Model factory fixtures
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
def create_test_act(db_session):
    """Factory fixture to create test acts."""

    def _create_act(
        game_id,
        title="Test Act",
        description="A test act",
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
            description=description,
            sequence=sequence,
        )
        act.is_active = is_active
        db_session.add(act)
        db_session.commit()
        return act

    return _create_act


@pytest.fixture
def create_test_scene(db_session):
    """Factory fixture to create test scenes."""

    def _create_scene(
        act_id,
        title="Test Scene",
        description="A test scene",
        sequence=1,
        is_active=True,
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
        db_session.add(scene)
        db_session.commit()
        return scene

    return _create_scene


@pytest.fixture
def create_test_event(db_session):
    """Factory fixture to create test events."""

    def _create_event(game_id, scene_id, description="Test event", source="manual"):
        # Get the source ID from the name
        source_obj = (
            db_session.query(EventSource).filter(EventSource.name == source).first()
        )
        if not source_obj:
            raise ValueError(f"Event source '{source}' not found")

        event = Event.create(
            game_id=game_id,
            scene_id=scene_id,
            description=description,
            source_id=source_obj.id,
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
def test_act(db_session, test_game):
    """Create a test act for the test game."""
    act = Act.create(
        game_id=test_game.id,
        title="Test Act",
        description="A test act",
        sequence=1,
    )
    act.is_active = True
    db_session.add(act)
    db_session.commit()
    return act


@pytest.fixture
def test_scene(db_session, test_act):
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
def test_events(db_session, test_game, test_scene):
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
            game_id=test_game.id,
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


@pytest.fixture(autouse=True)
def initialize_event_sources(db_session):
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
