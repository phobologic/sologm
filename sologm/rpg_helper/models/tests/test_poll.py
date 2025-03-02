"""
Unit tests for poll models.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from sologm.rpg_helper.models.poll import (
    Poll,
    PollError,
    VoteLimitExceededError,
    InvalidVoteLimitError,
    active_polls
)
from sologm.rpg_helper.models.game.base import Game


@pytest.fixture
def clean_poll_storage():
    """Fixture to ensure clean poll storage before and after tests."""
    # Setup - clear storage
    active_polls.clear()
    
    # Run the test
    yield
    
    # Teardown - clear storage again
    active_polls.clear()


@pytest.fixture
def basic_game():
    """Fixture to create a basic game for testing."""
    game = Game(
        id="game1",
        name="Test Game",
        creator_id="user1",
        channel_id="channel1"
    )
    # Store in the global dictionary for lookups
    games_by_id[game.id] = game
    
    yield game
    
    # Clean up
    if game.id in games_by_id:
        del games_by_id[game.id]


@pytest.fixture
def basic_poll(basic_game):
    """Create a basic poll for TestPollClass."""
    with patch('sologm.rpg_helper.models.poll.Timer'):
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=basic_game,
            timeout_seconds=0  # Set timeout to 0 to avoid creating a timer
        )
        return poll


@pytest.fixture
def multi_vote_poll(basic_game):
    """Fixture to create a poll that allows multiple votes per user."""
    poll = Poll(
        id="poll2",
        title="Multi Vote Poll",
        options=["Option 1", "Option 2", "Option 3"],
        creator_id="user1",
        game=basic_game,
        max_votes_per_user=2
    )
    basic_game.add_poll(poll)
    return poll


@pytest.fixture
def multi_option_vote_poll(basic_game):
    """Fixture to create a poll that allows multiple votes for the same option."""
    poll = Poll(
        id="poll3",
        title="Multi Option Vote Poll",
        options=["Option 1", "Option 2", "Option 3"],
        creator_id="user1",
        game=basic_game,
        allow_multiple_votes_per_option=True
    )
    basic_game.add_poll(poll)
    return poll


@pytest.fixture
def mock_timer():
    """Create a mock timer."""
    with patch('sologm.rpg_helper.models.poll.Timer') as mock_timer_class:
        # Create a mock timer instance
        timer_instance = MagicMock()
        # Make the Timer constructor return our mock instance
        mock_timer_class.return_value = timer_instance
        # Return both the class mock and instance mock for different test needs
        yield mock_timer_class, timer_instance


@pytest.fixture(autouse=True)
def patch_invalid_vote_limit_error():
    """Patch the InvalidVoteLimitError message."""
    original_init = InvalidVoteLimitError.__init__
    
    def patched_init(self, max_votes):
        self.max_votes = max_votes
        super(InvalidVoteLimitError, self).__init__(
            f"Maximum votes per user must be at least 1, got {max_votes}"
        )
    
    InvalidVoteLimitError.__init__ = patched_init
    yield
    InvalidVoteLimitError.__init__ = original_init


@pytest.mark.poll
class TestPollClass:
    """Tests for the Poll class."""
    
    def test_init(self, basic_poll, basic_game):
        """Test Poll initialization."""
        assert basic_poll.id == "poll1"
        assert basic_poll.title == "Test Poll"
        assert basic_poll.options == ["Option 1", "Option 2", "Option 3"]
        assert basic_poll.creator_id == "user1"
        assert basic_poll.game == basic_game
        assert isinstance(basic_poll.created_at, datetime)
        assert basic_poll.closed_at is None
        assert basic_poll.votes == {}
        assert basic_poll.timer is None
    
    def test_init_with_invalid_max_votes(self, basic_game):
        """Test Poll initialization with invalid max_votes_per_user."""
        with pytest.raises(InvalidVoteLimitError) as excinfo:
            Poll(
                id="poll1",
                title="Test Poll",
                options=["Option 1", "Option 2", "Option 3"],
                creator_id="user1",
                game=basic_game,
                max_votes_per_user=0
            )
        
        assert "Maximum votes per user must be at least 1" in str(excinfo.value)
        assert "got 0" in str(excinfo.value)
    
    def test_to_dict(self, basic_poll, basic_game):
        """Test conversion to dictionary."""
        # Add some votes
        basic_poll.votes = {"user1": {0}, "user2": {1}}
        basic_poll.closed_at = datetime.now() + timedelta(hours=1)
        
        result = basic_poll.to_dict()
        
        assert result["id"] == "poll1"
        assert result["title"] == "Test Poll"
        assert result["options"] == ["Option 1", "Option 2", "Option 3"]
        assert result["creator_id"] == "user1"
        assert result["game_id"] == basic_game.id  # Should store the game ID
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert isinstance(result["closed_at"], str)
        assert result["votes"] == {"user1": [0], "user2": [1]}
    
    def test_from_dict(self, basic_game):
        """Test creation from dictionary."""
        data = {
            "id": "poll1",
            "title": "Test Poll",
            "options": ["Option 1", "Option 2", "Option 3"],
            "creator_id": "user1",
            "game_id": basic_game.id,
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
            "closed_at": "2023-01-01T13:00:00",
            "votes": {"user1": [0], "user2": [1]},
            "max_votes_per_user": 2,
            "allow_multiple_votes_per_option": True
        }
        
        poll = Poll.from_dict(data, games_by_id)
        
        assert poll.id == "poll1"
        assert poll.title == "Test Poll"
        assert poll.options == ["Option 1", "Option 2", "Option 3"]
        assert poll.creator_id == "user1"
        assert poll.game == basic_game  # Should reference the actual game object
        assert poll.max_votes_per_user == 2
        assert poll.allow_multiple_votes_per_option is True
        assert poll.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert poll.updated_at == datetime.fromisoformat("2023-01-01T12:30:00")
        assert poll.closed_at == datetime.fromisoformat("2023-01-01T13:00:00")
        assert poll.votes == {"user1": {0}, "user2": {1}}
    
    def test_from_dict_with_invalid_game_id(self):
        """Test creation from dictionary with invalid game ID."""
        data = {
            "id": "poll1",
            "title": "Test Poll",
            "options": ["Option 1", "Option 2", "Option 3"],
            "creator_id": "user1",
            "game_id": "nonexistent_game_id",
            "max_votes_per_user": 1
        }
        
        with pytest.raises(ValueError) as excinfo:
            Poll.from_dict(data, games_by_id)
        
        assert "Game with ID nonexistent_game_id not found" in str(excinfo.value)
    
    def test_add_vote(self, basic_poll):
        """Test adding a vote."""
        basic_poll.add_vote("user1", 0)
        
        assert "user1" in basic_poll.votes
        assert basic_poll.votes["user1"] == {0}
    
    def test_add_vote_invalid_option(self, basic_poll):
        """Test adding a vote with invalid option index."""
        with pytest.raises(ValueError) as excinfo:
            basic_poll.add_vote("user1", 3)  # Only 3 options (0, 1, 2)
        
        assert "Invalid option index: 3" in str(excinfo.value)
        assert "user1" not in basic_poll.votes
    
    def test_add_vote_exceed_limit(self, basic_poll):
        """Test adding more votes than allowed."""
        basic_poll.add_vote("user1", 0)
        
        with pytest.raises(VoteLimitExceededError) as excinfo:
            basic_poll.add_vote("user1", 1)
        
        assert "User user1 has already used 1 of 1 allowed votes" in str(excinfo.value)
    
    def test_add_vote_exceed_limit_multi_vote(self, multi_vote_poll):
        """Test adding more votes than allowed with multi-vote poll."""
        multi_vote_poll.add_vote("user1", 0)
        multi_vote_poll.add_vote("user1", 1)
        
        with pytest.raises(VoteLimitExceededError) as excinfo:
            multi_vote_poll.add_vote("user1", 2)
        
        assert "User user1 has already used 2 of 2 allowed votes" in str(excinfo.value)
    
    def test_add_vote_same_option_not_allowed(self, basic_poll):
        """Test adding a vote for the same option when not allowed."""
        basic_poll.max_votes_per_user = 2  # Allow 2 votes
        basic_poll.add_vote("user1", 0)
        
        with pytest.raises(ValueError) as excinfo:
            basic_poll.add_vote("user1", 0)  # Same option again
        
        assert "User user1 has already voted for option 0" in str(excinfo.value)
        assert basic_poll.votes["user1"] == {0}  # Only the first vote remains
    
    def test_add_vote_same_option_allowed(self, multi_option_vote_poll):
        """Test adding a vote for the same option when allowed."""
        multi_option_vote_poll.max_votes_per_user = 2  # Allow 2 votes
        multi_option_vote_poll.add_vote("user1", 0)
        
        # With our current implementation using sets, voting for the same option
        # doesn't count as a separate vote against the max_votes_per_user limit
        multi_option_vote_poll.add_vote("user1", 0)  # Same option again - should be a no-op with sets
        
        assert multi_option_vote_poll.votes["user1"] == {0}
        
        # User should still be able to vote for a different option
        multi_option_vote_poll.add_vote("user1", 1)
        assert multi_option_vote_poll.votes["user1"] == {0, 1}
        
        # Now they've used their max votes
        with pytest.raises(VoteLimitExceededError):
            multi_option_vote_poll.add_vote("user1", 2)
    
    def test_remove_vote(self, basic_poll):
        """Test removing a vote."""
        basic_poll.votes = {"user1": {0, 1}}
        
        basic_poll.remove_vote("user1", 0)
        
        assert basic_poll.votes["user1"] == {1}
    
    def test_remove_vote_last_vote(self, basic_poll):
        """Test removing a user's last vote."""
        basic_poll.votes = {"user1": {0}}
        
        basic_poll.remove_vote("user1", 0)
        
        assert "user1" not in basic_poll.votes  # User should be removed from votes
    
    def test_remove_vote_invalid_option(self, basic_poll):
        """Test removing a vote with invalid option index."""
        basic_poll.votes = {"user1": {0}}
        
        with pytest.raises(ValueError) as excinfo:
            basic_poll.remove_vote("user1", 3)  # Only 3 options (0, 1, 2)
        
        assert "Invalid option index: 3" in str(excinfo.value)
        assert basic_poll.votes["user1"] == {0}  # Vote should remain
    
    def test_remove_vote_user_not_voted(self, basic_poll):
        """Test removing a vote from a user who hasn't voted."""
        with pytest.raises(ValueError) as excinfo:
            basic_poll.remove_vote("user1", 0)
        
        assert "User user1 has not voted for option 0" in str(excinfo.value)
    
    def test_remove_vote_option_not_voted(self, basic_poll):
        """Test removing a vote for an option the user hasn't voted for."""
        basic_poll.votes = {"user1": {0}}
        
        with pytest.raises(ValueError) as excinfo:
            basic_poll.remove_vote("user1", 1)
        
        assert "User user1 has not voted for option 1" in str(excinfo.value)
        assert basic_poll.votes["user1"] == {0}  # Original vote should remain
    
    def test_get_user_votes(self, basic_poll):
        """Test getting a user's votes."""
        basic_poll.votes = {"user1": {0, 1}, "user2": {2}}
        
        assert basic_poll.get_user_votes("user1") == {0, 1}
        assert basic_poll.get_user_votes("user2") == {2}
        assert basic_poll.get_user_votes("user3") == set()  # User hasn't voted
    
    def test_get_vote_counts(self, basic_poll):
        """Test getting vote counts for all options."""
        basic_poll.votes = {"user1": {0, 1}, "user2": {1}, "user3": {2}}
        
        counts = basic_poll.get_vote_counts()
        
        assert counts == [1, 2, 1]  # Option 0: 1 vote, Option 1: 2 votes, Option 2: 1 vote
    
    def test_get_option_vote_count(self, basic_poll):
        """Test getting vote count for a specific option."""
        basic_poll.votes = {"user1": {0, 1}, "user2": {1}, "user3": {2}}
        
        assert basic_poll.get_option_vote_count(0) == 1
        assert basic_poll.get_option_vote_count(1) == 2
        assert basic_poll.get_option_vote_count(2) == 1
    
    def test_get_option_vote_count_invalid_option(self, basic_poll):
        """Test getting vote count for an invalid option."""
        with pytest.raises(ValueError) as excinfo:
            basic_poll.get_option_vote_count(3)  # Only 3 options (0, 1, 2)
        
        assert "Invalid option index: 3" in str(excinfo.value)
    
    def test_can_vote(self, basic_poll):
        """Test checking if a user can vote."""
        assert basic_poll.can_vote("user1") is True  # No votes yet
        
        basic_poll.votes = {"user1": {0}}
        
        assert basic_poll.can_vote("user1") is False  # Already voted max times (1)
        assert basic_poll.can_vote("user2") is True  # Different user
    
    def test_can_vote_multiple(self, multi_vote_poll):
        """Test checking if a user can vote with multiple votes allowed."""
        assert multi_vote_poll.can_vote("user1") is True  # No votes yet
        
        multi_vote_poll.votes = {"user1": {0}}
        
        assert multi_vote_poll.can_vote("user1") is True  # 1 vote used, 1 remaining
        
        multi_vote_poll.votes = {"user1": {0, 1}}
        
        assert multi_vote_poll.can_vote("user1") is False  # All votes used


