"""Dice rolling functionality."""

import logging
import random
import re
from dataclasses import dataclass
from typing import List

from sologm.utils.errors import DiceError

logger = logging.getLogger(__name__)

@dataclass
class DiceRoll:
    """Represents a dice roll result."""
    
    notation: str
    individual_results: List[int]
    modifier: int
    total: int
    reason: str | None = None

def parse_dice_notation(notation: str) -> tuple[int, int, int]:
    """Parse XdY+Z notation into components.
    
    Args:
        notation: Dice notation string (e.g., "2d6+3")
        
    Returns:
        Tuple of (number of dice, sides per die, modifier)
        
    Raises:
        DiceError: If notation is invalid
    """
    pattern = r"^(\d+)d(\d+)([+-]\d+)?$"
    match = re.match(pattern, notation)
    
    if not match:
        logger.error(f"Invalid dice notation: {notation}")
        raise DiceError(f"Invalid dice notation: {notation}")
    
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3) or 0)
    
    if count < 1:
        raise DiceError("Must roll at least 1 die")
    if sides < 2:
        raise DiceError("Die must have at least 2 sides")
        
    logger.debug(f"Parsed {notation} as {count}d{sides}{modifier:+d}")
    return count, sides, modifier

def roll_dice(notation: str, reason: str | None = None) -> DiceRoll:
    """Roll dice according to the specified notation.
    
    Args:
        notation: Dice notation string (e.g., "2d6+3")
        reason: Optional reason for the roll
        
    Returns:
        DiceRoll object with results
        
    Raises:
        DiceError: If notation is invalid
    """
    count, sides, modifier = parse_dice_notation(notation)
    
    logger.debug(f"Rolling {count}d{sides}{modifier:+d}")
    individual_results = [random.randint(1, sides) for _ in range(count)]
    total = sum(individual_results) + modifier
    
    logger.debug(f"Rolled {individual_results} + {modifier} = {total}")
    
    return DiceRoll(
        notation=notation,
        individual_results=individual_results,
        modifier=modifier,
        total=total,
        reason=reason
    )
