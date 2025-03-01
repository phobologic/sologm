"""
Unit tests for game models.
"""
import pytest
from datetime import datetime
from unittest.mock import patch

from sologm.rpg_helper.models.game import (
    Game, 
    MythicGMEGame,
    GameError,
    ChannelGameExistsError,
    create_game,
    get_game_class,
    get_game_in_channel,
    get_active_game_for_user,
    delete_game,
    games_by_id,
    games_by_channel,
    GAME_TYPES
)


# Fixtures
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


@pytest.fixture
def basic_game():
    """Fixture to create a basic game for testing."""
    return Game(
        id="game1",
        name="Test Game",
        creator_id="user1",
        channel_id="channel1"
    )


@pytest.fixture
def mythic_game():
    """Fixture to create a Mythic GME game for testing."""
    return MythicGMEGame(
        id="game1",
        name="Test Game",
        creator_id="user1",
        channel_id="channel1",
        chaos_factor=5
    )


@pytest.mark.game
class TestGameClass:
    """Tests for the Game class."""
    
    def test_init(self, basic_game):
        """Test Game initialization."""
        assert basic_game.id == "game1"
        assert basic_game.name == "Test Game"
        assert basic_game.creator_id == "user1"
        assert basic_game.channel_id == "channel1"
        assert basic_game.setting_description is None
        assert isinstance(basic_game.created_at, datetime)
        assert isinstance(basic_game.updated_at, datetime)
        assert basic_game.members == set()
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            setting_description="Fantasy world"
        )
        game.members.add("user1")
        game.members.add("user2")
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert result["setting_description"] == "Fantasy world"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert set(result["members"]) == {"user1", "user2"}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "setting_description": "Fantasy world",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-02T12:00:00",
            "members": ["user1", "user2"]
        }
        
        game = Game.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.setting_description == "Fantasy world"
        assert game.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert game.updated_at == datetime.fromisoformat("2023-01-02T12:00:00")
        assert game.members == {"user1", "user2"}
    
    def test_add_member(self, basic_game):
        """Test adding a member to the game."""
        original_time = basic_game.updated_at
        
        # Add a member
        basic_game.add_member("user2")
        
        assert "user2" in basic_game.members
        assert basic_game.updated_at > original_time

    def test_add_member_already_exists(self, basic_game):
        """Test adding a member that's already in the game."""
        basic_game.members.add("user2")
        original_time = basic_game.updated_at
        
        with pytest.raises(ValueError) as excinfo:
            basic_game.add_member("user2")
        
        assert "User user2 is already a member of this game" in str(excinfo.value)
        assert basic_game.updated_at == original_time  # Time shouldn't change

    def test_remove_member_success(self, basic_game):
        """Test successfully removing a member from the game."""
        basic_game.members.add("user2")
        original_time = basic_game.updated_at
        
        result = basic_game.remove_member("user2")
        
        assert result is True
        assert "user2" not in basic_game.members
        assert basic_game.updated_at > original_time

    def test_remove_member_not_found(self, basic_game):
        """Test removing a non-existent member from the game."""
        original_time = basic_game.updated_at
        
        with pytest.raises(KeyError) as excinfo:
            basic_game.remove_member("user2")
        
        assert "user2" not in basic_game.members
        assert basic_game.updated_at == original_time  # Time shouldn't change
    
    @pytest.mark.parametrize("user_id,expected", [
        ("user2", True),
        ("user3", False)
    ])
    def test_is_member(self, basic_game, user_id, expected):
        """Test checking if a user is a member of the game."""
        basic_game.members.add("user2")
        
        assert basic_game.is_member(user_id) is expected
    
    @pytest.mark.parametrize("user_id,expected", [
        ("user1", True),
        ("user2", False)
    ])
    def test_is_creator(self, basic_game, user_id, expected):
        """Test checking if a user is the creator of the game."""
        assert basic_game.is_creator(user_id) is expected
    
    def test_update_setting(self, basic_game):
        """Test updating the game's setting description."""
        # Save the original updated_at time
        original_time = basic_game.updated_at
        
        # Update the setting
        basic_game.update_setting("New fantasy world")
        
        assert basic_game.setting_description == "New fantasy world"
        assert basic_game.updated_at > original_time


