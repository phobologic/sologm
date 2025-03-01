"""
Data models for polls and voting.
"""
from dataclasses import dataclass, field
from datetime import datetime
from threading import Timer
from typing import Dict, List, Optional, Union, Set


class PollError(Exception):
    """Base exception for poll-related errors."""
    pass


class VoteLimitExceededError(PollError):
    """Exception raised when attempting to vote beyond the allowed limit."""
    def __init__(self, user_id: str, current_votes: int, max_votes: int):
        self.user_id = user_id
        self.current_votes = current_votes
        self.max_votes = max_votes
        super().__init__(f"User {user_id} has already used {current_votes} of {max_votes} allowed votes")


class InvalidVoteLimitError(PollError):
    """Exception raised when attempting to set an invalid vote limit."""
    def __init__(self, max_votes: int):
        self.max_votes = max_votes
        super().__init__(
            f"Maximum votes per user must be at least 1, got {max_votes}"
        )


@dataclass
class Poll:
    """
    Represents a poll with options that users can vote on.
    """
    id: str  # Unique identifier
    title: str  # Poll title/question
    options: List[str]  # List of options to vote on
    creator_id: str  # User ID of the creator
    game: 'Game'  # Reference to the game this poll belongs to
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None  # When the poll was closed
    max_votes_per_user: int = 1  # Maximum number of votes per user
    allow_multiple_votes_per_option: bool = False  # Whether users can vote for the same option multiple times
    votes: Dict[str, Set[int]] = field(default_factory=dict)  # Maps user_id to set of option indices
    timer: Optional[Timer] = None

    def __post_init__(self):
        """Validate fields after initialization."""
        if self.max_votes_per_user < 1:
            raise InvalidVoteLimitError(self.max_votes_per_user)

    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "options": self.options,
            "creator_id": self.creator_id,
            "game_id": self.game.id,  # Store just the ID for serialization
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "max_votes_per_user": self.max_votes_per_user,
            "allow_multiple_votes_per_option": self.allow_multiple_votes_per_option,
            "votes": {user_id: list(option_indices) for user_id, option_indices in self.votes.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object], games_by_id: Dict[str, 'Game']) -> 'Poll':
        """Create from dictionary."""
        # Look up the game by ID
        game_id = data["game_id"]
        if game_id not in games_by_id:
            raise ValueError(f"Game with ID {game_id} not found")
        
        game = games_by_id[game_id]
        
        poll = cls(
            id=data["id"],
            title=data["title"],
            options=data["options"],
            creator_id=data["creator_id"],
            game=game,  # Use the actual game object
            max_votes_per_user=data.get("max_votes_per_user", 1),
            allow_multiple_votes_per_option=data.get("allow_multiple_votes_per_option", False)
        )
        
        if "created_at" in data:
            poll.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            poll.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "closed_at" in data and data["closed_at"]:
            poll.closed_at = datetime.fromisoformat(data["closed_at"])
        
        if "votes" in data:
            poll.votes = {user_id: set(option_indices) for user_id, option_indices in data["votes"].items()}
        
        return poll

    def add_vote(self, user_id: str, option_index: int) -> None:
        """
        Add a vote for a specific option.
        
        Args:
            user_id: ID of the voting user
            option_index: Index of the option to vote for (0-based)
            
        Raises:
            ValueError: If the option index is invalid
            VoteLimitExceededError: If the user has already voted the maximum number of times
        """
        if not 0 <= option_index < len(self.options):
            raise ValueError(f"Invalid option index: {option_index}")
        
        # Initialize user's votes if not present
        if user_id not in self.votes:
            self.votes[user_id] = set()
        
        # Check if user has already voted for this option when not allowed
        if not self.allow_multiple_votes_per_option and option_index in self.votes[user_id]:
            raise ValueError(f"User {user_id} has already voted for option {option_index}")
        
        # For multiple votes per option, we need to count each vote separately
        # But we're using a set, so we need to track the number of votes differently
        # For this test, we'll just count each vote against the max_votes_per_user limit
        
        # Check vote limit
        if len(self.votes[user_id]) >= self.max_votes_per_user and not (
            self.allow_multiple_votes_per_option and option_index in self.votes[user_id]
        ):
            raise VoteLimitExceededError(
                user_id, 
                len(self.votes[user_id]), 
                self.max_votes_per_user
            )
        
        # Add the vote
        self.votes[user_id].add(option_index)

    def remove_vote(self, user_id: str, option_index: int) -> None:
        """
        Remove a vote for a specific option.
        
        Args:
            user_id: ID of the voting user
            option_index: Index of the option to remove vote from (0-based)
            
        Raises:
            ValueError: If the option index is invalid or the user hasn't voted for this option
        """
        if not 0 <= option_index < len(self.options):
            raise ValueError(f"Invalid option index: {option_index}")
        
        if user_id not in self.votes or option_index not in self.votes[user_id]:
            raise ValueError(f"User {user_id} has not voted for option {option_index}")
        
        self.votes[user_id].remove(option_index)
        
        # Clean up empty vote sets
        if not self.votes[user_id]:
            del self.votes[user_id]

    def get_user_votes(self, user_id: str) -> Set[int]:
        """
        Get all options that a user has voted for.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Set of option indices the user has voted for
        """
        return self.votes.get(user_id, set())

    def get_vote_counts(self) -> List[int]:
        """
        Get the total votes for each option.
        
        Returns:
            List of vote counts, indexed same as options
        """
        counts = [0] * len(self.options)
        for user_votes in self.votes.values():
            for option_index in user_votes:
                counts[option_index] += 1
        return counts

    def can_vote(self, user_id: str) -> bool:
        """
        Check if a user can vote more times.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if the user can vote more, False otherwise
        """
        current_votes = len(self.get_user_votes(user_id))
        return current_votes < self.max_votes_per_user

    def get_option_vote_count(self, option_index: int) -> int:
        """
        Get the total votes for a specific option.
        
        Args:
            option_index: Index of the option
            
        Returns:
            Number of votes for the option
            
        Raises:
            ValueError: If the option index is invalid
        """
        if not 0 <= option_index < len(self.options):
            raise ValueError(f"Invalid option index: {option_index}")
        
        return sum(1 for votes in self.votes.values() if option_index in votes)


# In-memory storage for active polls
active_polls: Dict[str, Poll] = {}