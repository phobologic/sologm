"""
Advanced Mythic GME features for the MythicGame class.
"""
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models2.game.mythic import MythicGame, MythicChaosFactor

logger = get_logger()

# Mythic GME tables
class EventFocus(str, Enum):
    """Event focus categories for Mythic GME."""
    REMOTE = "Remote event"
    NPC_ACTION = "NPC action"
    NEW_NPC = "Introduce a new NPC"
    MOVE_TOWARD = "Move toward a thread"
    MOVE_AWAY = "Move away from a thread"
    CLOSE_THREAD = "Close a thread"
    PC_NEGATIVE = "PC negative"
    PC_POSITIVE = "PC positive"
    AMBIGUOUS = "Ambiguous event"
    NPC_NEGATIVE = "NPC negative"
    NPC_POSITIVE = "NPC positive"

# Event meaning tables
ACTION_MEANINGS = [
    "Attainment", "Starting", "Neglect", "Fight", "Recruit", "Triumph", "Violate", "Oppose",
    "Malice", "Communicate", "Persecute", "Increase", "Decrease", "Abandon", "Gratify",
    "Inquire", "Antagonize", "Move", "Waste", "Truce", "Release", "Befriend", "Judge",
    "Desert", "Dominate", "Procrastinate", "Praise", "Separate", "Take", "Break",
    "Heal", "Delay", "Stop", "Lie", "Return", "Immitate", "Struggle", "Inform",
    "Bestow", "Postpone", "Expose", "Haggle", "Imprison", "Release", "Celebrate",
    "Develop", "Travel", "Block", "Harm", "Debase", "Overindulge", "Adjourn",
    "Adversity", "Kill", "Disrupt", "Usurp", "Create", "Betray", "Agree",
    "Abuse", "Oppress", "Inspect", "Ambush", "Spy", "Attach", "Carry",
    "Open", "Carelessness", "Ruin", "Extravagance", "Trick", "Arrive", "Propose",
    "Divide", "Refuse", "Mistrust", "Deceive", "Cruelty", "Intolerance", "Trust",
    "Excitement", "Activity", "Assist", "Care", "Negligence", "Passion", "Work hard",
    "Control", "Attract", "Failure", "Pursue", "Vengeance", "Proceedings", "Dispute",
    "Punish", "Guide", "Transform", "Overthrow", "Oppress", "Change"
]

SUBJECT_MEANINGS = [
    "Goals", "Dreams", "Environment", "Outside", "Inside", "Reality", "Allies", "Enemies",
    "Evil", "Good", "Emotions", "Opposition", "War", "Peace", "The innocent", "Love",
    "The spiritual", "The intellectual", "New ideas", "Joy", "Messages", "Energy", "Balance",
    "Tension", "Friendship", "The physical", "A project", "Pleasures", "Pain", "Possessions",
    "Benefits", "Plans", "Lies", "Expectations", "Legal matters", "Bureaucracy", "Business",
    "A path", "News", "Exterior factors", "Advice", "A plot", "Competition", "Prison",
    "Illness", "Food", "Attention", "Success", "Failure", "Travel", "Jealousy",
    "Dispute", "Home", "Investment", "Suffering", "Wishes", "Tactics", "Stalemate",
    "Random", "Misfortune", "Victory", "Dispute", "Riches", "Status quo", "Technology",
    "Hope", "Magic", "Illusions", "Portals", "Danger", "Weapons", "Animals",
    "Weather", "Elements", "Nature", "The public", "Leadership", "Fame", "Anger",
    "Information", "Messages", "Masses", "Vehicle", "Art"
]

def fate_check(self, odds: str) -> Tuple[bool, bool]:
    """
    Perform a fate check.
    
    Args:
        odds: The odds of success (e.g., "very likely", "50/50", etc.)
        
    Returns:
        Tuple of (success, exceptional)
    """
    # Map of odds to target numbers
    odds_map = {
        "impossible": 0,
        "no way": 1,
        "very unlikely": 2,
        "unlikely": 3,
        "50/50": 4,
        "somewhat likely": 5,
        "likely": 6,
        "very likely": 7,
        "near sure thing": 8,
        "sure thing": 9,
        "has to be": 10
    }
    
    # Get the target number
    target = odds_map.get(odds.lower(), 4)  # Default to 50/50
    
    # Roll the dice
    roll = random.randint(1, 10)
    
    # Check for exceptional result
    exceptional = (roll == 1 or roll == 10)
    
    # Determine success
    success = roll <= target
    
    # Check for random event
    random_event = False
    if exceptional:
        chaos_roll = random.randint(1, 10)
        random_event = chaos_roll <= self.chaos_factor
        
        if random_event:
            # Generate a random event
            event_focus, action, subject = self.generate_random_event()
            
            logger.info(
                "Random event triggered in fate check",
                game_id=self.id,
                odds=odds,
                roll=roll,
                target=target,
                chaos_factor=self.chaos_factor,
                chaos_roll=chaos_roll,
                event_focus=event_focus,
                action=action,
                subject=subject
            )
    
    logger.debug(
        "Performed fate check",
        game_id=self.id,
        odds=odds,
        roll=roll,
        target=target,
        success=success,
        exceptional=exceptional,
        random_event=random_event
    )
    
    return success, exceptional

