"""
Service for handling dice rolls.
"""
import re
import random
from typing import Dict, List, Union, Tuple


# Regular expression for dice roll format (e.g., 2d6+3)
DICE_PATTERN = re.compile(r"(\d+)d(\d+)(?:([\+\-])(\d+))?")


class DiceRollError(Exception):
    """Exception raised for errors in the dice rolling process."""
    pass


def roll_dice(dice_str: str) -> Dict[str, Union[List[int], int, str]]:
    """
    Roll dice based on standard RPG notation (e.g., 2d6+3).
    
    Args:
        dice_str: Dice roll in standard notation (e.g., "2d6+3")
        
    Returns:
        Dictionary with roll results
        
    Raises:
        DiceRollError: If the dice format is invalid or exceeds limits
    """
    match = DICE_PATTERN.fullmatch(dice_str)
    if not match:
        raise DiceRollError("Invalid dice format. Use NdM+X (e.g., 2d6+3)")
    
    num_dice = int(match.group(1))
    dice_type = int(match.group(2))
    
    # Check for reasonable limits
    if num_dice > 30 or dice_type > 100:
        raise DiceRollError("Too many dice (>30) or too large dice (> d100) type requested.")
    
    # Roll the dice
    rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
    total = sum(rolls)
    
    # Apply modifier if present
    if match.group(3) and match.group(4):
        modifier_type = match.group(3)
        modifier_value = int(match.group(4))
        
        if modifier_type == '+':
            total += modifier_value
        else:  # '-'
            total -= modifier_value
    
    return {
        "rolls": rolls,
        "total": total,
        "dice_str": dice_str
    }