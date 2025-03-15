"""
Fantasy RPG Game Demo

This script demonstrates the functionality of the RPG Helper system
using a corporate-fantasy parody scenario.

Architectural Notes:
- Models (Game, Scene, Poll, User) handle their own state management and validation
- Services (GameService) handle creation of complex objects and coordinate between models
- Direct model access is preferred for state changes and queries
- Service methods are used only for operations requiring coordination or complex setup
"""
import sys
import logging
import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.rpg_helper.utils.story_logging import get_story_logger, setup_story_logging, STORY_LEVEL_ID, StoryLogFormatter
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.db.config import set_session_factory, get_session, close_session
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.services.game import GameService
from sologm.rpg_helper.models.user import User

# Get logger for this module
logger = get_story_logger()

def setup_database():
    """Set up an in-memory SQLite database."""
    # Create in-memory SQLite database
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create all tables
    BaseModel.metadata.create_all(engine)
    
    # Create and configure session factory
    session_factory = sessionmaker(bind=engine)
    set_session_factory(session_factory)
    
    return engine

def create_sample_users():
    """Create sample users for the demo."""
    # Get logger for this module
    logger = get_story_logger()
    
    user_data = [
        ("U1", "Randalf", "Randalf the Beige", "A wizard on a budget, sporting clearance-rack robes"),
        ("U2", "Swagorn", "Swagorn, Heir to the Throne of PTO", "Trying way too hard to be cool"),
        ("U3", "Bragolas", "Bragolas, @ArcheryInfluencer", "With too many followers"),
        ("U4", "Gimme", "Gimme, CFO of Mines Inc.", "With questionable capitalism tendencies")
    ]
    
    session = get_session()
    try:
        users = []
        for user_id, username, display_name, description in user_data:
            user = User(id=user_id, username=username, display_name=display_name)
            session.add(user)
            users.append(user)
        session.commit()
        
        # Eagerly load all attributes we'll need
        for user in users:
            # Access these attributes to ensure they're loaded
            _ = user.id
            _ = user.username
            _ = user.display_name
        
        # Log both technical and narrative information
        logger.debug(
            "Created sample users",
            users=[u.username for u in users]
        )
        
        # Story mode logs
        logger.story("Our intrepid heroes assemble:", prefix="User")
        for user, (_, _, _, description) in zip(users, user_data):
            logger.story(f"• {user.display_name} - {description}", prefix="User")
        
        return users
    finally:
        close_session(session)

def setup_logging(debug_mode=False):
    """Set up logging configuration based on mode.
    
    Args:
        debug_mode (bool): If True, show technical debug output.
                          If False, show narrative story output.
    """
    # Initialize logging with appropriate mode
    setup_story_logging(debug_mode=debug_mode)
    
    # Log the mode we're running in
    logger = get_story_logger()
    if debug_mode:
        logger.debug("Debug mode enabled - showing technical details")

