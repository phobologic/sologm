"""
Data models for polls and voting.
"""
from dataclasses import dataclass, field
from datetime import datetime
from threading import Timer
from typing import Dict, List, Optional, Union


@dataclass
class Poll:
    """
    Represents a poll for interpretation voting.
    """
    id: str
    channel_id: str
    creator_id: str
    question: str
    options: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    message_ts: Optional[str] = None
    votes: Dict[str, int] = field(default_factory=dict)
    timer: Optional[Timer] = None

    def to_dict(self) -> Dict[str, Union[str, List[str], Dict[str, int]]]:
        """Convert to dictionary (excluding timer for serialization)."""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "creator_id": self.creator_id,
            "question": self.question,
            "options": self.options,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "message_ts": self.message_ts,
            "votes": self.votes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, List[str], Dict[str, int]]]) -> 'Poll':
        """Create from dictionary."""
        poll = cls(
            id=data["id"],
            channel_id=data["channel_id"],
            creator_id=data["creator_id"],
            question=data["question"],
            options=data["options"],
            votes=data.get("votes", {})
        )
        
        if "created_at" in data:
            poll.created_at = datetime.fromisoformat(data["created_at"])
        
        if "expires_at" in data and data["expires_at"]:
            poll.expires_at = datetime.fromisoformat(data["expires_at"])
        
        if "message_ts" in data:
            poll.message_ts = data["message_ts"]
        
        return poll


# In-memory storage for active polls
active_polls: Dict[str, Poll] = {}