def scene_check(self) -> Tuple[bool, str]:
    """
    Perform a scene check to determine if there's an altered scene.
    
    Returns:
        Tuple of (altered, alteration_type)
        where alteration_type is one of: "none", "interrupt", "altered"
    """
    # Roll the dice
    roll = random.randint(1, 10)
    
    # Check against chaos factor
    if roll > self.chaos_factor:
        logger.debug(
            "Scene check: No alteration",
            game_id=self.id,
            roll=roll,
            chaos_factor=self.chaos_factor
        )
        return False, "none"
    
    # Determine the type of alteration
    if roll % 2 == 0:
        logger.info(
            "Scene check: Interrupt",
            game_id=self.id,
            roll=roll,
            chaos_factor=self.chaos_factor
        )
        return True, "interrupt"
    else:
        logger.info(
            "Scene check: Altered",
            game_id=self.id,
            roll=roll,
            chaos_factor=self.chaos_factor
        )
        return True, "altered"

def generate_random_event(self) -> Tuple[str, str, str]:
    """
    Generate a random event for Mythic GME.
    
    Returns:
        Tuple of (event_focus, action, subject)
    """
    # Roll for event focus
    focus_roll = random.randint(1, 100)
    
    if focus_roll <= 7:
        event_focus = EventFocus.REMOTE.value
    elif focus_roll <= 28:
        event_focus = EventFocus.NPC_ACTION.value
    elif focus_roll <= 35:
        event_focus = EventFocus.NEW_NPC.value
    elif focus_roll <= 45:
        event_focus = EventFocus.MOVE_TOWARD.value
    elif focus_roll <= 52:
        event_focus = EventFocus.MOVE_AWAY.value
    elif focus_roll <= 55:
        event_focus = EventFocus.CLOSE_THREAD.value
    elif focus_roll <= 67:
        event_focus = EventFocus.PC_NEGATIVE.value
    elif focus_roll <= 75:
        event_focus = EventFocus.PC_POSITIVE.value
    elif focus_roll <= 83:
        event_focus = EventFocus.AMBIGUOUS.value
    elif focus_roll <= 92:
        event_focus = EventFocus.NPC_NEGATIVE.value
    else:
        event_focus = EventFocus.NPC_POSITIVE.value
    
    # Roll for meaning
    action = random.choice(ACTION_MEANINGS)
    subject = random.choice(SUBJECT_MEANINGS)
    
    logger.info(
        "Generated random event",
        game_id=self.id,
        event_focus=event_focus,
        action=action,
        subject=subject
    )
    
    return event_focus, action, subject

def record_random_event(self, scene_id: str, event_focus: str, action: str, subject: str, 
                       description: Optional[str] = None) -> 'SceneEvent':
    """
    Record a random event in a scene.
    
    Args:
        scene_id: The scene ID
        event_focus: The event focus
        action: The action meaning
        subject: The subject meaning
        description: Optional description of the event
        
    Returns:
        The created scene event
    """
    from sologm.rpg_helper.models2.scene_event import SceneEvent
    
    # Create a default description if none provided
    if description is None:
        description = f"Random Event: {event_focus} - {action} of {subject}"
    
    # Create the event
    event = SceneEvent(
        scene_id=scene_id,
        description=description,
        metadata={
            "type": "random_event",
            "event_focus": event_focus,
            "action": action,
            "subject": subject
        }
    )
    
    # Add the event to the session
    session = object_session(self)
    if session:
        session.add(event)
        session.commit()
    
    logger.info(
        "Recorded random event",
        game_id=self.id,
        scene_id=scene_id,
        event_focus=event_focus,
        action=action,
        subject=subject
    )
    
    return event

# Add the methods to the MythicGame class
MythicGame.fate_check = fate_check
MythicGame.scene_check = scene_check
MythicGame.generate_random_event = generate_random_event
MythicGame.record_random_event = record_random_event 