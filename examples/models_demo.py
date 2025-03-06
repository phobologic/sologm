"""
Demonstration of using the models.
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sologm.rpg_helper.models2.init_db import init_db
from sologm.rpg_helper.models2 import (
    User, 
    Game, GameType, MythicGame, MythicChaosFactor,
    Scene, SceneStatus,
    Poll
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
        
        # Create a poll
        poll = game.create_poll(
            question="Which direction should the hero go?",
            options=["North to the mountains", "East to the forest", "South to the sea"]
        )
        
        # Add a vote
        game.add_vote(poll.id, user.id, 1)  # Vote for "East to the forest"
        
        # Print the game details
        print(f"Game: {game.name}")
        print(f"Description: {game.description}")
        print(f"Type: {game.game_type}")
        print(f"Chaos Factor: {game.chaos_factor}")
        print(f"Members: {[member.display_name for member in game.members]}")
        print()
        
        # Print the scenes
        print("Scenes:")
        for scene in game.get_scenes():
            print(f"  - {scene.title}: {scene.status.value}")
            print(f"    Description: {scene.description}")
            print("    Events:")
            for event in scene.events:
                print(f"      * {event.description}")
        print()
        
        # Print the polls
        print("Polls:")
        for poll in game.get_polls():
            print(f"  - {poll.question}")
            print("    Options:")
            for i, option in enumerate(poll.options):
                votes = poll.get_results()[i]
                print(f"      {i}. {option} ({votes} votes)")
            
            winner = poll.get_winning_option()
            if winner is not None:
                print(f"    Winner: {poll.options[winner]}")
            else:
                winners = poll.get_winning_options()
                if winners:
                    print(f"    Tied winners: {', '.join(poll.options[w] for w in winners)}")
                else:
                    print("    No votes yet")
        
    finally:
        # Close the session
        session.close()


if __name__ == "__main__":
    main() 