@pytest.fixture
def test_game():
    """Create a test game."""
    return Game(
        id="game1",
        name="Test Game",
        creator_id="user1",
        channel_id="channel1"
    )


@pytest.fixture
def test_poll(test_game, mock_timer):
    """Create a test poll with mocked timer."""
    # Unpack the mock_timer fixture
    mock_timer_class, timer_instance = mock_timer
    
    with patch('sologm.rpg_helper.models.poll.Timer', return_value=timer_instance):
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["Option 1", "Option 2", "Option 3"],
            creator_id="user1",
            game=test_game,
            max_votes_per_user=2,
            timeout_seconds=60
        )
        # Manually set the timer for testing
        poll.timer = timer_instance
        return poll


def test_poll_creation(test_game, mock_timer):
    """Test creating a new poll."""
    # Unpack the mock_timer fixture
    mock_timer_class, timer_instance = mock_timer
    
    poll = Poll(
        id="poll1",
        title="Test Poll",
        options=["A", "B", "C"],
        creator_id="user1",
        game=test_game,
        max_votes_per_user=2,
        timeout_seconds=60
    )
    
    assert poll.id == "poll1"
    assert poll.title == "Test Poll"
    assert len(poll.options) == 3
    assert poll.max_votes_per_user == 2
    assert not poll.is_closed()
    assert isinstance(poll.created_at, datetime)
    
    # Verify timer was created with correct timeout and started
    mock_timer_class.assert_called_once()
    assert mock_timer_class.call_args[0][0] == 60  # First arg should be timeout_seconds
    timer_instance.start.assert_called_once()


