"""
Poll commands for the RPG Helper bot.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from sologm.rpg_helper.models import (
    Game, Poll, PollStatus, Vote,
    PollError, PollNotFoundError, PollClosedError
)
from sologm.rpg_helper.models.init_db import init_db
from sologm.rpg_helper.utils.logging import get_logger

# Initialize the database at module load time
init_db()

logger = get_logger()

def create_poll_command(
    game_id: str,
    question: str,
    options: List[str]
) -> Dict[str, Any]:
    """
    Create a new poll.
    
    Args:
        game_id: The game ID
        question: The poll question
        options: List of poll options
        
    Returns:
        The created poll as a dictionary
        
    Raises:
        NotFoundError: If the game is not found
    """
    logger.info(
        "Creating poll",
        game_id=game_id,
        question=question,
        option_count=len(options)
    )
    
    session = init_db()[1]()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            raise Game.NotFoundError(f"Game with ID {game_id} not found")
        
        # Create the poll
        poll = game.create_poll(
            question=question,
            options=options
        )
        
        # Commit the changes
        session.commit()
        
        logger.info(
            "Poll created",
            game_id=game_id,
            poll_id=poll.id,
            question=poll.question
        )
        
        return poll.to_dict()
    finally:
        session.close()

# Add other poll commands here... 