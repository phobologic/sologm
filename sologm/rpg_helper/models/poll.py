"""
Data models for polls and voting.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from threading import Timer
from typing import Dict, List, Optional, Union, Set, Any, TYPE_CHECKING
import uuid

from sologm.rpg_helper.utils.logging import get_logger

# Only import Game when type checking
if TYPE_CHECKING:
    from sologm.rpg_helper.models.game.base import Game

logger = get_logger()


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
        super().__init__(f"Invalid max votes per user: {max_votes}")


@dataclass
class Poll:
    """
    Represents a poll with options that users can vote on.
    """
    title: str  # Poll title/question
    options: List[str]  # List of options to vote on
    creator_id: str  # User ID of the creator
    game: 'Game'  # Reference to the game this poll belongs to
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier with default
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None  # When the poll was closed
    max_votes_per_user: int = 1  # Maximum number of votes per user
    allow_multiple_votes_per_option: bool = False  # Whether users can vote for the same option multiple times
    votes: Dict[str, Set[int]] = field(default_factory=dict)  # Maps user_id to set of option indices
    timeout_seconds: int = 60  # Time in seconds until the poll auto-closes
    timer: Optional[Timer] = None  # Timer for auto-closing

    def __post_init__(self):
        """Validate fields after initialization."""
        if self.max_votes_per_user < 1:
            logger.error(
                "Invalid max votes per user",
                poll_id=self.id,
                max_votes=self.max_votes_per_user
            )
            raise InvalidVoteLimitError(self.max_votes_per_user)
        
        logger.debug(
            "Created new poll",
            poll_id=self.id,
            game_id=self.game.id,
            question=self.title,
            option_count=len(self.options),
            timeout=self.timeout_seconds
        )
        
        # Set up auto-close timer if timeout is specified
        if self.timeout_seconds > 0:
            self.timer = Timer(self.timeout_seconds, self.close)
            self.timer.start()
            logger.debug(
                "Started poll timer",
                poll_id=self.id,
                timeout=self.timeout_seconds
            )

    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        logger.debug("Converting poll to dict", poll_id=self.id)
        
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
            "timeout_seconds": self.timeout_seconds,
            "votes": {user_id: list(option_indices) for user_id, option_indices in self.votes.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object], games_by_id: Dict[str, 'Game']) -> 'Poll':
        """Create from dictionary."""
        logger.debug("Creating poll from dict", poll_id=data["id"])
        
        # Look up the game by ID
        game_id = data["game_id"]
        if game_id not in games_by_id:
            logger.error(
                "Game not found for poll",
                game_id=game_id,
                poll_id=data["id"]
            )
            raise ValueError(f"Game with ID {game_id} not found")
        
        game = games_by_id[game_id]
        
        poll = cls(
            id=data["id"],
            title=data["title"],
            options=data["options"],
            creator_id=data["creator_id"],
            game=game,  # Use the actual game object
            max_votes_per_user=data.get("max_votes_per_user", 1),
            allow_multiple_votes_per_option=data.get("allow_multiple_votes_per_option", False),
            timeout_seconds=data.get("timeout_seconds", 60)
        )
        
        if "created_at" in data:
            poll.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            poll.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "closed_at" in data and data["closed_at"]:
            poll.closed_at = datetime.fromisoformat(data["closed_at"])
            # Don't start timer if poll is already closed
            if poll.timer:
                poll.timer.cancel()
                poll.timer = None
        
        if "votes" in data:
            poll.votes = {user_id: set(option_indices) for user_id, option_indices in data["votes"].items()}
        
        logger.debug(
            "Loaded poll data",
            poll_id=poll.id,
            vote_count=len(poll.votes),
            is_closed=poll.is_closed()
        )
        return poll

    def add_vote(self, user_id: str, option_index: int) -> None:
        """
        Add a vote for a specific option.
        
        Args:
            user_id: ID of the voting user
            option_index: Index of the option to vote for (0-based)
            
        Raises:
            ValueError: If the option index is invalid or poll is closed
            VoteLimitExceededError: If the user has already voted the maximum number of times
        """
        if self.is_closed():
            logger.error(
                "Attempted to vote on closed poll",
                poll_id=self.id,
                user_id=user_id
            )
            raise ValueError("Poll is closed")
            
        if not 0 <= option_index < len(self.options):
            logger.error(
                "Invalid option index in vote",
                poll_id=self.id,
                user_id=user_id,
                invalid_index=option_index,
                option_count=len(self.options)
            )
            raise ValueError(f"Invalid option index: {option_index}")
        
        # Initialize user's votes if not present
        if user_id not in self.votes:
            self.votes[user_id] = set()
        
        # Check if user has already voted for this option when not allowed
        if not self.allow_multiple_votes_per_option and option_index in self.votes[user_id]:
            logger.error(
                "User attempted to vote for same option multiple times",
                poll_id=self.id,
                user_id=user_id,
                option_index=option_index
            )
            raise ValueError(f"User {user_id} has already voted for option {option_index}")
        
        # Check vote limit
        # Even with allow_multiple_votes_per_option, users are still limited by max_votes_per_user
        if len(self.votes[user_id]) >= self.max_votes_per_user:
            logger.error(
                "User exceeded vote limit",
                poll_id=self.id,
                user_id=user_id,
                current_votes=len(self.votes[user_id]),
                max_votes=self.max_votes_per_user
            )
            raise VoteLimitExceededError(
                user_id, 
                len(self.votes[user_id]), 
                self.max_votes_per_user
            )
        
        # Add the vote
        self.votes[user_id].add(option_index)
        self.updated_at = datetime.now()
        
        logger.debug(
            "Recorded vote",
            poll_id=self.id,
            user_id=user_id,
            option_index=option_index,
            total_votes=len(self.votes)
        )

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
            List of vote counts, indexed by option
        """
        counts = [0] * len(self.options)
        for votes in self.votes.values():
            for idx in votes:
                counts[idx] += 1
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
            logger.error(
                "Invalid option index",
                poll_id=self.id,
                invalid_index=option_index,
                option_count=len(self.options)
            )
            raise ValueError(f"Invalid option index: {option_index}")
        
        return sum(1 for votes in self.votes.values() if option_index in votes)

    def close(self) -> None:
        """Close the poll for voting."""
        if not self.is_closed():
            self.closed_at = datetime.now()
            self.updated_at = self.closed_at
            
            # Cancel the timer if it exists
            if self.timer:
                self.timer.cancel()
                self.timer = None
            
            winning_options = self.get_winning_options()
            logger.info(
                "Closed poll",
                poll_id=self.id,
                total_votes=len(self.votes),
                winning_options=winning_options,
                winning_vote_count=self.get_vote_count(winning_options[0]) if winning_options else 0
            )

    def is_closed(self) -> bool:
        """Check if the poll is closed."""
        return self.closed_at is not None

    def get_winning_options(self) -> List[int]:
        """Get indices of options with the most votes."""
        counts = self.get_vote_counts()
        if not counts:
            return []
        
        max_votes = max(counts)
        return [i for i, count in enumerate(counts) if count == max_votes]

    def get_vote_count(self, option_index: int) -> int:
        """Get number of votes for a specific option."""
        if not 0 <= option_index < len(self.options):
            logger.error(
                "Invalid option index",
                poll_id=self.id,
                invalid_index=option_index,
                option_count=len(self.options)
            )
            raise ValueError(f"Invalid option index: {option_index}")
        
        count = sum(1 for votes in self.votes.values() if option_index in votes)
        logger.debug(
            "Retrieved vote count",
            poll_id=self.id,
            option_index=option_index,
            count=count
        )
        return count


# In-memory storage for active polls
active_polls: Dict[str, Poll] = {}
archived_polls: Dict[str, Poll] = {}