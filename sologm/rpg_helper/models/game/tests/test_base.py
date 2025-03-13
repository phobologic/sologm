"""
Tests for the base game model.
"""
import pytest
from unittest.mock import MagicMock, patch, call, PropertyMock
from datetime import datetime

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Table, Boolean, Enum
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.game.errors import ChannelGameExistsError
from sologm.rpg_helper.db.config import set_session_factory, get_session, close_session


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def game_data():
    """Create sample game data for testing."""
    return {
        "id": "test-game-id",
        "name": "Test Game",
        "description": "A test game",
        "channel_id": "test-channel-id",
        "workspace_id": "test-workspace-id",
        "game_type": GameType.STANDARD,
        "is_active": True  # Add default value
    }


@pytest.fixture
def game(game_data):
    """Create a sample game for testing."""
    return Game(**game_data)


class TestGameModel:
    """Tests for the Game model."""
    
    @pytest.fixture(autouse=True)
    def setup_session_factory(self, mock_session):
        """Set up the session factory before each test."""
        # Create a session factory that returns our mock session
        session_factory = MagicMock(return_value=mock_session)
        
        # Patch both the session factory and the session management functions
        with patch('sologm.rpg_helper.db.config._session_factory', session_factory), \
             patch('sologm.rpg_helper.db.config.get_session', return_value=mock_session), \
             patch('sologm.rpg_helper.db.config.close_session') as self.mock_close_session, \
             patch('sologm.rpg_helper.models.game.base.object_session') as self.mock_object_session:
            yield
    
    def test_inheritance(self):
        """Test that Game inherits from BaseModel."""
        from sologm.rpg_helper.models.base import BaseModel
        assert issubclass(Game, BaseModel)
    
    def test_columns(self):
        """Test that Game has the expected columns."""
        from sqlalchemy.orm.attributes import InstrumentedAttribute
        
        # Check that the columns exist and are instrumented
        columns = ['name', 'description', 'channel_id', 'workspace_id', 'game_type', 'is_active']
        for column in columns:
            assert hasattr(Game, column)
            assert isinstance(getattr(Game, column), InstrumentedAttribute)
    
    def test_relationships(self):
        """Test that Game has the expected relationships."""
        from sqlalchemy.orm.attributes import InstrumentedAttribute
        
        # Check that the relationships exist and are instrumented
        relationships = ['members', 'scenes', 'polls', 'settings']
        for rel in relationships:
            assert hasattr(Game, rel)
            assert isinstance(getattr(Game, rel), InstrumentedAttribute)
    
    def test_init(self, game_data):
        """Test initialization of Game model."""
        # Execute
        game = Game(**game_data)
        
        # Verify all attributes are set correctly
        for key, value in game_data.items():
            assert getattr(game, key) == value
    
    def test_repr(self, game):
        """Test the __repr__ method."""
        repr_str = repr(game)
        
        # Verify that the string representation contains key identifiers
        assert game.id in repr_str
        assert game.name in repr_str
        assert str(game.game_type.value) in repr_str or str(game.game_type) in repr_str

    def test_get_by_id(self, mock_session, game):
        """Test the get_by_id class method."""
        # Setup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = game
        
        # Execute
        result = Game.get_by_id(game.id)
        
        # Verify
        assert result == game
        mock_session.query.assert_called_once_with(Game)
        query_mock.filter_by.assert_called_once_with(id=game.id)
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_get_by_id_not_found(self, mock_session):
        """Test the get_by_id class method when the game is not found."""
        # Setup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = None
        
        # Execute
        result = Game.get_by_id("nonexistent-id")
        
        # Verify
        assert result is None
        mock_session.query.assert_called_once_with(Game)
        query_mock.filter_by.assert_called_once_with(id="nonexistent-id")
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_get_by_channel(self, mock_session, game):
        """Test the get_by_channel class method."""
        # Setup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = game
        
        # Execute
        result = Game.get_by_channel(game.channel_id, game.workspace_id)
        
        # Verify
        assert result == game
        mock_session.query.assert_called_once_with(Game)
        query_mock.filter_by.assert_called_once_with(
            channel_id=game.channel_id,
            workspace_id=game.workspace_id
        )
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_get_by_channel_not_found(self, mock_session):
        """Test the get_by_channel class method when the game is not found."""
        # Setup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = None
        
        # Execute
        result = Game.get_by_channel("nonexistent-channel", "nonexistent-workspace")
        
        # Verify
        assert result is None
        mock_session.query.assert_called_once_with(Game)
        query_mock.filter_by.assert_called_once_with(
            channel_id="nonexistent-channel",
            workspace_id="nonexistent-workspace"
        )
        self.mock_close_session.assert_called_once_with(mock_session)
    
    @patch('sologm.rpg_helper.models.game.base.Game.get_by_channel')
    def test_create_for_channel(self, mock_get_by_channel, mock_session, game_data):
        """Test the create_for_channel class method."""
        # Setup
        mock_get_by_channel.return_value = None
        
        # Execute
        result = Game.create_for_channel(
            game_data["channel_id"], 
            game_data["workspace_id"],
            name=game_data["name"],
            description=game_data["description"],
            game_type=game_data["game_type"]
        )
        
        # Verify
        assert result.name == game_data["name"]
        assert result.description == game_data["description"]
        assert result.channel_id == game_data["channel_id"]
        assert result.workspace_id == game_data["workspace_id"]
        assert result.game_type == game_data["game_type"]
        
        mock_get_by_channel.assert_called_once_with(
            game_data["channel_id"], 
            game_data["workspace_id"]
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        self.mock_close_session.assert_called_once_with(mock_session)

    @patch('sologm.rpg_helper.models.game.base.Game.get_by_channel')
    def test_create_for_channel_already_exists(self, mock_get_by_channel, game):
        """Test the create_for_channel class method when a game already exists for the channel."""
        # Setup
        mock_get_by_channel.return_value = game
        
        # Execute & Verify
        with pytest.raises(ChannelGameExistsError) as excinfo:
            Game.create_for_channel(game.channel_id, game.workspace_id)
        
        assert excinfo.value.channel_id == game.channel_id
        expected_message = f"A game already exists in channel {game.channel_id}"
        assert str(excinfo.value) == expected_message
    
    def test_get_all_active(self, mock_session, game):
        """Test the get_all_active class method."""
        # Setup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.all.return_value = [game]
        
        # Execute
        result = Game.get_all_active()
        
        # Verify
        assert result == [game]
        mock_session.query.assert_called_once_with(Game)
        query_mock.filter_by.assert_called_once_with(is_active=True)
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_to_dict(self, game):
        """Test the to_dict method."""
        # Setup
        game.created_at = datetime(2023, 1, 1, 12, 0, 0)
        game.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        
        # Execute
        result = game.to_dict()
        
        # Verify
        assert result["id"] == game.id
        assert result["name"] == game.name
        assert result["description"] == game.description
        assert result["channel_id"] == game.channel_id
        assert result["workspace_id"] == game.workspace_id
        assert result["game_type"] == game.game_type.value
        assert result["is_active"] == game.is_active
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["updated_at"] == "2023-01-02T12:00:00"
    
    def test_add_member(self, game):
        """Test the add_member method."""
        # Setup
        user = MagicMock()
        user.id = "test-user-id"
        user.username = "test-user"
        game.members = []
        
        # Execute
        game.add_member(user)
        
        # Verify
        assert user in game.members
    
    def test_add_member_already_member(self, game):
        """Test the add_member method when the user is already a member."""
        # Setup
        user = MagicMock()
        user.id = "test-user-id"
        user.username = "test-user"
        game.members = [user]
        
        # Execute
        game.add_member(user)
        
        # Verify - should not add the user again
        assert game.members.count(user) == 1
    
    def test_remove_member(self, game):
        """Test the remove_member method."""
        # Setup
        user = MagicMock()
        user.id = "test-user-id"
        user.username = "test-user"
        game.members = []
        game.members.append(user)
        
        # Verify initial state
        assert len(game.members) == 1, "User should be in members list before removal"
        
        # Execute
        game.remove_member(user)
        
        # Verify
        assert len(game.members) == 0, "Members list should be empty after removal"
        assert user not in game.members, "User should not be in members list"
    
    def test_remove_member_not_member(self, game):
        """Test the remove_member method when the user is not a member."""
        # Setup
        user = MagicMock()
        user.id = "test-user-id"
        user.username = "test-user"
        game.members = []
        
        # Execute
        game.remove_member(user)
        
        # Verify - should not raise an exception
        assert user not in game.members
    
    def test_is_member(self, game):
        """Test the is_member method."""
        # Setup
        user_id = "test-user-id"
        user = MagicMock()
        user.id = user_id
        game.members = [user]
        
        # Execute & Verify
        assert game.is_member(user_id) is True
        assert game.is_member("nonexistent-user-id") is False
    
    def test_get_setting(self, mock_session, game):
        """Test the get_setting method."""
        # Setup
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        setting_name = "test-setting"
        setting_value = "test-value"
        
        mock_setting = MagicMock(spec=GameSetting)
        mock_setting.value = setting_value
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        # Ensure object_session returns None so we use get_session
        self.mock_object_session.return_value = None
        
        # Setup query chain
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = mock_setting
        
        # Execute
        result = game.get_setting(setting_name)
        
        # Verify
        assert result == setting_value
        mock_session.query.assert_called_once()
        query_mock.filter_by.assert_called_once_with(
            game_id=game.id, name=setting_name
        )
        # Verify session management
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_get_setting_not_found(self, mock_session, game):
        """Test the get_setting method when the setting is not found."""
        # Setup
        setting_name = "nonexistent-setting"
        default_value = "default-value"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        self.mock_object_session.return_value = None
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = None
        
        # Execute
        result = game.get_setting(setting_name, default_value)
        
        # Verify
        assert result == default_value
        mock_session.query.assert_called_once()
        query_mock.filter_by.assert_called_once_with(
            game_id=game.id, name=setting_name
        )
        self.mock_close_session.assert_called_once_with(mock_session)
    
    def test_get_setting_with_existing_session(self, mock_session, game):
        """Test the get_setting method with an existing session."""
        # Setup
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        setting_name = "test-setting"
        setting_value = "test-value"
        
        mock_setting = MagicMock(spec=GameSetting)
        mock_setting.value = setting_value
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        self.mock_object_session.return_value = mock_session
        mock_session.query.return_value = query_mock
        query_mock.filter_by.return_value = filter_mock
        filter_mock.first.return_value = mock_setting
        
        # Execute
        result = game.get_setting(setting_name)
        
        # Verify
        assert result == setting_value
        self.mock_object_session.assert_called_once_with(game)
        mock_session.query.assert_called_once()
        query_mock.filter_by.assert_called_once_with(
            game_id=game.id, name=setting_name
        )
    
    def test_deactivate(self, game):
        """Test the deactivate method."""
        # Setup
        game.is_active = True
        
        # Execute
        game.deactivate()
        
        # Verify
        assert game.is_active is False
    
    def test_deactivate_already_inactive(self, game):
        """Test the deactivate method when the game is already inactive."""
        # Setup
        game.is_active = False
        
        # Execute
        game.deactivate()
        
        # Verify - should not change the status
        assert game.is_active is False
    
    def test_activate(self, game):
        """Test the activate method."""
        # Setup
        game.is_active = False
        
        # Execute
        game.activate()
        
        # Verify
        assert game.is_active is True
    
    def test_activate_already_active(self, game):
        """Test the activate method when the game is already active."""
        # Setup
        game.is_active = True
        
        # Execute
        game.activate()
        
        # Verify - should not change the status
        assert game.is_active is True 