@pytest.mark.mythic
class TestMythicGMEGameClass:
    """Tests for the MythicGMEGame class."""
    
    def test_init(self, mythic_game):
        """Test MythicGMEGame initialization."""
        assert mythic_game.id == "game1"
        assert mythic_game.name == "Test Game"
        assert mythic_game.creator_id == "user1"
        assert mythic_game.channel_id == "channel1"
        assert mythic_game.chaos_factor == 5  # Default value
    
    def test_to_dict(self):
        """Test conversion to dictionary for MythicGMEGame."""
        game = MythicGMEGame(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            chaos_factor=7
        )
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert result["chaos_factor"] == 7
    
    def test_from_dict(self):
        """Test creation from dictionary for MythicGMEGame."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "chaos_factor": 7,
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-02T12:00:00",
            "members": ["user1", "user2"]
        }
        
        game = MythicGMEGame.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.chaos_factor == 7
        assert game.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert game.updated_at == datetime.fromisoformat("2023-01-02T12:00:00")
        assert game.members == {"user1", "user2"}
    
    def test_from_dict_default_chaos_factor(self):
        """Test creation from dictionary without chaos factor."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1"
        }
        
        game = MythicGMEGame.from_dict(data)
        assert game.chaos_factor == 5  # Default value
    
    def test_get_chaos_factor(self, mythic_game):
        """Test getting the current chaos factor."""
        mythic_game.chaos_factor = 7
        assert mythic_game.get_chaos_factor() == 7
    
    @pytest.mark.parametrize("factor,expected", [
        (1, 1),  # Minimum value
        (5, 5),  # Middle value
        (9, 9),  # Maximum value
    ])
    def test_update_chaos_factor_valid(self, mythic_game, factor, expected):
        """Test updating chaos factor with valid values."""
        original_time = mythic_game.updated_at
        
        result = mythic_game.update_chaos_factor(factor)
        
        assert result == expected
        assert mythic_game.chaos_factor == expected
        assert mythic_game.updated_at > original_time
    
    @pytest.mark.parametrize("invalid_factor", [
        0,    # Below minimum
        -1,   # Negative
        10,   # Above maximum
        100,  # Far above maximum
    ])
    def test_update_chaos_factor_invalid(self, mythic_game, invalid_factor):
        """Test updating chaos factor with invalid values."""
        original_factor = mythic_game.chaos_factor
        original_time = mythic_game.updated_at
        
        with pytest.raises(ValueError) as excinfo:
            mythic_game.update_chaos_factor(invalid_factor)
        
        assert "Chaos factor must be between 1 and 9" in str(excinfo.value)
        assert str(invalid_factor) in str(excinfo.value)
        assert mythic_game.chaos_factor == original_factor  # Unchanged
        assert mythic_game.updated_at == original_time  # Unchanged
    
    @pytest.mark.parametrize("initial,expected", [
        (5, 6),  # Normal increment
        (8, 9),  # Increment to maximum
        (9, None),  # Already at maximum
    ])
    def test_increment_chaos_factor(self, mythic_game, initial, expected):
        """Test incrementing chaos factor."""
        mythic_game.chaos_factor = initial
        original_time = mythic_game.updated_at
        
        result = mythic_game.increment_chaos_factor()
        
        if expected is None:
            assert result is None
            assert mythic_game.chaos_factor == initial
            assert mythic_game.updated_at == original_time
        else:
            assert result == expected
            assert mythic_game.chaos_factor == expected
            assert mythic_game.updated_at > original_time
    
    @pytest.mark.parametrize("initial,expected", [
        (5, 4),  # Normal decrement
        (2, 1),  # Decrement to minimum
        (1, None),  # Already at minimum
    ])
    def test_decrement_chaos_factor(self, mythic_game, initial, expected):
        """Test decrementing chaos factor."""
        mythic_game.chaos_factor = initial
        original_time = mythic_game.updated_at
        
        result = mythic_game.decrement_chaos_factor()
        
        if expected is None:
            assert result is None
            assert mythic_game.chaos_factor == initial
            assert mythic_game.updated_at == original_time
        else:
            assert result == expected
            assert mythic_game.chaos_factor == expected
            assert mythic_game.updated_at > original_time
    
    @pytest.mark.parametrize("initial,operations,expected", [
        (5, ["inc", "inc"], 7),
        (5, ["dec", "dec"], 3),
        (8, ["inc", "inc"], 9),  # Should stop at max
        (2, ["dec", "dec"], 1),  # Should stop at min
        (5, ["inc", "dec"], 5),  # Should end up where it started
    ])
    def test_chaos_factor_operations_sequence(self, mythic_game, initial, operations, expected):
        """Test sequences of chaos factor operations."""
        mythic_game.chaos_factor = initial
        
        for op in operations:
            if op == "inc":
                mythic_game.increment_chaos_factor()
            else:  # op == "dec"
                mythic_game.decrement_chaos_factor()
        
        assert mythic_game.chaos_factor == expected