def main():
    """Run the fantasy RPG demo.
    
    The demo follows these architectural patterns:
    1. Direct model usage for state management (settings, members, votes)
    2. Service usage for complex object creation (scenes, polls)
    3. Models handle their own validation and state changes
    4. Logging uses direct model references for consistency
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Fantasy RPG Demo')
    parser.add_argument('--debug', action='store_true',
                       help='Show detailed technical output instead of story mode')
    args = parser.parse_args()
    
    # Initialize logging based on mode
    setup_logging(args.debug)
    
    # Get logger for this module
    logger = get_story_logger()
    
    # Log both technical and narrative information
    logger.debug("Starting Fantasy RPG Demo in debug mode")
    logger.debug("Initializing database and core systems")
    logger.story("Welcome to The Fellowship of the Bling!", prefix="System")
    logger.story("Preparing the corporate-fantasy realm...", prefix="System")
    
    # Setup Phase
    engine = setup_database()
    logger.debug(
        "Database initialized",
        engine_url=str(engine.url)
    )
    
    # Create sample users - logging is now handled within the function
    users = create_sample_users()
    
    # Create a new game first
    session = get_session()
    try:
        # Game creation is done directly through the model as it's a simple operation
        game = Game(
            channel_id="C_BLING_CREW",
            workspace_id="W_MIDDLEMGMT",
            name="The Fellowship of the Bling",
            description="""
            In the corporate wasteland of Middle-Management, where productivity metrics are forged,
            a great evil has emerged: The One Bling, a cursed piece of jewelry that makes its wearer
            'literally just too extra.' Created by the dark lord CEO-ron in the fires of Mount Doom's Day,
            this gaudy accessory threatens to transform all who wear it into insufferable influencers.

            Now, an unlikely group of heroes must embark on an epic quest through the dangerous
            landscape of quarterly reviews, past the artisanal coffee shops of River-dale, and into
            the heart of More-door (a retail chain with aggressive expansion plans) to destroy the
            One Bling before its powers of cringe consume all of Middle-Management.

            Join Randalf the Beige (a wizard on a budget), Swagorn (a ranger trying way too hard
            to be cool), Bragolas (an elf with too many Instagram followers), and Gimme (a dwarf
            with questionable capitalism tendencies) as they navigate this corporate-fantasy realm
            where the greatest dangers are reply-all emails and team-building exercises.
            """.strip(),
            game_type=GameType.STANDARD
        )
        session.add(game)
        session.commit()

        logger.debug(
            "Created new game",
            game_id=game.id,
            name=game.name,
            type=game.game_type.value
        )
        
        # Split description into paragraphs and use the first one for initial story
        paragraphs = game.description.split('\n\n')
        logger.story(paragraphs[0].strip(), prefix="Game")
        
        # GameService is used primarily for operations requiring coordination
        # between multiple models or complex setup. Here it's kept only for
        # scene and poll creation.
        game_service = GameService(game)  # Keep for scene/poll creation only
        
        # Add members to the game - Randalf is the game master
        randalf = users[0]  # Game master
        fellowship_members = users[1:]  # Other members
        
        # Member management is handled directly by the Game model
        if not game.is_member(randalf.id):
            game.add_member(randalf)
            logger.debug(
                "Added game master",
                game_id=game.id,
                user_id=randalf.id,
                username=randalf.username
            )
            logger.story(f"{randalf.display_name} takes charge as the game master", prefix="Game")
        
        # Add the rest of the fellowship
        member_descriptions = []
        for user in fellowship_members:
            try:
                game.add_member(user)
                logger.debug(
                    "Added member to game",
                    game_id=game.id,
                    user_id=user.id,
                    username=user.username
                )
                member_descriptions.append(user.display_name)
            except ValueError as e:
                logger.error(
                    "Failed to add member to game",
                    game_id=game.id,
                    user_id=user.id,
                    username=user.username,
                    error=str(e)
                )
        
        if member_descriptions:
            logger.story(
                f"The fellowship grows as {', '.join(member_descriptions[:-1])} and {member_descriptions[-1]} join the quest",
                prefix="Game"
            )
        
        # Configure game settings
        game.set_setting("difficulty", "business-casual")  # Updated from "hard"
        game.set_setting("allow_magic", True)  # But only if it fits in the budget
        game.set_setting("max_party_size", 9)  # The Fellowship's Slack channel limit
        
        logger.debug(
            "Game settings configured",
            game_id=game.id,
            settings={
                "difficulty": game.get_setting("difficulty"),
                "allow_magic": game.get_setting("allow_magic"),
                "max_party_size": game.get_setting("max_party_size")
            }
        )
        
        logger.story(
            "The quest difficulty is set to 'business-casual' (magic allowed, but only if it fits the budget)",
            prefix="Game"
        )
        logger.story(
            "The fellowship's Slack channel is capped at 9 members to avoid notification chaos",
            prefix="Game"
        )
        
        logger.info(
            "Initial setup complete",
            game_id=game.id
        )
        
        # Scene creation is handled by the service as it requires setup and coordination
        scene = game_service.create_scene(
            title="The Meeting That Could Have Been an Email",
            description="""
            In the fluorescent-lit chambers of River-dale's WeWork space, 
            the greatest minds of Middle-Management gather to discuss the 
            fate of a cursed piece of jewelry that's been circulating through 
            the office (and causing way too many inspirational LinkedIn posts).
            """.strip()
        )
        
        logger.debug(
            "Created opening scene",
            game_id=game.id,
            scene_id=scene.id,
            title=scene.title
        )
        logger.story(f"[{scene.title}]", prefix="Scene")
        logger.story(scene.description, prefix="Scene")
        
        # Add initial scene events
        scene_events = [
            ("""
            Randalf the Beige stands up, straightens his clearance-rack robes, 
            and begins his 47-slide PowerPoint presentation titled 
            'The One Bling: A Deep Dive into Workplace Culture Threats (Q3 Edition)'
            """.strip(), randalf),
            
            ("""
            *Fifteen minutes into the presentation*
            
            Swagorn, trying to look casual while secretly practicing his 
            "thoughtful leader" pose, raises his hand: "But what if we 
            just uploaded it to the cloud?"
            """.strip(), users[1]),
            
            ("""
            Bragolas, without looking up from his phone: "My followers 
            would literally die if they saw this ring. Like, literally. 
            Maybe we should do an unboxing video?"
            """.strip(), users[2]),
            
            ("""
            Gimme adjusts his crypto-mining rig cooling fan and clears 
            his throat: "Have we considered the NFT angle? I know a guy..."
            """.strip(), users[3])
        ]
        
        # Add and log each event
        for event_text, character in scene_events:
            scene.add_event(event_text)
            logger.debug(
                "Added scene event",
                scene_id=scene.id,
                character=character.username,
                text_length=len(event_text)
            )
            logger.story(event_text, prefix="SceneEvent")
        
        # Poll creation and setup
        poll = game_service.create_poll(
            question="How Should We Deal With the One Bling?",
            options=[
                "Destroy it in Mount Doom's Day (requires overtime)",
                "Sell it on Corporate Marketplace",
                "Re-gift it at the holiday party",
                "Create a committee to evaluate options"
            ]
        )
        
        logger.debug(
            "Created decision poll",
            game_id=game.id,
            poll_id=poll.id,
            question=poll.question,
            option_count=len(poll.options)
        )
        logger.story(f"A critical decision looms: {poll.question}", prefix="Poll")
        logger.story("The options are:", prefix="Poll")
        for i, option in enumerate(poll.options, 1):
            logger.story(f"{i}. {option}", prefix="Poll")
        
        # Add scene event about the poll
        poll_announcement = """
            Randalf the Beige, realizing this meeting has already gone 30 minutes over time,
            hastily creates a poll in the #bling-quest Slack channel: "Let's take this
            offline and circle back with our thoughts. Please fill out the poll by EOD."
            """.strip()
        scene.add_event(poll_announcement)
        logger.story(poll_announcement, prefix="SceneEvent")
        
        # Vote management is handled directly by the Poll model
        # Track votes for narrative
        votes = [
            (users[1], 3, "wanting to network"),
            (users[2], 3, "eyeing the social chair position"),
            (users[3], 3, "seeing an opportunity to lead"),
            (users[0], 0, "desperately trying to save everyone's time")
        ]
        
        for user, choice, reason in votes:
            poll.add_vote(user.id, choice)
            logger.debug(
                "Recorded vote",
                poll_id=poll.id,
                user=user.username,
                choice=choice
            )
            option_text = poll.options[choice]
            logger.story(
                f"{user.display_name} votes to {option_text.lower()} ({reason})",
                prefix="Poll"
            )

        # Get poll results using built-in methods
        results = poll.get_results()
        winning_index = poll.get_winning_option()
        
        logger.debug(
            "Poll results",
            poll_id=poll.id,
            results=results,
            winning_option=poll.options[winning_index]
        )
        logger.story("The votes are tallied...", prefix="Poll")
        for i, option in enumerate(poll.options):
            vote_count = results.get(i, 0)  # Get vote count for this option index
            logger.story(f"• {option}: {vote_count} votes", prefix="Poll")
        logger.story(f"\nThe winner is: {poll.options[winning_index]}!", prefix="Poll")
        
        # Add final scene event showing the landslide committee victory
        results_event = f"""
            The results are in:
            - Committee Formation: {results.get(3, 0)} votes
            - Ring Destruction: {results.get(0, 0)} votes
            - Marketplace Sale: {results.get(1, 0)} votes
            - Holiday Re-gift: {results.get(2, 0)} votes
            
            Despite Randalf's protests about "unnecessary bureaucracy" and "the fate of Middle-Management hanging in the balance,"
            the committee option has won by a landslide. Gimme has already sent out calendar invites for the first "Bling Disposal
            Strategy Planning Committee Kick-off Pre-meeting Sync."
            """.strip()
        
        scene.add_event(results_event)
        logger.story(results_event, prefix="SceneEvent")
        
        # Complete the first scene
        scene.complete()
        logger.debug(
            "Completed opening scene",
            scene_id=scene.id,
            event_count=len(scene.events)
        )
        logger.story("The meeting finally ends, but this is just the beginning...", prefix="Scene")
        
        # Create the follow-up scene based on the winning option
        next_scene = game_service.create_scene(
            title="The First Committee Meeting (of Many)",
            description="""
            One week later, in Conference Room Mordor (the one with the broken projector),
            the newly formed Committee for the Strategic Assessment of Jewelry-Related
            Workplace Enhancement Limitations (C-SAJWEL) convenes its first meeting.
            The agenda includes ice breakers, sub-committee assignments, and a heated
            debate about the committee's official Zoom background.
            """.strip()
        )
        
        logger.debug(
            "Created follow-up scene",
            scene_id=next_scene.id,
            title=next_scene.title
        )
        logger.story(f"\n[{next_scene.title}]", prefix="Scene")
        logger.story(next_scene.description, prefix="Scene")
        
        # Add initial events for the new scene with character context
        committee_events = [
            ("""
            Gimme, sporting a new "Committee Chair" nameplate and a power tie,
            opens the meeting: "Before we begin, let's go around and share our
            names, roles, and favorite corporate buzzwords. I'll start:
            'Synergy.'"
            """.strip(), users[3]),
            
            ("""
            Bragolas raises his hand: "Point of order! Shouldn't we first
            establish our committee's social media presence? I've already
            designed our LinkedIn banner and TikTok strategy."
            """.strip(), users[2]),
            
            ("""
            Swagorn, who has somehow acquired a laser pointer: "I've prepared
            a 90-slide deck on 'The Journey to Excellence: A Deep Dive into
            Ring Disposal Best Practices and Thought Leadership.'"
            """.strip(), users[1]),
            
            ("""
            Randalf, slumped in his chair and clutching his clearance-rack
            coffee mug, mutters something about "could've been halfway to
            Mount Doom's Day by now" while marking his calendar for the
            next six months of weekly committee meetings.
            """.strip(), users[0])
        ]
        
        # Add and log each committee event
        for event_text, character in committee_events:
            next_scene.add_event(event_text)
            logger.debug(
                "Added committee scene event",
                scene_id=next_scene.id,
                character=character.username,
                text_length=len(event_text)
            )
            logger.story(event_text, prefix="SceneEvent")
        
        # Complete the second scene
        next_scene.complete()
        logger.debug(
            "Completed committee scene",
            scene_id=next_scene.id,
            event_count=len(next_scene.events)
        )
        logger.story("\nAnd so begins the long journey through corporate bureaucracy...", prefix="Scene")
    finally:
        close_session(session)

if __name__ == "__main__":
    main() 