"""
Unit tests for poll models.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from sologm.rpg_helper.models.poll import (
    Poll,
    PollError,
    VoteLimitExceededError,
    InvalidVoteLimitError,
    active_polls
)


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
def basic_poll():
    """Fixture to create a basic poll for testing."""
    return Poll(
        id="poll1",
        channel_id="channel1",
        creator_id="user1",
        question="What should happen next?",
        options=["Option 1", "Option 2", "Option 3"]
    )


@pytest.fixture
def multi_vote_poll():
    """Fixture to create a poll that allows multiple votes per user."""
    return Poll(
        id="poll2",
        channel_id="channel1",
        creator_id="user1",
        question="What should happen next?",
        options=["Option 1", "Option 2", "Option 3"],
        max_votes_per_user=2
    )


@pytest.fixture
def multi_option_vote_poll():
    """Fixture to create a poll that allows multiple votes for the same option."""
    return Poll(
        id="poll3",
        channel_id="channel1",
        creator_id="user1",
        question="What should happen next?",
        options=["Option 1", "Option 2", "Option 3"],
        allow_multiple_votes_per_option=True
    )


@pytest.mark.poll
class TestPollClass:
    """Tests for the Poll class."""
    
    def test_init(self, basic_poll):
        """Test Poll initialization."""
        assert basic_poll.id == "poll1"
        assert basic_poll.channel_id == "channel1"
        assert basic_poll.creator_id == "user1"
        assert basic_poll.question == "What should happen next?"
        assert basic_poll.options == ["Option 1", "Option 2", "Option 3"]
        assert basic_poll.max_votes_per_user == 1
        assert basic_poll.allow_multiple_votes_per_option is False
        assert isinstance(basic_poll.created_at, datetime)
        assert basic_poll.expires_at is None
        assert basic_poll.message_ts is None
        assert basic_poll.votes == {}
        assert basic_poll.timer is None
    
    def test_init_with_invalid_max_votes(self):
        """Test Poll initialization with invalid max_votes_per_user."""
        with pytest.raises(InvalidVoteLimitError) as excinfo:
            Poll(
                id="poll1",
                channel_id="channel1",
                creator_id="user1",
                question="What should happen next?",
                options=["Option 1", "Option 2", "Option 3"],
                max_votes_per_user=0
            )
        
        assert "Maximum votes per user must be at least 1" in str(excinfo.value)
        assert "got 0" in str(excinfo.value)
    
    def test_to_dict(self, basic_poll):
        """Test conversion to dictionary."""
        # Add some votes
        basic_poll.votes = {"user1": {0}, "user2": {1}}
        basic_poll.expires_at = datetime.now() + timedelta(hours=1)
        basic_poll.message_ts = "12345.67890"
        
        result = basic_poll.to_dict()
        
        assert result["id"] == "poll1"
        assert result["channel_id"] == "channel1"
        assert result["creator_id"] == "user1"
        assert result["question"] == "What should happen next?"
        assert result["options"] == ["Option 1", "Option 2", "Option 3"]
        assert result["max_votes_per_user"] == 1
        assert result["allow_multiple_votes_per_option"] is False
        assert isinstance(result["created_at"], str)
        assert isinstance(result["expires_at"], str)
        assert result["message_ts"] == "12345.67890"
        assert result["votes"] == {"user1": [0], "user2": [1]}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "poll1",
            "channel_id": "channel1",
            "creator_id": "user1",
            "question": "What should happen next?",
            "options": ["Option 1", "Option 2", "Option 3"],
            "created_at": "2023-01-01T12:00:00",
            "expires_at": "2023-01-01T13:00:00",
            "message_ts": "12345.67890",
            "votes": {"user1": [0], "user2": [1]},
            "max_votes_per_user": 2,
            "allow_multiple_votes_per_option": True
        }
        
        poll = Poll.from_dict(data)
        
        assert poll.id == "poll1"
        assert poll.channel_id == "channel1"
        assert poll.creator_id == "user1"
        assert poll.question == "What should happen next?"
        assert poll.options == ["Option 1", "Option 2", "Option 3"]
        assert poll.max_votes_per_user == 2
        assert poll.allow_multiple_votes_per_option is True
        assert poll.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert poll.expires_at == datetime.fromisoformat("2023-01-01T13:00:00")
        assert poll.message_ts == "12345.67890"
        assert poll.votes == {"user1": {0}, "user2": {1}}
    
    def test_from_dict_with_invalid_max_votes(self):
        """Test creation from dictionary with invalid max_votes_per_user."""
        data = {
            "id": "poll1",
            "channel_id": "channel1",
            "creator_id": "user1",
            "question": "What should happen next?",
            "options": ["Option 1", "Option 2", "Option 3"],
            "max_votes_per_user": 0
        }
        
        with pytest.raises(InvalidVoteLimitError) as excinfo:
            Poll.from_dict(data)
        
        assert "Maximum votes per user must be at least 1" in str(excinfo.value)
        assert "got 0" in str(excinfo.value)
    
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
        
        assert "User user1 has already voted 1 times" in str(excinfo.value)
        assert "Maximum allowed votes is 1" in str(excinfo.value)
        assert basic_poll.votes["user1"] == {0}  # Only the first vote remains
    
    def test_add_vote_multiple_allowed(self, multi_vote_poll):
        """Test adding multiple votes when allowed."""
        multi_vote_poll.add_vote("user1", 0)
        multi_vote_poll.add_vote("user1", 1)
        
        assert multi_vote_poll.votes["user1"] == {0, 1}
        
        # Third vote should still fail
        with pytest.raises(VoteLimitExceededError):
            multi_vote_poll.add_vote("user1", 2)
    
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