@pytest.mark.functions
class TestGameFunctions:
    """Tests for game-related functions."""
    
    @pytest.mark.parametrize("game_type,expected_class", [
        (None, Game),
        ("standard", Game),
        ("mythic", MythicGMEGame)
    ])
    def test_get_game_class(self, game_type, expected_class):
        """Test getting game classes by type."""
        game_class = get_game_class(game_type)
        assert game_class == expected_class
    
    def test_get_game_class_invalid(self):
        """Test getting an invalid game class."""
        with pytest.raises(ValueError) as excinfo:
            get_game_class("invalid_type")
        assert "Invalid game type" in str(excinfo.value)
    
    @pytest.mark.usefixtures("clean_game_storage")
    @patch('uuid.uuid4', return_value='mock-uuid')
    def test_create_game_standard(self, mock_uuid):
        """Test creating a standard game."""
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        assert game.id == "mock-uuid"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert isinstance(game, Game)
        assert not isinstance(game, MythicGMEGame)
        assert "user1" in game.members
        
        # Check that the game was stored correctly
        assert games_by_id["mock-uuid"] == game
        assert games_by_channel["channel1"] == game
    
    @pytest.mark.usefixtures("clean_game_storage")
    @patch('uuid.uuid4', return_value='mock-uuid')
    def test_create_game_mythic(self, mock_uuid):
        """Test creating a Mythic GME game."""
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            game_type="mythic",
            chaos_factor=7
        )
        
        assert game.id == "mock-uuid"
        assert game.name == "Test Game"
        assert isinstance(game, MythicGMEGame)
        assert game.chaos_factor == 7
        
        # Check that the game was stored correctly
        assert games_by_id["mock-uuid"] == game
        assert games_by_channel["channel1"] == game
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_create_game_channel_exists(self):
        """Test creating a game in a channel that already has one."""
        # Create a game first
        game1 = create_game(
            name="Test Game 1",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Try to create another game in the same channel
        with pytest.raises(ChannelGameExistsError) as excinfo:
            create_game(
                name="Test Game 2",
                creator_id="user2",
                channel_id="channel1"
            )
        
        assert game1.name in str(excinfo.value)
        assert game1.id in str(excinfo.value)
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_game_in_channel(self):
        """Test getting a game in a channel."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the game
        result = get_game_in_channel("channel1")
        assert result == game
        
        # Try to get a game from a channel that doesn't have one
        result = get_game_in_channel("channel2")
        assert result is None
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_active_game_for_user_member(self):
        """Test getting the active game for a user who is a member."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        game.add_member("user2")
        
        # Get the active game for a member
        result = get_active_game_for_user("user2", "channel1")
        assert result == game
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_active_game_for_user_not_member(self):
        """Test getting the active game for a user who is not a member."""
        # Create a game
        create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the active game for a non-member
        result = get_active_game_for_user("user2", "channel1")
        assert result is None
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_get_active_game_for_user_no_game(self):
        """Test getting the active game for a user in a channel with no game."""
        result = get_active_game_for_user("user1", "channel1")
        assert result is None
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_delete_game_success(self):
        """Test successfully deleting a game."""
        # Create a game
        game = create_game(
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Delete the game
        result = delete_game(game.id)
        
        assert result is True
        assert game.id not in games_by_id
        assert "channel1" not in games_by_channel
    
    @pytest.mark.usefixtures("clean_game_storage")
    def test_delete_game_not_found(self):
        """Test deleting a non-existent game."""
        result = delete_game("nonexistent-id")
        assert result is False 

@pytest.mark.game
class TestGameSettings:
    """Tests for the Game settings functionality."""
    
    def test_default_settings(self, basic_game):
        """Test that a new game has empty settings by default."""
        assert basic_game.settings == {}
    
    def test_set_setting(self, basic_game):
        """Test setting a game setting."""
        original_time = basic_game.updated_at
        
        basic_game.set_setting("test_key", "test_value")
        
        assert basic_game.settings["test_key"] == "test_value"
        assert basic_game.updated_at > original_time
    
    def test_set_setting_overwrite(self, basic_game):
        """Test overwriting an existing setting."""
        basic_game.settings["test_key"] = "old_value"
        original_time = basic_game.updated_at
        
        basic_game.set_setting("test_key", "new_value")
        
        assert basic_game.settings["test_key"] == "new_value"
        assert basic_game.updated_at > original_time
    
    def test_get_setting_exists(self, basic_game):
        """Test getting an existing setting."""
        basic_game.settings["test_key"] = "test_value"
        
        result = basic_game.get_setting("test_key")
        
        assert result == "test_value"
    
    def test_get_setting_not_exists(self, basic_game):
        """Test getting a non-existent setting."""
        result = basic_game.get_setting("nonexistent_key")
        
        assert result is None
    
    def test_get_setting_with_default(self, basic_game):
        """Test getting a non-existent setting with a default value."""
        result = basic_game.get_setting("nonexistent_key", "default_value")
        
        assert result == "default_value"
    
    def test_delete_setting_exists(self, basic_game):
        """Test deleting an existing setting."""
        basic_game.settings["test_key"] = "test_value"
        original_time = basic_game.updated_at
        
        result = basic_game.delete_setting("test_key")
        
        assert result is True
        assert "test_key" not in basic_game.settings
        assert basic_game.updated_at > original_time
    
    def test_delete_setting_not_exists(self, basic_game):
        """Test deleting a non-existent setting."""
        original_time = basic_game.updated_at
        
        result = basic_game.delete_setting("nonexistent_key")
        
        assert result is False
        assert basic_game.updated_at == original_time
    
    def test_settings_in_to_dict(self, basic_game):
        """Test that settings are included in to_dict output."""
        basic_game.settings = {"key1": "value1", "key2": 42}
        
        result = basic_game.to_dict()
        
        assert "settings" in result
        assert result["settings"] == {"key1": "value1", "key2": 42}
    
    def test_settings_from_dict(self):
        """Test that settings are loaded from dict."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "settings": {"key1": "value1", "key2": 42}
        }
        
        game = Game.from_dict(data)
        
        assert game.settings == {"key1": "value1", "key2": 42}
    
    def test_complex_settings(self, basic_game):
        """Test storing complex nested settings."""
        complex_setting = {
            "nested": {
                "deeper": [1, 2, 3],
                "value": True
            },
            "list": ["a", "b", "c"]
        }
        
        basic_game.set_setting("complex", complex_setting)
        
        # Test direct access
        assert basic_game.settings["complex"] == complex_setting
        
        # Test via get_setting
        retrieved = basic_game.get_setting("complex")
        assert retrieved == complex_setting
        assert retrieved["nested"]["deeper"] == [1, 2, 3]
        
        # Test serialization roundtrip
        game_dict = basic_game.to_dict()
        new_game = Game.from_dict(game_dict)
        assert new_game.settings["complex"] == complex_setting 