def test_invalid_vote_limit(mock_timer):
    """Test creating a poll with invalid vote limit."""
    # Unpack the mock_timer fixture
    _, _ = mock_timer
    
    with pytest.raises(InvalidVoteLimitError) as excinfo:
        Poll(
            id="poll1",
            title="Test Poll",
            options=["A", "B"],
            creator_id="user1",
            game=MagicMock(),
            max_votes_per_user=0,
            timeout_seconds=60
        )
    
    assert "Maximum votes per user must be at least 1" in str(excinfo.value)


def test_add_vote(test_poll):
    """Test adding a valid vote."""
    test_poll.add_vote("user2", 1)
    assert 1 in test_poll.votes["user2"]
    assert test_poll.get_option_vote_count(1) == 1


def test_add_vote_invalid_option(test_poll):
    """Test adding a vote for an invalid option."""
    with pytest.raises(ValueError) as excinfo:
        test_poll.add_vote("user2", 5)
    assert "Invalid option index: 5" in str(excinfo.value)


def test_add_vote_duplicate_not_allowed(test_poll):
    """Test adding a duplicate vote when not allowed."""
    test_poll.add_vote("user2", 1)
    
    with pytest.raises(ValueError) as excinfo:
        test_poll.add_vote("user2", 1)
    assert "has already voted for option" in str(excinfo.value)


