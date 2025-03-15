"""
Tests for the GameService class.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from sqlalchemy.orm import Session

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.scene import Scene, SceneStatus
from sologm.rpg_helper.models.scene_event import SceneEvent
from sologm.rpg_helper.models.poll import Poll, PollStatus
from sologm.rpg_helper.models.game.errors import (
    SceneNotFoundError, PollNotFoundError
)
from sologm.rpg_helper.services.game.game_service import GameService
from sologm.rpg_helper.db.config import get_session


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_game():
    """Create a mock game for testing."""
    game = MagicMock(spec=Game)
    game.id = "test-game-id"
    game.name = "Test Game"
    game.game_type = GameType.STANDARD
    game.updated_at = datetime.now()
    # Initialize empty collections
    game.scenes = []
    game.polls = []
    return game


@pytest.fixture
def game_service(mock_game, mock_session):
    """Create a GameService instance with a mock game."""
    # Patch the get_session function to return our mock session
    with patch('sologm.rpg_helper.services.game.game_service.get_session', return_value=mock_session):
        service = GameService(mock_game)
        return service


class TestGameService:
    """Tests for the GameService class."""

    def test_init(self, mock_game):
        """Test initialization of GameService."""
        service = GameService(mock_game)
        assert service.game == mock_game

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_create_scene(self, mock_object_session, game_service, mock_game, mock_session):
        """Test creating a scene."""
        # Setup
        mock_object_session.return_value = mock_session
        title = "Test Scene"
        description = "This is a test scene"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = "test-scene-id"
        mock_scene.title = title
        mock_scene.description = description
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        
        # Mock the Scene constructor
        with patch('sologm.rpg_helper.services.game.game_service.Scene', return_value=mock_scene) as mock_scene_class:
            # Execute
            result = game_service.create_scene(title, description)
            
            # Verify
            assert result == mock_scene
            mock_scene_class.assert_called_once_with(
                title=title,
                description=description,
                game_id=mock_game.id
            )
            mock_session.add.assert_called_once_with(mock_scene)
            mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_scene_not_found(self, mock_object_session, game_service, mock_session):
        """Test getting a scene that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "non-existent-scene"
        # Ensure game's scenes collection is empty
        game_service.game.scenes = []
        # Ensure database query returns None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(SceneNotFoundError) as excinfo:
            game_service.get_scene(scene_id)
        
        assert scene_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter_by.assert_called_once_with(
            id=scene_id,
            game_id=game_service.game.id
        )

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_scene_from_collection(self, mock_object_session, game_service):
        """Test getting a scene that exists in the game's collection."""
        # Setup
        scene_id = "existing-scene"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        game_service.game.scenes = [mock_scene]
        
        # Execute
        result = game_service.get_scene(scene_id)
        
        # Verify
        assert result == mock_scene
        # Should not query database since found in collection
        mock_object_session.assert_not_called()

    @patch('sologm.rpg_helper.services.game.game_service.get_session')
    def test_for_game_id(self, mock_get_session, mock_game, mock_session):
        """Test creating a service for a game by ID."""
        # Setup
        game_id = "test-game-id"
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_game
        
        # Execute
        with patch('sologm.rpg_helper.services.game.game_service.close_session') as mock_close_session:
            service = GameService.for_game_id(game_id)
        
        # Verify
        assert service.game == mock_game
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Game)
        mock_session.query.return_value.filter_by.assert_called_once_with(id=game_id)
        mock_close_session.assert_called_once_with(mock_session)

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_create_poll(self, mock_object_session, game_service, mock_game, mock_session):
        """Test creating a poll."""
        # Setup
        mock_object_session.return_value = mock_session
        question = "Test Question"
        options = ["Option 1", "Option 2"]
        mock_poll = MagicMock(spec=Poll)
        mock_poll.question = question
        mock_poll.options = options
        mock_poll.game_id = mock_game.id
        mock_poll.status = PollStatus.OPEN
        
        # Mock the Poll constructor
        with patch('sologm.rpg_helper.services.game.game_service.Poll', return_value=mock_poll) as mock_poll_class:
            # Execute
            result = game_service.create_poll(question, options)
            
            # Verify
            assert result == mock_poll
            mock_poll_class.assert_called_once_with(
                game_id=mock_game.id,
                question=question,
                options=options
            )
            mock_session.add.assert_called_once_with(mock_poll)
            mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_poll_not_found(self, mock_object_session, game_service, mock_session):
        """Test getting a poll that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "nonexistent-poll-id"
        # Ensure game's polls collection is empty
        game_service.game.polls = []
        # Ensure database query returns None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(PollNotFoundError) as excinfo:
            game_service.get_poll(poll_id)
        
        assert poll_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter_by.assert_called_once_with(
            id=poll_id,
            game_id=game_service.game.id
        )

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_poll_from_collection(self, mock_object_session, game_service):
        """Test getting a poll that exists in the game's collection."""
        # Setup
        poll_id = "existing-poll"
        mock_poll = MagicMock(spec=Poll)
        mock_poll.id = poll_id
        game_service.game.polls = [mock_poll]
        
        # Execute
        result = game_service.get_poll(poll_id)
        
        # Verify
        assert result == mock_poll
        # Should not query database since found in collection
        mock_object_session.assert_not_called()