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
from sologm.rpg_helper.models.poll import Poll, PollStatus, Vote
from sologm.rpg_helper.models.game.errors import (
    SceneNotFoundError, InvalidSceneStateError, SceneStateTransitionError,
    PollNotFoundError, PollClosedError
)
from sologm.rpg_helper.services.game.game_service import GameService


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
    return game


@pytest.fixture
def game_service(mock_game, mock_session):
    """Create a GameService instance with a mock game."""
    # Set up the session factory
    GameService.set_session_factory(lambda: mock_session)
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
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        
        # Mock the Scene constructor
        with patch('sologm.rpg_helper.services.game.game_service.Scene', return_value=mock_scene) as mock_scene_class:
            # Execute
            result = game_service.create_scene(title, description)
            
            # Verify
            assert result == mock_scene
            mock_scene_class.assert_called_once_with(
                game_id=mock_game.id,
                title=title,
                description=description,
                status=SceneStatus.ACTIVE
            )
            mock_session.add.assert_called_once_with(mock_scene)
            mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_scene_not_found(self, mock_object_session, game_service, mock_session):
        """Test getting a scene that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "non-existent-scene"
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(SceneNotFoundError) as excinfo:
            game_service.get_scene(scene_id)
        
        assert scene_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_active_scene(self, mock_object_session, game_service, mock_game, mock_session):
        """Test getting the active scene."""
        # Setup
        mock_object_session.return_value = mock_session
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = "test-scene-id"
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute
        result = game_service.get_active_scene()
        
        # Verify
        assert result == mock_scene
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_active_scene_none(self, mock_object_session, game_service, mock_session):
        """Test getting the active scene when none exists."""
        # Setup
        mock_object_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = game_service.get_active_scene()
        
        # Verify
        assert result is None
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_complete_scene(self, mock_object_session, game_service, mock_session):
        """Test completing a scene."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        mock_session.commit.return_value = None
        
        # Execute
        result = game_service.complete_scene(scene_id)
        
        # Verify
        assert result == mock_scene
        assert mock_scene.status == SceneStatus.COMPLETED
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_complete_scene_not_found(self, mock_object_session, game_service, mock_session):
        """Test completing a scene that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "nonexistent-scene-id"
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(SceneNotFoundError) as excinfo:
            game_service.complete_scene(scene_id)
        
        assert scene_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_complete_scene_already_completed(self, mock_object_session, game_service, mock_session):
        """Test completing a scene that is already completed."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.COMPLETED
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute & Verify
        with pytest.raises(InvalidSceneStateError) as excinfo:
            game_service.complete_scene(scene_id)
        
        assert scene_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_complete_scene_invalid_transition(self, mock_object_session, game_service, mock_session):
        """Test completing a scene that is not in ACTIVE state."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.COMPLETED
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute & Verify
        with pytest.raises(SceneStateTransitionError) as excinfo:
            game_service.complete_scene(scene_id)
        
        assert scene_id in str(excinfo.value)
        assert SceneStatus.COMPLETED.value in str(excinfo.value)
        assert SceneStatus.ACTIVE.value in str(excinfo.value)
        assert "cannot transition from" in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_add_scene_event(self, mock_object_session, game_service, mock_session):
        """Test adding an event to a scene."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        event_text = "Test event"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        mock_event = MagicMock(spec=SceneEvent)
        mock_event.text = event_text
        
        # Mock the SceneEvent constructor
        with patch('sologm.rpg_helper.services.game.game_service.SceneEvent', return_value=mock_event) as mock_event_class:
            # Execute
            result = game_service.add_scene_event(scene_id, event_text)
            
            # Verify
            assert result == mock_event
            mock_event_class.assert_called_once_with(
                scene_id=scene_id,
                text=event_text
            )
            mock_session.add.assert_called_once_with(mock_event)
            mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_add_scene_event_not_found(self, mock_object_session, game_service, mock_session):
        """Test adding an event to a scene that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "nonexistent-scene-id"
        event_text = "Test event"
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(SceneNotFoundError) as excinfo:
            game_service.add_scene_event(scene_id, event_text)
        
        assert scene_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_scene(self, mock_object_session, game_service, mock_session):
        """Test getting a scene."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute
        result = game_service.get_scene(scene_id)
        
        # Verify
        assert result == mock_scene
        mock_session.query.assert_called_once_with(Scene)
        mock_session.query.return_value.filter.assert_called_once()

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
                options=options,
                status=PollStatus.OPEN
            )
            mock_session.add.assert_called_once_with(mock_poll)
            mock_session.commit.assert_called_once()
            assert mock_game.updated_at > datetime.now() - timedelta(seconds=1)

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_poll(self, mock_object_session, game_service, mock_session):
        """Test getting a poll."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "test-poll-id"
        mock_poll = MagicMock(spec=Poll)
        mock_poll.id = poll_id
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poll
        
        # Execute
        result = game_service.get_poll(poll_id)
        
        # Verify
        assert result == mock_poll
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_get_poll_not_found(self, mock_object_session, game_service, mock_session):
        """Test getting a poll that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "nonexistent-poll-id"
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(PollNotFoundError) as excinfo:
            game_service.get_poll(poll_id)
        
        assert poll_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_close_poll(self, mock_object_session, game_service, mock_session):
        """Test closing a poll."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "test-poll-id"
        mock_poll = MagicMock(spec=Poll)
        mock_poll.id = poll_id
        mock_poll.status = PollStatus.OPEN
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poll
        mock_session.commit.return_value = None
        
        # Execute
        result = game_service.close_poll(poll_id)
        
        # Verify
        assert result == mock_poll
        assert mock_poll.status == PollStatus.CLOSED
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter.assert_called_once()
        mock_session.commit.assert_called_once()
        assert mock_game.updated_at > datetime.now() - timedelta(seconds=1)

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_close_poll_not_found(self, mock_object_session, game_service, mock_session):
        """Test closing a poll that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "nonexistent-poll-id"
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(PollNotFoundError) as excinfo:
            game_service.close_poll(poll_id)
        
        assert poll_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_add_vote(self, mock_object_session, game_service, mock_game, mock_session):
        """Test adding a vote to a poll."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "test-poll-id"
        user_id = "test-user-id"
        option_index = 0
        mock_poll = MagicMock(spec=Poll)
        mock_poll.id = poll_id
        mock_poll.status = PollStatus.OPEN
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poll
        mock_session.commit.return_value = None
        
        # Mock the Vote constructor
        mock_vote = MagicMock(spec=Vote)
        with patch('sologm.rpg_helper.services.game.game_service.Vote', return_value=mock_vote) as mock_vote_class:
            # Execute
            result = game_service.add_vote(poll_id, user_id, option_index)
            
            # Verify
            assert result == mock_vote
            mock_vote_class.assert_called_once_with(
                poll_id=poll_id,
                user_id=user_id,
                option_index=option_index
            )
            mock_session.add.assert_called_once_with(mock_vote)
            mock_session.commit.assert_called_once()
            assert mock_game.updated_at > datetime.now() - timedelta(seconds=1)

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_add_vote_not_found(self, mock_object_session, game_service, mock_session):
        """Test adding a vote to a poll that doesn't exist."""
        # Setup
        mock_object_session.return_value = mock_session
        poll_id = "nonexistent-poll-id"
        user_id = "test-user-id"
        option_index = 0
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(PollNotFoundError) as excinfo:
            game_service.add_vote(poll_id, user_id, option_index)
        
        assert poll_id in str(excinfo.value)
        mock_session.query.assert_called_once_with(Poll)
        mock_session.query.return_value.filter.assert_called_once()

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_complete_scene_success(self, mock_object_session, game_service, mock_session):
        """Test successfully completing an active scene."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute
        result = game_service.complete_scene(scene_id)
        
        # Verify
        assert result == mock_scene
        assert mock_scene.status == SceneStatus.COMPLETED
        mock_session.commit.assert_called_once()
        assert mock_scene.updated_at > datetime.now() - timedelta(seconds=1)

    @patch('sologm.rpg_helper.services.game.game_service.object_session')
    def test_abandon_scene_success(self, mock_object_session, game_service, mock_session):
        """Test successfully abandoning an active scene."""
        # Setup
        mock_object_session.return_value = mock_session
        scene_id = "test-scene-id"
        mock_scene = MagicMock(spec=Scene)
        mock_scene.id = scene_id
        mock_scene.status = SceneStatus.ACTIVE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Execute
        result = game_service.abandon_scene(scene_id)
        
        # Verify
        assert result == mock_scene
        assert mock_scene.status == SceneStatus.ABANDONED
        mock_session.commit.assert_called_once()
        assert mock_scene.updated_at > datetime.now() - timedelta(seconds=1) 