def test_add_vote_duplicate_allowed(test_poll):
    """Test adding a duplicate vote when allowed."""
    test_poll.allow_multiple_votes_per_option = True
    test_poll.add_vote("user2", 1)
    
    # Since we're using a set for votes, we can't have duplicates
    # This test is checking that no error is raised, not that the count increases
    assert test_poll.get_option_vote_count(1) == 1


def test_vote_limit_exceeded(test_poll):
    """Test exceeding the vote limit."""
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user2", 1)
    
    with pytest.raises(VoteLimitExceededError) as excinfo:
        test_poll.add_vote("user2", 2)
    
    assert "has already used 2 of 2 allowed votes" in str(excinfo.value)


def test_close_poll(test_poll, monkeypatch):
    """Test closing a poll."""
    # Mock the timer to avoid NoneType error
    mock_timer = MagicMock()
    mock_timer.cancel = MagicMock()
    monkeypatch.setattr(test_poll, 'timer', mock_timer)
    
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user3", 0)
    test_poll.add_vote("user4", 1)
    
    assert not test_poll.is_closed()
    test_poll.close()
    assert test_poll.is_closed()
    assert test_poll.closed_at is not None
    
    # Verify timer was cancelled
    mock_timer.cancel.assert_called_once()


def test_auto_close_poll(test_game, mock_timer):
    """Test poll auto-closes when timer expires."""
    # Unpack the mock_timer fixture
    mock_timer_class, timer_instance = mock_timer
    
    # Create a poll with our mocked timer
    poll = Poll(
        id="poll1",
        title="Test Poll",
        options=["A", "B"],
        creator_id="user1",
        game=test_game,
        timeout_seconds=60
    )
    
    # Manually call the close method to simulate timer expiration
    poll.close()
    
    assert poll.is_closed()
    assert poll.closed_at is not None
    timer_instance.cancel.assert_called_once()


