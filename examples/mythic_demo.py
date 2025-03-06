"""
Demonstration of Mythic GME features.
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sologm.rpg_helper.models.init_db import init_db
from sologm.rpg_helper.models import (
    User, 
    MythicGame, MythicChaosFactor, EventFocus,
    Scene, SceneStatus
)

def main():
    """Run the demonstration."""
    # Initialize the database in memory for this demo
    engine, Session = init_db(":memory:")
    
    # Create a session
    session = Session()
    
    try:
        # Create a user
        user = User(
            username="demo_user",
            display_name="Demo User"
        )
        session.add(user)
        
        # Create a Mythic GME game
        game = MythicGame(
            name="Demo Mythic Game",
            description="A demonstration of the Mythic GME game",
            channel_id="demo_channel",
            workspace_id="demo_workspace"
        )
        
        # Add the user as a member
        game.members.append(user)
        
        # Add the game to the session
        session.add(game)
        session.commit()
        
        # Create a scene
        scene = game.create_scene(
            title="The Adventure Begins",
            description="Our hero sets out on a journey."
        )
        
        # Add an event to the scene
        event = game.add_scene_event(
            scene_id=scene.id,
            description="The hero leaves home with only a backpack and a map."
        )
        
        # Print the game details
        print(f"Game: {game.name}")
        print(f"Description: {game.description}")
        print(f"Type: {game.game_type}")
        print(f"Chaos Factor: {game.chaos_factor}")
        print(f"Members: {[member.display_name for member in game.members]}")
        print()
        
        # Demonstrate fate checks
        print("=== Fate Checks ===")
        odds_levels = ["impossible", "very unlikely", "unlikely", "50/50", 
                      "somewhat likely", "likely", "very likely", "has to be"]
        
        for odds in odds_levels:
            success, exceptional = game.fate_check(odds)
            result = "Success" if success else "Failure"
            if exceptional:
                result += " (Exceptional)"
            print(f"Odds: {odds.capitalize()} - Result: {result}")
        print()
        
        # Demonstrate scene checks
        print("=== Scene Checks ===")
        for i in range(5):
            altered, alteration_type = game.scene_check()
            if altered:
                print(f"Scene Check {i+1}: {alteration_type.capitalize()}")
            else:
                print(f"Scene Check {i+1}: No alteration")
        print()
        
        # Demonstrate random events
        print("=== Random Events ===")
        for i in range(3):
            event_focus, action, subject = game.generate_random_event()
            print(f"Random Event {i+1}:")
            print(f"  Focus: {event_focus}")
            print(f"  Meaning: {action} of {subject}")
            
            # Record the random event
            event = game.record_random_event(
                scene_id=scene.id,
                event_focus=event_focus,
                action=action,
                subject=subject
            )
        print()
        
        # Print the scene with events
        print("=== Scene with Events ===")
        print(f"Scene: {scene.title}")
        print(f"Description: {scene.description}")
        print("Events:")
        for i, event in enumerate(scene.events, 1):
            print(f"  {i}. {event.description}")
            if event.metadata and event.metadata.get("type") == "random_event":
                print(f"     Focus: {event.metadata.get('event_focus')}")
                print(f"     Action: {event.metadata.get('action')}")
                print(f"     Subject: {event.metadata.get('subject')}")
        print()
        
        # Demonstrate chaos factor changes
        print("=== Chaos Factor Changes ===")
        print(f"Initial Chaos Factor: {game.chaos_factor}")
        
        game.increase_chaos()
        print(f"After increase: {game.chaos_factor}")
        
        game.increase_chaos()
        print(f"After another increase: {game.chaos_factor}")
        
        game.decrease_chaos()
        print(f"After decrease: {game.chaos_factor}")
        
        game.set_chaos_factor(MythicChaosFactor.MAX.value)
        print(f"Set to maximum: {game.chaos_factor}")
        
        game.set_chaos_factor(MythicChaosFactor.MIN.value)
        print(f"Set to minimum: {game.chaos_factor}")
        
    finally:
        # Close the session
        session.close()


if __name__ == "__main__":
    main() 