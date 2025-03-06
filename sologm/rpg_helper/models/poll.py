"""
Poll model for the RPG Helper application.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
import json

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer, Table
from sqlalchemy.orm import relationship, object_session

from sologm.rpg_helper.utils.logging import get_logger
from .base import BaseModel, get_session, close_session
from .game.errors import PollNotFoundError, PollClosedError

if TYPE_CHECKING:
    from .game.base import Game

logger = get_logger()

class PollStatus(str, Enum):
    """Status of a poll."""
    OPEN = "open"
    CLOSED = "closed"


class Vote(BaseModel):
    """
    SQLAlchemy model for votes in a poll.
    
    Represents a single vote cast by a user for an option in a poll.
    """
    # Foreign keys
    poll_id = Column(String(36), ForeignKey('polls.id'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Vote details
    option_index = Column(Integer, nullable=False)
    
    # Relationships
    poll = relationship("Poll", back_populates="votes")
    user = relationship("User")
    
    __table_args__ = (
        # A user can only vote once per poll
        {'sqlite_autoincrement': True},
    )
    
    def __init__(self, **kwargs):
        """Initialize a new vote."""
        super().__init__(**kwargs)
        logger.debug(
            "Created new vote",
            poll_id=self.poll_id,
            user_id=self.user_id,
            option_index=self.option_index
        )
    
    def __repr__(self):
        """String representation of the vote."""
        return f"<Vote(poll_id='{self.poll_id}', user_id='{self.user_id}', option_index={self.option_index})>"


class Poll(BaseModel):
    """
    SQLAlchemy model for polls.
    
    Represents a poll in a game, which can have multiple options and votes.
    """
    question = Column(String(255), nullable=False)
    options_json = Column(Text, nullable=False)  # JSON array of options
    status = Column(String(10), nullable=False, default=PollStatus.OPEN.value)
    closes_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Foreign key to game
    game_id = Column(String(36), ForeignKey('games.id'), nullable=False, index=True)
    
    # Relationships
    game = relationship("Game", back_populates="polls")
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        """Initialize a new poll."""
        # Handle options as a list
        if 'options' in kwargs:
            kwargs['options_json'] = json.dumps(kwargs.pop('options'))
        
        # Set closes_at if timeout is provided
        if 'timeout' in kwargs:
            timeout = kwargs.pop('timeout')
            kwargs['closes_at'] = datetime.now() + timedelta(seconds=timeout)
        
        super().__init__(**kwargs)
        logger.info(
            "Created new poll",
            poll_id=self.id,
            game_id=self.game_id,
            question=self.question,
            option_count=len(self.options),
            closes_at=self.closes_at.isoformat() if self.closes_at else None
        )
    
    def __repr__(self):
        """String representation of the poll."""
        return f"<Poll(id='{self.id}', game_id='{self.game_id}', question='{self.question}', status='{self.status}')>"
    
    @property
    def options(self) -> List[str]:
        """Get the poll options."""
        return json.loads(self.options_json)
    
    @options.setter
    def options(self, options: List[str]) -> None:
        """Set the poll options."""
        self.options_json = json.dumps(options)
    
    def is_open(self) -> bool:
        """Check if the poll is open."""
        # Check status
        if self.status != PollStatus.OPEN.value:
            return False
        
        # Check if it has timed out
        if self.closes_at and datetime.now() > self.closes_at:
            # Auto-close the poll
            self.close()
            return False
        
        return True
    
    def close(self) -> None:
        """
        Close the poll.
        
        This prevents further votes from being cast.
        """
        if self.status == PollStatus.CLOSED.value:
            logger.debug(
                "Attempted to close already closed poll",
                poll_id=self.id
            )
            return
        
        self.status = PollStatus.CLOSED.value
        self.closed_at = datetime.now()
        self.updated_at = datetime.now()
        
        logger.info(
            "Closed poll",
            poll_id=self.id,
            game_id=self.game_id,
            vote_count=len(self.votes)
        )
        
        # Save changes if the poll is already in a session
        session = object_session(self)
        if session:
            session.commit()
    
    def add_vote(self, user_id: str, option_index: int) -> Vote:
        """
        Add a vote to the poll.
        
        Args:
            user_id: ID of the user casting the vote
            option_index: Index of the option being voted for
            
        Returns:
            The created vote
            
        Raises:
            PollClosedError: If the poll is closed
            ValueError: If the option index is invalid
        """
        # Check if the poll is open
        if not self.is_open():
            logger.warning(
                "Attempted to vote on closed poll",
                poll_id=self.id,
                user_id=user_id
            )
            raise PollClosedError(self.id)
        
        # Check if the option index is valid
        if option_index < 0 or option_index >= len(self.options):
            logger.warning(
                "Invalid option index for vote",
                poll_id=self.id,
                user_id=user_id,
                option_index=option_index,
                option_count=len(self.options)
            )
            raise ValueError(f"Invalid option index: {option_index}")
        
        # Check if the user has already voted
        session = object_session(self) or get_session()
        try:
            existing_vote = session.query(Vote).filter_by(
                poll_id=self.id, user_id=user_id
            ).first()
            
            if existing_vote:
                # Update the existing vote
                old_option = existing_vote.option_index
                existing_vote.option_index = option_index
                existing_vote.updated_at = datetime.now()
                
                logger.info(
                    "Updated vote",
                    poll_id=self.id,
                    user_id=user_id,
                    old_option=old_option,
                    new_option=option_index
                )
                
                if session == object_session(self):
                    session.commit()
                
                return existing_vote
            
            # Create a new vote
            vote = Vote(
                poll_id=self.id,
                user_id=user_id,
                option_index=option_index
            )
            
            self.votes.append(vote)
            self.updated_at = datetime.now()
            
            if session == object_session(self):
                session.add(vote)
                session.commit()
            
            logger.info(
                "Added vote to poll",
                poll_id=self.id,
                user_id=user_id,
                option_index=option_index
            )
            
            return vote
        finally:
            if session != object_session(self):
                close_session(session)
    
    def get_results(self) -> Dict[int, int]:
        """
        Get the results of the poll.
        
        Returns:
            Dictionary mapping option indices to vote counts
        """
        results = {}
        
        # Initialize all options with 0 votes
        for i in range(len(self.options)):
            results[i] = 0
        
        # Count votes
        for vote in self.votes:
            results[vote.option_index] = results.get(vote.option_index, 0) + 1
        
        logger.debug(
            "Retrieved poll results",
            poll_id=self.id,
            vote_count=len(self.votes),
            results=results
        )
        
        return results
    
    def get_winning_option(self) -> Optional[int]:
        """
        Get the index of the winning option.
        
        Returns:
            Index of the winning option, or None if there are no votes or a tie
        """
        results = self.get_results()
        
        if not results:
            return None
        
        # Find the option(s) with the most votes
        max_votes = max(results.values())
        
        if max_votes == 0:
            return None
        
        winners = [option for option, count in results.items() if count == max_votes]
        
        # If there's a tie, return None
        if len(winners) > 1:
            logger.info(
                "Poll has tied winners",
                poll_id=self.id,
                winners=winners,
                vote_count=max_votes
            )
            return None
        
        logger.debug(
            "Retrieved winning option",
            poll_id=self.id,
            winner=winners[0],
            vote_count=max_votes
        )
        
        return winners[0]
    
    def get_winning_options(self) -> List[int]:
        """
        Get the indices of all winning options.
        
        Returns:
            List of indices of winning options (could be multiple in case of a tie)
            or an empty list if there are no votes
        """
        results = self.get_results()
        
        if not results or max(results.values()) == 0:
            return []
        
        # Find the option(s) with the most votes
        max_votes = max(results.values())
        winners = [option for option, count in results.items() if count == max_votes]
        
        logger.debug(
            "Retrieved winning options",
            poll_id=self.id,
            winners=winners,
            vote_count=max_votes,
            is_tie=len(winners) > 1
        )
        
        return winners
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Add options
        data['options'] = self.options
        del data['options_json']
        
        # Add results
        data['results'] = self.get_results()
        
        # Add winner and winners
        data['winner'] = self.get_winning_option()  # Single winner or None if tie
        data['winners'] = self.get_winning_options()  # All winners (could be multiple)
        
        # Add vote details
        data['votes'] = [
            {
                'user_id': vote.user_id,
                'option_index': vote.option_index
            }
            for vote in self.votes
        ]
        
        return data
    
    @classmethod
    def get_by_game(cls, game_id: str, status: Optional[PollStatus] = None) -> List[Poll]:
        """
        Get polls for a game, optionally filtered by status.
        
        Args:
            game_id: ID of the game
            status: Optional status to filter by
            
        Returns:
            List of polls ordered by creation date (newest first)
        """
        session = get_session()
        try:
            query = session.query(cls).filter_by(game_id=game_id)
            
            if status:
                query = query.filter_by(status=status.value)
            
            # Order by creation date, newest first
            query = query.order_by(cls.created_at.desc())
            
            polls = query.all()
            
            logger.debug(
                "Retrieved polls for game",
                game_id=game_id,
                status=status.value if status else "all",
                count=len(polls)
            )
            
            return polls
        finally:
            close_session(session)
    
    @classmethod
    def get_for_game(cls, game_id: str, poll_id: str) -> Poll:
        """
        Get a poll for a game by ID.
        
        Args:
            game_id: ID of the game
            poll_id: ID of the poll
            
        Returns:
            The poll
            
        Raises:
            PollNotFoundError: If the poll is not found
        """
        session = get_session()
        try:
            poll = session.query(cls).filter_by(game_id=game_id, id=poll_id).first()
            
            if not poll:
                logger.warning(
                    "Poll not found for game",
                    game_id=game_id,
                    poll_id=poll_id
                )
                raise PollNotFoundError(poll_id, game_id)
            
            logger.debug(
                "Retrieved poll for game",
                game_id=game_id,
                poll_id=poll_id
            )
            
            return poll
        finally:
            close_session(session) 