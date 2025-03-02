"""
Tests for game-related functions.
"""
import pytest
from unittest.mock import patch

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.mythic import MythicGMEGame
from sologm.rpg_helper.models.game.errors import ChannelGameExistsError
from sologm.rpg_helper.models.game.functions import (
    create_game,
    get_game_in_channel,
    get_active_game_for_user,
    delete_game
)
from sologm.rpg_helper.models.game.storage import games_by_id, games_by_channel

@pytest.fixture
def clean_game_storage():
    """Fixture to ensure clean game storage before and after tests."""
    # Setup - clear storage
    games_by_id.clear()
    games_by_channel.clear()
    
    # Run the test
    yield
    
    # Teardown - clear storage again
    games_by_id.clear()
    games_by_channel.clear()


class TestGameFunctions:
    """Tests for game-related functions."""
    
    @pytest.mark.usefixtures("clean_game_storage")
    @patch('uuid.uuid4', return_value='mock-uuid')
    def test_create_game_standard(self, mock_uuid):
        """Test creating a standard game."""
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        assert isinstance(game, Game)
        assert not isinstance(game, MythicGMEGame)
        assert game.id == "mock-uuid"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.members == {"user1"}  # Creator is a member
        
        # Check that it was stored correctly
        assert game.id in games_by_id
        assert games_by_id[game.id] is game
        assert games_by_channel["channel1"] is game
    
    @pytest.mark.usefixtures("clean_game_storage")
    @patch('uuid.uuid4', return_value='mock-uuid')
    def test_create_game_mythic(self, mock_uuid):
        """Test creating a Mythic GME game."""
        game = create_game(
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="mythic"
        )
        
        assert isinstance(game, MythicGMEGame)
        assert game.id == "mock-uuid"
        assert game.name == "Test Mythic Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.members == {"user1"}  # Creator is a member
        assert game.chaos_factor == 5  # Default chaos factor
        
        # Check that it was stored correctly
        assert game.id in games_by_id
        assert games_by_id[game.id] is game
        assert games_by_channel["channel1"] is game
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_create_game_invalid_type(self):
        """Test creating a game with an invalid type."""
        with pytest.raises(ValueError) as excinfo:
            create_game(
                name="Test Game",
                creator_id="user1",
                channel_id="channel1",
                game_type="invalid"
            )
        
        assert "Invalid game type" in str(excinfo.value)
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_create_game_channel_exists(self):
        """Test creating a game in a channel that already has one."""
        # Create a game first
        game1 = create_game(
            name="Test Game 1",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        # Try to create another game in the same channel
        with pytest.raises(ChannelGameExistsError) as excinfo:
            create_game(
                name="Test Game 2",
                creator_id="user2",
                channel_id="channel1",
                game_type="standard"
            )
        
        assert "A game already exists in channel" in str(excinfo.value)
        assert excinfo.value.existing_game is game1
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_game_in_channel(self):
        """Test getting a game in a channel."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        # Get the game
        result = get_game_in_channel("channel1")
        assert result is game
        
        # Try to get a game in a channel that doesn't have one
        result = get_game_in_channel("channel2")
        assert result is None
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_active_game_for_user_member(self):
        """Test getting an active game for a user who is a member."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        # Add another member
        game.add_member("user2")
        
        # Get the game for the creator
        result = get_active_game_for_user("user1", "channel1")
        assert result is game
        
        # Get the game for the other member
        result = get_active_game_for_user("user2", "channel1")
        assert result is game
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_active_game_for_user_not_member(self):
        """Test getting an active game for a user who is not a member."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        # Try to get the game for a non-member
        result = get_active_game_for_user("user3", "channel1")
        assert result is None
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_delete_game_success(self):
        """Test successfully deleting a game."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="standard"
        )
        
        # Delete the game
        result = delete_game(game.id)
        assert result is True
        
        # Check that it was removed from storage
        assert game.id not in games_by_id
        assert "channel1" not in games_by_channel
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_delete_game_not_found(self):
        """Test deleting a game that doesn't exist."""
        result = delete_game("nonexistent")
        assert result is False 