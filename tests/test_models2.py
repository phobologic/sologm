"""
Tests for the models2 package.
"""
import os
import unittest
from datetime import datetime, timedelta
import tempfile
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.rpg_helper.models2.base import BaseModel, get_session, set_session_factory
from sologm.rpg_helper.models2 import (
    User, 
    Game, GameType, MythicGame, MythicChaosFactor, ChaosBoundaryError,
    Scene, SceneStatus, SceneEvent,
    Poll, PollStatus, Vote,
    GameSetting
)


class TestModels(unittest.TestCase):
    """Test case for the models2 package."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        
        # Create all tables
        BaseModel.metadata.create_all(self.engine)
        
        # Create a session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Set the session factory for the models
        set_session_factory(self.Session)
        
        # Create a session
        self.session = self.Session()
    
    def tearDown(self):
        """Tear down the test case."""
        # Close the session
        self.session.close()
        
        # Remove the temporary database
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_user(self):
        """Test the User model."""
        # Create a user
        user = User(
            username="test_user",
            display_name="Test User"
        )
        
        # Add the user to the session
        self.session.add(user)
        self.session.commit()
        
        # Retrieve the user
        retrieved_user = self.session.query(User).filter_by(username="test_user").first()
        
        # Check that the user was retrieved
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "test_user")
        self.assertEqual(retrieved_user.display_name, "Test User")
    
    def test_game(self):
        """Test the Game model."""
        # Create a user
        user = User(
            username="test_user",
            display_name="Test User"
        )
        
        # Create a game
        game = Game(
            name="Test Game",
            description="A test game",
            channel_id="test_channel",
            workspace_id="test_workspace"
        )
        
        # Add the user as a member
        game.members.append(user)
        
        # Add the game to the session
        self.session.add(game)
        self.session.commit()
        
        # Retrieve the game
        retrieved_game = self.session.query(Game).filter_by(name="Test Game").first()
        
        # Check that the game was retrieved
        self.assertIsNotNone(retrieved_game)
        self.assertEqual(retrieved_game.name, "Test Game")
        self.assertEqual(retrieved_game.description, "A test game")
        self.assertEqual(retrieved_game.channel_id, "test_channel")
        self.assertEqual(retrieved_game.workspace_id, "test_workspace")
        self.assertEqual(retrieved_game.game_type, GameType.GENERIC.value)
        self.assertTrue(retrieved_game.is_active)
        
        # Check that the user is a member
        self.assertEqual(len(retrieved_game.members), 1)
        self.assertEqual(retrieved_game.members[0].username, "test_user")
    
    def test_mythic_game(self):
        """Test the MythicGame model."""
        # Create a mythic game
        game = MythicGame(
            name="Test Mythic Game",
            description="A test mythic game",
            channel_id="test_channel",
            workspace_id="test_workspace",
            chaos_factor=MythicChaosFactor.AVERAGE.value
        )
        
        # Add the game to the session
        self.session.add(game)
        self.session.commit()
        
        # Retrieve the game
        retrieved_game = self.session.query(Game).filter_by(name="Test Mythic Game").first()
        
        # Check that the game was retrieved
        self.assertIsNotNone(retrieved_game)
        self.assertEqual(retrieved_game.name, "Test Mythic Game")
        self.assertEqual(retrieved_game.game_type, GameType.MYTHIC_GME.value)
        
        # Check that it's a MythicGame
        self.assertIsInstance(retrieved_game, MythicGame)
        self.assertEqual(retrieved_game.chaos_factor, MythicChaosFactor.AVERAGE.value)
        
        # Test chaos factor methods
        retrieved_game.increase_chaos()
        self.assertEqual(retrieved_game.chaos_factor, MythicChaosFactor.AVERAGE.value + 1)
        
        retrieved_game.decrease_chaos()
        self.assertEqual(retrieved_game.chaos_factor, MythicChaosFactor.AVERAGE.value)
        
        retrieved_game.set_chaos_factor(MythicChaosFactor.HIGH.value)
        self.assertEqual(retrieved_game.chaos_factor, MythicChaosFactor.HIGH.value)
        
        # Test chaos factor validation
        with self.assertRaises(ChaosBoundaryError):
            retrieved_game.set_chaos_factor(MythicChaosFactor.MAX.value + 1)
        
        with self.assertRaises(ChaosBoundaryError):
            retrieved_game.set_chaos_factor(MythicChaosFactor.MIN.value - 1)
    
    def test_scene(self):
        """Test the Scene model."""
        # Create a game
        game = Game(
            name="Test Game",
            description="A test game",
            channel_id="test_channel",
            workspace_id="test_workspace"
        )
        
        # Add the game to the session
        self.session.add(game)
        self.session.commit()
        
        # Create a scene
        scene = Scene(
            title="Test Scene",
            description="A test scene",
            game_id=game.id
        )
        
        # Add the scene to the session
        self.session.add(scene)
        self.session.commit()
        
        # Retrieve the scene
        retrieved_scene = self.session.query(Scene).filter_by(title="Test Scene").first()
        
        # Check that the scene was retrieved
        self.assertIsNotNone(retrieved_scene)
        self.assertEqual(retrieved_scene.title, "Test Scene")
        self.assertEqual(retrieved_scene.description, "A test scene")
        self.assertEqual(retrieved_scene.game_id, game.id)
        self.assertEqual(retrieved_scene.status, SceneStatus.ACTIVE)
        
        # Add an event
        event = SceneEvent(
            description="A test event",
            scene_id=retrieved_scene.id
        )
        
        # Add the event to the session
        self.session.add(event)
        self.session.commit()
        
        # Retrieve the scene with events
        retrieved_scene = self.session.query(Scene).filter_by(title="Test Scene").first()
        
        # Check that the event was added
        self.assertEqual(len(retrieved_scene.events), 1)
        self.assertEqual(retrieved_scene.events[0].description, "A test event")
        
        # Complete the scene
        retrieved_scene.complete()
        self.session.commit()
        
        # Retrieve the scene again
        retrieved_scene = self.session.query(Scene).filter_by(title="Test Scene").first()
        
        # Check that the scene was completed
        self.assertEqual(retrieved_scene.status, SceneStatus.COMPLETED)
        self.assertIsNotNone(retrieved_scene.completed_at)
    
    def test_poll(self):
        """Test the Poll model."""
        # Create a game
        game = Game(
            name="Test Game",
            description="A test game",
            channel_id="test_channel",
            workspace_id="test_workspace"
        )
        
        # Add the game to the session
        self.session.add(game)
        self.session.commit()
        
        # Create a poll
        poll = Poll(
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            game_id=game.id
        )
        
        # Add the poll to the session
        self.session.add(poll)
        self.session.commit()
        
        # Retrieve the poll
        retrieved_poll = self.session.query(Poll).filter_by(question="Test Question").first()
        
        # Check that the poll was retrieved
        self.assertIsNotNone(retrieved_poll)
        self.assertEqual(retrieved_poll.question, "Test Question")
        self.assertEqual(retrieved_poll.options, ["Option 1", "Option 2", "Option 3"])
        self.assertEqual(retrieved_poll.game_id, game.id)
        self.assertEqual(retrieved_poll.status, PollStatus.OPEN.value)
        
        # Create a user
        user = User(
            username="test_user",
            display_name="Test User"
        )
        
        # Add the user to the session
        self.session.add(user)
        self.session.commit()
        
        # Add a vote
        retrieved_poll.add_vote(user.id, 1)
        self.session.commit()
        
        # Retrieve the poll with votes
        retrieved_poll = self.session.query(Poll).filter_by(question="Test Question").first()
        
        # Check that the vote was added
        self.assertEqual(len(retrieved_poll.votes), 1)
        self.assertEqual(retrieved_poll.votes[0].user_id, user.id)
        self.assertEqual(retrieved_poll.votes[0].option_index, 1)
        
        # Check the results
        results = retrieved_poll.get_results()
        self.assertEqual(results[0], 0)
        self.assertEqual(results[1], 1)
        self.assertEqual(results[2], 0)
        
        # Close the poll
        retrieved_poll.close()
        self.session.commit()
        
        # Retrieve the poll again
        retrieved_poll = self.session.query(Poll).filter_by(question="Test Question").first()
        
        # Check that the poll was closed
        self.assertEqual(retrieved_poll.status, PollStatus.CLOSED.value)
        self.assertIsNotNone(retrieved_poll.closed_at)
    
    def test_game_settings(self):
        """Test the GameSetting model."""
        # Create a game
        game = Game(
            name="Test Game",
            description="A test game",
            channel_id="test_channel",
            workspace_id="test_workspace"
        )
        
        # Add the game to the session
        self.session.add(game)
        self.session.commit()
        
        # Set a setting
        game.set_setting("test_setting", "test_value")
        
        # Retrieve the game
        retrieved_game = self.session.query(Game).filter_by(name="Test Game").first()
        
        # Check that the setting was set
        self.assertEqual(len(retrieved_game.settings), 1)
        self.assertEqual(retrieved_game.settings[0].name, "test_setting")
        self.assertEqual(retrieved_game.settings[0].value, "test_value")
        
        # Get the setting
        setting_value = retrieved_game.get_setting("test_setting")
        self.assertEqual(setting_value, "test_value")
        
        # Get a non-existent setting with default
        setting_value = retrieved_game.get_setting("non_existent", "default_value")
        self.assertEqual(setting_value, "default_value")
        
        # Update the setting
        game.set_setting("test_setting", "updated_value")
        
        # Retrieve the game again
        retrieved_game = self.session.query(Game).filter_by(name="Test Game").first()
        
        # Check that the setting was updated
        self.assertEqual(len(retrieved_game.settings), 1)
        self.assertEqual(retrieved_game.settings[0].name, "test_setting")
        self.assertEqual(retrieved_game.settings[0].value, "updated_value")


if __name__ == "__main__":
    unittest.main() 