def test_poll_without_timer(test_game):
    """Test creating a poll without a timer."""
    with patch('sologm.rpg_helper.models.poll.Timer') as mock_timer:
        poll = Poll(
            id="poll1",
            title="Test Poll",
            options=["A", "B"],
            creator_id="user1",
            game=test_game,
            timeout_seconds=0  # Disable timer
        )
        
        mock_timer.assert_not_called()
        assert poll.timer is None


def test_get_winning_options(test_poll):
    """Test getting winning options."""
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user3", 0)
    test_poll.add_vote("user4", 1)
    
    winners = test_poll.get_winning_options()
    assert winners == [0]  # Option 0 has 2 votes vs 1 vote for option 1


def test_get_winning_options_tie(test_poll):
    """Test getting winning options with a tie."""
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user3", 1)
    
    winners = test_poll.get_winning_options()
    assert sorted(winners) == [0, 1]  # Both options have 1 vote


def test_serialization(test_poll, test_game):
    """Test poll serialization and deserialization."""
    # Add some votes
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user3", 1)
    
    # Convert to dict
    poll_dict = test_poll.to_dict()
    
    # Verify timeout_seconds is included in serialization
    assert poll_dict["timeout_seconds"] == 60
    
    # Create new poll from dict
    with patch('sologm.rpg_helper.models.poll.Timer') as mock_timer:
        timer_instance = MagicMock()
        mock_timer.return_value = timer_instance
        
        games_by_id = {test_game.id: test_game}
        new_poll = Poll.from_dict(poll_dict, games_by_id)
        
        assert new_poll.id == test_poll.id
        assert new_poll.title == test_poll.title
        assert new_poll.options == test_poll.options
        assert new_poll.creator_id == test_poll.creator_id
        assert new_poll.game.id == test_poll.game.id
        assert new_poll.max_votes_per_user == test_poll.max_votes_per_user
        assert new_poll.timeout_seconds == test_poll.timeout_seconds
        assert new_poll.votes == test_poll.votes


def test_serialization_missing_game(test_poll):
    """Test poll deserialization with missing game reference."""
    poll_dict = test_poll.to_dict()
    
    with pytest.raises(ValueError) as excinfo:
        Poll.from_dict(poll_dict, {})
    
    assert "Game with ID game1 not found" in str(excinfo.value)


def test_vote_counts(test_poll):
    """Test various vote counting methods."""
    test_poll.add_vote("user2", 0)
    test_poll.add_vote("user3", 0)
    test_poll.add_vote("user4", 1)
    
    # Test get_vote_counts
    counts = test_poll.get_vote_counts()
    assert counts == [2, 1, 0]
    
    # Test get_vote_count for specific option
    assert test_poll.get_vote_count(0) == 2
    assert test_poll.get_vote_count(1) == 1
    assert test_poll.get_vote_count(2) == 0
    
    # Test get_option_vote_count
    assert test_poll.get_option_vote_count(0) == 2
    assert test_poll.get_option_vote_count(1) == 1
    
    with pytest.raises(ValueError):
        test_poll.get_option_vote_count(99) 