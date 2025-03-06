"""
Mythic GME features.
"""
import random
import enum
from typing import Tuple, Dict, Any, List

class EventFocus(enum.Enum):
    """Event focus for Mythic GME random events."""
    REMOTE_EVENT = "Remote event"
    NPC_ACTION = "NPC action"
    INTRODUCE_NEW_NPC = "Introduce a new NPC"
    MOVE_TOWARD_A_THREAD = "Move toward a thread"
    MOVE_AWAY_FROM_A_THREAD = "Move away from a thread"
    CLOSE_A_THREAD = "Close a thread"
    PC_NEGATIVE = "PC negative"
    PC_POSITIVE = "PC positive"
    AMBIGUOUS_EVENT = "Ambiguous event"
    NPC_NEGATIVE = "NPC negative"
    NPC_POSITIVE = "NPC positive"

class EventMeaning:
    """Event meaning tables for Mythic GME."""
    
    # Action tables
    ACTIONS = [
        "Attainment", "Starting", "Neglect", "Fight", "Recruit", "Triumph",
        "Violate", "Oppose", "Malice", "Communicate", "Persecute", "Increase",
        "Decrease", "Abandon", "Gratify", "Inquire", "Antagonize", "Move",
        "Waste", "Truce", "Release", "Befriend", "Judge", "Desert", "Dominate",
        "Procrastinate", "Praise", "Separate", "Take", "Break", "Heal",
        "Delay", "Stop", "Lie", "Return", "Immitate", "Struggle", "Inform",
        "Bestow", "Postpone", "Expose", "Haggle", "Imprison", "Release",
        "Celebrate", "Develop", "Travel", "Block", "Harm", "Debase",
        "Overindulge", "Adjourn", "Adversity", "Kill", "Disrupt", "Usurp",
        "Create", "Betray", "Agree", "Abuse", "Oppress", "Inspect", "Ambush",
        "Spy", "Attach", "Carry", "Open", "Carelessness", "Ruin", "Extravagance",
        "Trick", "Arrive", "Propose", "Divide", "Refuse", "Mistrust",
        "Deceive", "Cruelty", "Intolerance", "Trust", "Excitement", "Activity",
        "Assist", "Care", "Negligence", "Passion", "Work", "Control",
        "Attract", "Failure", "Pursue", "Vengeance", "Proceedings", "Dispute",
        "Punish", "Guide", "Transform", "Overthrow", "Oppress", "Change"
    ]
    
    # Subject tables
    SUBJECTS = [
        "Goals", "Dreams", "Environment", "Outside", "Inside", "Reality",
        "Allies", "Enemies", "Evil", "Good", "Emotions", "Opposition",
        "War", "Peace", "The innocent", "Love", "The spiritual", "The intellectual",
        "New ideas", "Joy", "Messages", "Energy", "Balance", "Tension",
        "Friendship", "The physical", "A project", "Pleasures", "Pain", "Possessions",
        "Benefits", "Plans", "Lies", "Expectations", "Legal matters", "Bureaucracy",
        "Business", "A path", "News", "Exterior factors", "Advice", "A plot",
        "Competition", "Prison", "Illness", "Food", "Attention", "Success",
        "Failure", "Travel", "Jealousy", "Dispute", "Home", "Investment",
        "Suffering", "Wishes", "Tactics", "Stalemate", "Randomness", "Misfortune",
        "Death", "Disruption", "Power", "A burden", "Intrigues", "Fears",
        "Ambush", "Rumor", "Wounds", "Extravagance", "A representative", "Adversities",
        "Opulence", "Liberty", "Military", "The mundane", "Trials", "Masses",
        "Vehicle", "Art", "Victory", "Dispute", "Riches", "Status quo",
        "Technology", "Hope", "Magic", "Illusions", "Portals", "Danger",
        "Weapons", "Animals", "Weather", "Elements", "Nature", "The public",
        "Leadership", "Fame", "Anger", "Information"
    ]

class RandomEvent:
    """Random event for Mythic GME."""
    
    def __init__(self, focus: EventFocus, action: str, subject: str):
        """
        Initialize a random event.
        
        Args:
            focus: The event focus
            action: The event action
            subject: The event subject
        """
        self.focus = focus
        self.action = action
        self.subject = subject
    
    def __str__(self) -> str:
        """Return a string representation of the random event."""
        return f"{self.focus.value}: {self.action} of {self.subject}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the random event to a dictionary."""
        return {
            "focus": self.focus.value,
            "action": self.action,
            "subject": self.subject
        }

def generate_event_focus() -> EventFocus:
    """
    Generate a random event focus.
    
    Returns:
        A random event focus
    """
    return random.choice(list(EventFocus))

def generate_event_meaning() -> Tuple[str, str]:
    """
    Generate a random event meaning.
    
    Returns:
        A tuple of (action, subject)
    """
    action = random.choice(EventMeaning.ACTIONS)
    subject = random.choice(EventMeaning.SUBJECTS)
    return action, subject 