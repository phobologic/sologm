"""
Tests for game initialization command.
"""
import os
import tempfile
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.commands.game.init import InitGameCommand, InitGameHandler
from sologm.commands.contexts import CLIContext, SlackContext
from sologm.commands.results import CommandResult
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.game.errors import ChannelGameExistsError
from sologm.rpg_helper.models.user import User
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.db.config import get_session, close_session, set_session_factory

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def engine(db_path):
    """Create a test database engine."""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    BaseModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def session_factory(engine):
    """Create a session factory."""
    factory = sessionmaker(bind=engine)
    set_session_factory(factory)
    return factory

@pytest.fixture
def session(session_factory):
    """Get a database session."""
    session = get_session()
    yield session
    close_session(session)

@pytest.fixture
def handler():
    """Create a command handler."""
    return InitGameHandler()

@pytest.fixture
def cli_context():
    """Create a CLI context."""
    return CLIContext(
        working_directory="/test/games",
        user="testuser"
    )

@pytest.fixture
def slack_context():
    """Create a Slack context."""
    return SlackContext(
        channel_id="test_channel",
        team_id="test_team",
        user_id="test_user"
    )

def test_can_handle(handler):
    """Test that handler can handle InitGameCommand."""
    command = InitGameCommand(
        game_system="standard",
        name="Test Game",
        channel_id="test_channel",
        workspace_id="cli:/test/games"
    )
    assert handler.can_handle(command)

def test_cannot_handle_other_command(handler):
    """Test that handler cannot handle other commands."""
    command = Mock()
    assert not handler.can_handle(command)

def test_init_game_standard(handler, cli_context, session):
    """Test initializing a standard game."""
    command = InitGameCommand(
        game_system="standard",
        name="Test Game",
        channel_id="test_channel",
        workspace_id="cli:/test/games",  # Match CLI context workspace_id
        description="A test game"
    )
    
    result = handler.handle(command, cli_context)
    
    assert result.success
    assert "Test Game" in result.message
    assert "standard" in result.message.lower()
    assert "A test game" in result.message
    
    # Verify game was created in database
    game = session.query(Game).filter_by(name="Test Game").first()
    assert game is not None
    assert game.game_type == GameType.STANDARD
    assert game.channel_id == "test_channel"
    assert game.workspace_id == "cli:/test/games"
    assert game.description == "A test game"

def test_init_game_mythic(handler, cli_context, session):
    """Test initializing a mythic game."""
    command = InitGameCommand(
        game_system="mythic",
        name="Mythic Game",
        channel_id="mythic_channel",
        workspace_id="cli:/test/games"  # Match CLI context workspace_id
    )
    
    result = handler.handle(command, cli_context)
    
    assert result.success
    assert "Mythic Game" in result.message
    assert "mythic" in result.message.lower()
    
    # Verify game was created in database
    game = session.query(Game).filter_by(name="Mythic Game").first()
    assert game is not None
    assert game.game_type == GameType.MYTHIC
    assert game.channel_id == "mythic_channel"
    assert game.workspace_id == "cli:/test/games"

def test_init_game_invalid_system(handler, cli_context):
    """Test initializing a game with invalid system."""
    command = InitGameCommand(
        game_system="invalid",
        name="Invalid Game",
        channel_id="test_channel",
        workspace_id="cli:/test/games"  # Match CLI context workspace_id
    )
    
    result = handler.handle(command, cli_context)
    
    assert not result.success
    assert "Invalid game system" in result.message
    assert "standard" in result.message.lower()
    assert "mythic" in result.message.lower()

def test_init_game_existing_channel(handler, cli_context, session):
    """Test initializing a game in a channel that already has one."""
    # Create initial game
    game = Game(
        name="Existing Game",
        channel_id="test_channel",
        workspace_id="cli:/test/games",  # Match CLI context workspace_id
        game_type=GameType.STANDARD  # Set game type
    )
    session.add(game)
    session.commit()
    
    # Try to create another game in same channel
    command = InitGameCommand(
        game_system="standard",
        name="New Game",
        channel_id="test_channel",  # Same channel as existing game
        workspace_id="cli:/test/games"  # Match CLI context workspace_id
    )
    
    result = handler.handle(command, cli_context)
    
    assert not result.success
    assert "already exists" in result.message
    assert "Existing Game" in result.message
    assert result.data is not None
    assert result.data.get("existing_game_id") == game.id
    assert result.data.get("existing_game_name") == "Existing Game"

def test_init_game_with_user(handler, slack_context, session):
    """Test initializing a game with a user."""
    # Create user
    user = User(
        id="test_user",
        username="test_user",
        display_name="Test User"
    )
    session.add(user)
    session.commit()
    
    command = InitGameCommand(
        game_system="standard",
        name="User Game",
        channel_id="test_channel",
        workspace_id="slack:test_team:test_channel",  # Match Slack context workspace_id
        user_id="test_user"
    )
    
    result = handler.handle(command, slack_context)
    
    assert result.success
    
    # Verify game was created and user is a member
    game = session.query(Game).filter_by(name="User Game").first()
    assert game is not None
    assert len(game.members) == 1
    assert game.members[0].id == "test_user" 