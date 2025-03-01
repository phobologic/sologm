"""
Service for generating interpretation options.
"""
import random
from typing import List


# Base interpretations for Mythic-style events
BASE_INTERPRETATIONS = [
    "A new character appears unexpectedly.",
    "A previous element in the story becomes significant.",
    "The environment changes in a meaningful way.",
    "An action is modified or altered.",
    "An expected event doesn't happen.",
    "Something happens to an NPC or faction.",
    "A physical object becomes important.",
    "A clue or information is revealed.",
    "The tone or emotional atmosphere shifts.",
    "A complication or obstacle appears.",
    "Progress toward a goal is made.",
    "A resource is gained or lost.",
    "A relationship changes.",
    "A misunderstanding occurs.",
    "A coincidence happens.",
    "Someone's motivation is revealed.",
    "A decision must be made quickly.",
    "Something breaks or fails.",
    "An opportunity presents itself.",
    "Something from the past returns."
]


def generate_mythic_interpretations(context: str = "", count: int = 5) -> List[str]:
    """
    Generate interpretation options based on Mythic GM Emulator concepts.
    
    Args:
        context: Optional context to add to interpretations
        count: Number of options to generate
        
    Returns:
        List of interpretation strings
    """
    # Select random interpretations from the base list
    selected = random.sample(
        BASE_INTERPRETATIONS, 
        min(count, len(BASE_INTERPRETATIONS))
    )
    
    # Add context to make them more specific if provided
    if context:
        context = context.strip()
        return [f"{interp} Related to: {context}" for interp in selected]
    
    return selected