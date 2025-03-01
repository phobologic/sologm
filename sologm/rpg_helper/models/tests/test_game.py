"""
Unit tests for game models.
"""
import pytest
from datetime import datetime
from unittest.mock import patch

from sologm.rpg_helper.models.game import (
    Game, 
    GameSettings,
    MythicGMEGame,
    GameError,
    SettingValidationError,
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
        assert basic_game.setting_info is None
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
            setting_info="Fantasy world"
        )
        game.members.add("user1")
        game.members.add("user2")
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert result["setting_info"] == "Fantasy world"
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
            "setting_info": "Fantasy world",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-02T12:00:00",
            "members": ["user1", "user2"]
        }
        
        game = Game.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.setting_info == "Fantasy world"
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
    
    def test_update_setting_info(self, basic_game):
        """Test updating the game's setting description."""
        # Save the original updated_at time
        original_time = basic_game.updated_at
        
        # Update the setting
        basic_game.update_setting_info("New fantasy world")
        
        assert basic_game.setting_info == "New fantasy world"
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
        """Test that a new game has default settings."""
        # Check that default settings are initialized
        assert hasattr(basic_game.settings, "poll_default_timeout_minutes")
        assert hasattr(basic_game.settings, "poll_default_options_count")
        assert hasattr(basic_game.settings, "poll_default_max_votes")
        assert hasattr(basic_game.settings, "poll_allow_multiple_votes_per_option")
        
        # Check default values
        assert basic_game.settings.poll_default_timeout_minutes == 240
        assert basic_game.settings.poll_default_options_count == 5
        assert basic_game.settings.poll_default_max_votes == 1
        assert basic_game.settings.poll_allow_multiple_votes_per_option is False
    
    def test_set_setting_valid(self, basic_game):
        """Test setting a valid game setting."""
        original_time = basic_game.updated_at
        
        basic_game.set_setting("poll_default_timeout_minutes", 120)
        
        assert basic_game.settings.poll_default_timeout_minutes == 120
        assert basic_game.updated_at > original_time
    
    def test_set_setting_invalid_name(self, basic_game):
        """Test setting a non-existent setting."""
        with pytest.raises(AttributeError) as excinfo:
            basic_game.set_setting("nonexistent_setting", "value")
        
        assert "'GameSettings' has no attribute 'nonexistent_setting'" in str(excinfo.value)
    
    def test_set_setting_invalid_value(self, basic_game):
        """Test setting a setting with an invalid value."""
        with pytest.raises(SettingValidationError) as excinfo:
            basic_game.set_setting("poll_default_timeout_minutes", -10)
        
        assert "Invalid value for setting 'poll_default_timeout_minutes'" in str(excinfo.value)
        assert "must be positive" in str(excinfo.value)
        # Original value should be unchanged
        assert basic_game.settings.poll_default_timeout_minutes == 240
    
    def test_get_setting_exists(self, basic_game):
        """Test getting an existing setting."""
        basic_game.settings.poll_default_timeout_minutes = 120
        
        result = basic_game.get_setting("poll_default_timeout_minutes")
        
        assert result == 120
    
    def test_get_setting_not_exists(self, basic_game):
        """Test getting a non-existent setting."""
        result = basic_game.get_setting("nonexistent_key")
        
        assert result is None
    
    def test_get_setting_with_default(self, basic_game):
        """Test getting a non-existent setting with a default value."""
        result = basic_game.get_setting("nonexistent_key", "default_value")
        
        assert result == "default_value"
    
    def test_delete_setting_not_allowed(self, basic_game):
        """Test that deleting settings is not allowed."""
        with pytest.raises(AttributeError) as excinfo:
            basic_game.delete_setting("poll_default_timeout_minutes")
        
        # Setting should still exist
        assert hasattr(basic_game.settings, "poll_default_timeout_minutes")
    
    def test_settings_in_to_dict(self, basic_game):
        """Test that settings are included in to_dict output."""
        basic_game.settings.poll_default_timeout_minutes = 120
        basic_game.settings.poll_default_options_count = 7
        
        result = basic_game.to_dict()
        
        assert "settings" in result
        assert result["settings"]["poll_default_timeout_minutes"] == 120
        assert result["settings"]["poll_default_options_count"] == 7
    
    def test_settings_from_dict(self):
        """Test that settings are loaded from dict."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "settings": {
                "poll_default_timeout_minutes": 120,
                "poll_default_options_count": 7,
                "unknown_setting": "value"  # This should be ignored
            }
        }
        
        game = Game.from_dict(data)
        
        # Custom settings should be loaded
        assert game.settings.poll_default_timeout_minutes == 120
        assert game.settings.poll_default_options_count == 7
        
        # Unknown settings should be ignored
        with pytest.raises(AttributeError):
            game.settings.unknown_setting
    
    def test_validation_on_init(self):
        """Test that validation happens during initialization."""
        with pytest.raises(SettingValidationError) as excinfo:
            GameSettings(poll_default_timeout_minutes=-10)
        
        assert "Invalid value for setting 'poll_default_timeout_minutes'" in str(excinfo.value)
        assert "must be positive" in str(excinfo.value)
    
    def test_validation_all_settings(self):
        """Test validation for all settings."""
        # Test poll_default_timeout_minutes
        with pytest.raises(SettingValidationError):
            GameSettings(poll_default_timeout_minutes=0)
        
        # Test poll_default_options_count
        with pytest.raises(SettingValidationError):
            GameSettings(poll_default_options_count=1)
        
        # Test poll_default_max_votes
        with pytest.raises(SettingValidationError):
            GameSettings(poll_default_max_votes=0)
        
        # Test poll_allow_multiple_votes_per_option (should accept any boolean-convertible value)
        settings = GameSettings(poll_allow_multiple_votes_per_option=True)
        assert settings.poll_allow_multiple_votes_per_option is True

@pytest.mark.game
class TestGamePollSettings:
    """Tests for the Game poll settings functionality."""
    
    def test_default_poll_settings(self, basic_game):
        """Test that a new game has default poll settings."""
        assert basic_game.get_poll_default_timeout() == 240
        assert basic_game.get_poll_default_options_count() == 5
        assert basic_game.get_poll_default_max_votes() == 1
        assert basic_game.get_poll_allow_multiple_votes_per_option() is False
    
    def test_set_poll_default_timeout(self, basic_game):
        """Test setting the default poll timeout."""
        basic_game.set_poll_default_timeout(10)
        
        assert basic_game.get_poll_default_timeout() == 10
        assert basic_game.settings.poll_default_timeout_minutes == 10
    
    def test_set_poll_default_timeout_invalid(self, basic_game):
        """Test setting an invalid default poll timeout."""
        with pytest.raises(ValueError) as excinfo:
            basic_game.set_poll_default_timeout(0)
        
        assert "Poll timeout must be positive" in str(excinfo.value)
        assert basic_game.get_poll_default_timeout() == 240  # Unchanged
    
    def test_set_poll_default_options_count(self, basic_game):
        """Test setting the default poll options count."""
        basic_game.set_poll_default_options_count(7)
        
        assert basic_game.get_poll_default_options_count() == 7
        assert basic_game.settings.poll_default_options_count == 7
    
    def test_set_poll_default_options_count_invalid(self, basic_game):
        """Test setting an invalid default poll options count."""
        with pytest.raises(ValueError) as excinfo:
            basic_game.set_poll_default_options_count(1)
        
        assert "Poll options count must be at least 2" in str(excinfo.value)
        assert basic_game.get_poll_default_options_count() == 5  # Unchanged
    
    def test_set_poll_default_max_votes(self, basic_game):
        """Test setting the default poll max votes."""
        basic_game.set_poll_default_max_votes(3)
        
        assert basic_game.get_poll_default_max_votes() == 3
        assert basic_game.settings.poll_default_max_votes == 3
    
    def test_set_poll_default_max_votes_invalid(self, basic_game):
        """Test setting an invalid default poll max votes."""
        with pytest.raises(ValueError) as excinfo:
            basic_game.set_poll_default_max_votes(0)
        
        assert "Poll max votes must be at least 1" in str(excinfo.value)
        assert basic_game.get_poll_default_max_votes() == 1  # Unchanged
    
    def test_set_poll_allow_multiple_votes_per_option(self, basic_game):
        """Test setting whether polls allow multiple votes per option."""
        basic_game.set_poll_allow_multiple_votes_per_option(True)
        
        assert basic_game.get_poll_allow_multiple_votes_per_option() is True
        assert basic_game.settings.poll_allow_multiple_votes_per_option is True
        
        # Test converting non-boolean to boolean
        basic_game.set_poll_allow_multiple_votes_per_option(0)
        assert basic_game.get_poll_allow_multiple_votes_per_option() is False 

@pytest.mark.game
class TestGamePolls:
    """Tests for the Game polls functionality."""
    
    def test_add_poll(self, basic_game):
        """Test adding a poll to a game."""
        from sologm.rpg_helper.models.poll import Poll
        
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        # The poll should already reference the game
        assert poll.game == basic_game
        
        # Add the poll to the game
        basic_game.add_poll(poll)
        
        # Check that the poll was added
        assert poll in basic_game.polls
        assert len(basic_game.polls) == 1
    
    def test_add_poll_already_exists(self, basic_game):
        """Test adding a poll that's already in the game."""
        from sologm.rpg_helper.models.poll import Poll
        
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        # Add the poll to the game
        basic_game.add_poll(poll)
        
        # Try to add it again
        with pytest.raises(ValueError) as excinfo:
            basic_game.add_poll(poll)
        
        assert f"Poll {poll.id} is already associated with this game" in str(excinfo.value)
    
    def test_remove_poll(self, basic_game):
        """Test removing a poll from a game."""
        from sologm.rpg_helper.models.poll import Poll
        
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        # Add the poll to the game
        basic_game.add_poll(poll)
        
        # Remove the poll
        result = basic_game.remove_poll(poll)
        
        # Check that the poll was removed
        assert result is True
        assert poll not in basic_game.polls
        assert len(basic_game.polls) == 0
    
    def test_remove_poll_not_exists(self, basic_game):
        """Test removing a poll that's not in the game."""
        from sologm.rpg_helper.models.poll import Poll
        
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        # Try to remove a poll that's not in the game
        result = basic_game.remove_poll(poll)
        
        # Check that the result is False
        assert result is False
    
    def test_get_polls(self, basic_game):
        """Test getting all polls for a game."""
        from sologm.rpg_helper.models.poll import Poll
        
        # Create some polls
        poll1 = Poll(
            id="poll1",
            title="Test Poll 1",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        poll2 = Poll(
            id="poll2",
            title="Test Poll 2",
            options=["Option A", "Option B", "Option C"],
            creator_id="user1",
            game=basic_game
        )
        
        # Add the polls to the game
        basic_game.add_poll(poll1)
        basic_game.add_poll(poll2)
        
        # Get all polls
        polls = basic_game.get_polls()
        
        # Check that both polls are returned
        assert len(polls) == 2
        assert poll1 in polls
        assert poll2 in polls
    
    def test_to_dict_with_polls(self, basic_game):
        """Test that polls are included in to_dict output."""
        from sologm.rpg_helper.models.poll import Poll
        
        # Create some polls
        poll1 = Poll(
            id="poll1",
            title="Test Poll 1",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game
        )
        
        poll2 = Poll(
            id="poll2",
            title="Test Poll 2",
            options=["Option A", "Option B", "Option C"],
            creator_id="user1",
            game=basic_game
        )
        
        # Add the polls to the game
        basic_game.add_poll(poll1)
        basic_game.add_poll(poll2)
        
        # Convert to dictionary
        result = basic_game.to_dict()
        
        # Check that poll IDs are included
        assert "poll_ids" in result
        assert set(result["poll_ids"]) == {"poll1", "poll2"}
    
    def test_from_dict_with_polls(self, clean_game_storage):
        """Test that poll IDs are loaded from dict but not resolved to objects."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "poll_ids": ["poll1", "poll2"]
        }
        
        game = Game.from_dict(data)
        
        # The poll_ids should be loaded as a list of strings
        # They will be resolved to Poll objects later when needed
        assert game.polls == ["poll1", "poll2"] 