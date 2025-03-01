"""
Service for managing interpretation polls.
"""
import random
import logging
from datetime import datetime, timedelta
from threading import Timer
from typing import Dict, List, Optional, Tuple

from slack_bolt import App

from rpg_helper.models.poll import Poll, active_polls

logger = logging.getLogger(__name__)


def create_poll(
    app: App,
    channel_id: str, 
    user_id: str, 
    options: List[str], 
    question: str, 
    timeout_hours: int = 4
) -> Poll:
    """
    Create a new interpretation poll.
    
    Args:
        app: Slack Bolt app instance
        channel_id: Slack channel ID
        user_id: User ID of the poll creator
        options: List of interpretation options
        question: Poll question text
        timeout_hours: Hours until poll expires
        
    Returns:
        The created Poll object
    """
    poll_id = f"{channel_id}-{int(datetime.now().timestamp())}"
    expiry_time = datetime.now() + timedelta(hours=timeout_hours)
    
    poll = Poll(
        id=poll_id,
        channel_id=channel_id,
        creator_id=user_id,
        question=question,
        options=options,
        expires_at=expiry_time
    )
    
    # Schedule poll expiration
    timer = Timer(timeout_hours * 3600, end_poll, args=[app, poll_id])
    timer.daemon = True
    timer.start()
    poll.timer = timer
    
    active_polls[poll_id] = poll
    return poll


def end_poll(app: App, poll_id: str) -> Optional[Dict]:
    """
    End a poll and announce results.
    
    Args:
        app: Slack Bolt app instance
        poll_id: ID of the poll to end
        
    Returns:
        Poll results or None if poll not found
    """
    if poll_id not in active_polls:
        return None
    
    poll = active_polls[poll_id]
    
    # Cancel timer if poll is ending early
    if poll.timer and poll.timer.is_alive():
        poll.timer.cancel()
    
    # Count votes
    vote_counts = {}
    for option_idx in range(len(poll.options)):
        vote_counts[option_idx] = 0
    
    for user_id, vote in poll.votes.items():
        vote_counts[vote] += 1
    
    # Find winning option(s)
    max_votes = max(vote_counts.values()) if vote_counts else 0
    winners = [idx for idx, count in vote_counts.items() if count == max_votes]
    
    # If there's a tie, pick randomly
    winner_idx = random.choice(winners) if winners else None
    winner_text = poll.options[winner_idx] if winner_idx is not None else "No votes were cast"
    
    # Prepare results
    results = {
        "poll_id": poll_id,
        "question": poll.question,
        "winner_idx": winner_idx,
        "winner_text": winner_text,
        "vote_counts": vote_counts
    }
    
    # Format results message
    results_text = f"*Poll Results*\n*Question:* {poll.question}\n\n*Winning interpretation:* {winner_text}\n\n*Voting breakdown:*"
    
    for idx, option in enumerate(poll.options):
        vote_count = vote_counts.get(idx, 0)
        is_winner = idx == winner_idx
        marker = "🏆 " if is_winner else ""
        results_text += f"\n{marker}{idx+1}. {option} - {vote_count} vote(s)"
    
    # Post results to Slack
    try:
        app.client.chat_postMessage(
            channel=poll.channel_id,
            text=results_text,
            thread_ts=poll.message_ts
        )
    except Exception as e:
        logger.error(f"Error posting poll results: {e}")
    
    # Clean up
    del active_polls[poll_id]
    
    return results


def get_channel_polls(channel_id: str) -> List[Poll]:
    """
    Get all active polls for a specific channel.
    
    Args:
        channel_id: Slack channel ID
        
    Returns:
        List of active polls in the channel
    """
    return [poll for poll in active_polls.values() if poll.channel_id == channel_id]


def get_user_polls(user_id: str) -> List[Poll]:
    """
    Get all active polls created by a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of active polls created by the user
    """
    return [poll for poll in active_polls.values() if poll.creator_id == user_id]


def record_vote(poll_id: str, user_id: str, option_idx: int) -> Tuple[bool, str]:
    """
    Record a user's vote in a poll.
    
    Args:
        poll_id: Poll ID
        user_id: User ID of the voter
        option_idx: Index of the option being voted for
        
    Returns:
        Tuple of (success, message)
    """
    if poll_id not in active_polls:
        return False, "This poll has expired or doesn't exist."
    
    poll = active_polls[poll_id]
    
    if option_idx < 0 or option_idx >= len(poll.options):
        return False, f"Invalid option index: {option_idx}"
    
    # Record the vote
    poll.votes[user_id] = option_idx
    
    return True, f"Your vote for *Option {option_idx+1}* has been recorded."