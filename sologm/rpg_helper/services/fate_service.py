"""
Service for handling Mythic GM Emulator fate checks.
"""
import random
from typing import Dict, Union


# Mythic GM Emulator fate chart results
FATE_CHART = {
    "Exceptional No": "The answer is definitely no, and something exceptionally negative happens.",
    "No": "The answer is no.",
    "Weak No": "The answer is probably no, but with some uncertainty.",
    "Weak Yes": "The answer is probably yes, but with some uncertainty.",
    "Yes": "The answer is yes.",
    "Exceptional Yes": "The answer is definitely yes, and something exceptionally positive happens."
}

# Likelihood map
LIKELIHOOD_MAP = {
    "impossible": 0,
    "very unlikely": 1,
    "unlikely": 2,
    "50/50": 3,
    "likely": 4, 
    "very likely": 5,
    "near certain": 6
}


def fate_check(chaos_factor: str, likelihood: str) -> Dict[str, Union[bool, str, int]]:
    """
    Perform a Mythic GM Emulator fate check.
    
    Args:
        chaos_factor: Chaos factor (1-9)
        likelihood: Likelihood description (impossible, unlikely, etc.)
        
    Returns:
        Dictionary with fate check results or error information
    """
    # Validate likelihood
    likelihood_lower = likelihood.lower()
    if likelihood_lower not in LIKELIHOOD_MAP:
        return {
            "success": False, 
            "error": "Invalid likelihood. Use: Impossible, Very Unlikely, Unlikely, 50/50, Likely, Very Likely, Near Certain"
        }
    
    # Validate chaos factor
    try:
        chaos_int = int(chaos_factor)
        if not 1 <= chaos_int <= 9:
            return {
                "success": False, 
                "error": "Chaos factor must be between 1 and 9"
            }
    except ValueError:
        return {
            "success": False, 
            "error": "Chaos factor must be a number between 1 and 9"
        }
    
    # Roll d100
    roll = random.randint(1, 100)
    
    # Determine fate based on likelihood and chaos factor
    likelihood_value = LIKELIHOOD_MAP[likelihood_lower]
    
    # Exceptional result on doubles (11, 22, 33, etc.) only if the answer is yes or no
    is_exceptional = (roll % 11 == 0) and roll <= 99
    
    # Determine the base threshold for a "Yes" result
    # The more likely, the higher the threshold
    base_thresholds = [10, 25, 45, 50, 55, 75, 85]
    threshold = base_thresholds[likelihood_value]
    
    # Adjust for chaos factor (higher chaos means more unexpected results)
    # For simplicity, each point of chaos above 5 decreases the threshold by 5%
    # Each point below 5 increases it by 5%
    threshold_modifier = (5 - chaos_int) * 5
    threshold += threshold_modifier
    
    # Determine result
    if roll <= threshold:
        result = "Exceptional Yes" if is_exceptional and roll <= threshold else "Yes"
        if 10 < threshold - roll <= 20:
            result = "Weak Yes"
    else:
        result = "Exceptional No" if is_exceptional and roll > threshold else "No"
        if 10 < roll - threshold <= 20:
            result = "Weak No"
    
    return {
        "success": True, 
        "roll": roll,
        "result": result,
        "description": FATE_CHART[result],
        "chaos_factor": chaos_int,
        "likelihood": likelihood
    }