"""
Tests for the base Game class.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from sologm.rpg_helper.models.game.base import Game, GameSettings
from sologm.rpg_helper.models.scene import Scene, SceneStatus

class TestGameSettings:
    """Tests for the GameSettings class."""
    
    def test_init(self):
        """Test GameSettings initialization."""
        settings = GameSettings()
        
        # Check default values
        assert settings.scene_default_status == "active"
        assert settings.scene_allow_multiple_active is False
        assert settings.poll_default_timeout == 60
        assert settings.poll_default_option_count == 5
        assert settings.poll_default_max_votes == 1
        assert settings.poll_allow_multiple_votes_per_option is False
    
    def test_getitem(self):
        """Test dictionary-style access to settings."""
        settings = GameSettings()
        
        assert settings["scene_default_status"] == "active"
        assert settings["poll_default_timeout"] == 60
        
        with pytest.raises(AttributeError):
            _ = settings["nonexistent_setting"]
    
    def test_get(self):
        """Test get method with default."""
        settings = GameSettings()
        
        assert settings.get("scene_default_status") == "active"
        assert settings.get("nonexistent_setting") is None
        assert settings.get("nonexistent_setting", "default") == "default"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = GameSettings(
            scene_default_status="inactive",
            poll_default_timeout=120
        )
        
        result = settings.to_dict()
        
        assert result["scene_default_status"] == "inactive"
        assert result["poll_default_timeout"] == 120
        assert result["poll_default_max_votes"] == 1
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "scene_default_status": "inactive",
            "poll_default_timeout": 120,
            "extra_field": "should be ignored"
        }
        
        settings = GameSettings.from_dict(data)
        
        assert settings.scene_default_status == "inactive"
        assert settings.poll_default_timeout == 120
        assert settings.poll_default_max_votes == 1
        assert not hasattr(settings, "extra_field")

class TestGameClass:
    """Tests for the Game class."""
    
    def test_init_creates_initial_scene(self):
        """Test that Game initialization creates an initial scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Check that an initial scene was created
        assert len(game.scenes) == 1
        assert game.current_scene is not None
        assert game.current_scene.title.startswith("Scene ")
        assert f"A new scene in {game.name}" in game.current_scene.description
        assert game.current_scene.is_active()
    
    def test_init_with_existing_scenes(self):
        """Test Game initialization with existing scenes."""
        # Create a scene first
        game1 = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Create a second game with the scene from the first game
        existing_scene = game1.current_scene
        
        game2 = Game(
            id="game2",
            name="Test Game 2",
            creator_id="user2",
            channel_id="channel2",
            scenes=[existing_scene],
            current_scene=existing_scene
        )
        
        # Check that no new scene was created
        assert len(game2.scenes) == 1
        assert game2.scenes[0] is existing_scene
        assert game2.current_scene is existing_scene
    
    def test_create_scene_with_active_scene_fails(self):
        """Test that creating a scene fails when there's already an active scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # The game already has an initial active scene
        assert len(game.scenes) == 1
        assert game.current_scene is not None
        assert game.current_scene.is_active()
        
        # Try to create another scene - should fail
        with pytest.raises(ValueError) as excinfo:
            game.create_scene(
                title="Another Scene",
                description="This should fail."
            )
        
        assert "Cannot create active scene when another active scene exists" in str(excinfo.value)
        assert len(game.scenes) == 1  # Still only the initial scene
    
    def test_create_scene_after_completing_current(self):
        """Test creating a scene after completing the current scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Complete the initial scene
        initial_scene = game.current_scene
        game.complete_current_scene()
        
        # Verify the scene is completed
        assert initial_scene.is_completed()
        
        # Now we should be able to create a new scene
        new_scene = game.create_scene(
            title="New Scene",
            description="This should work now."
        )
        
        # Verify the new scene was created and set as current
        assert len(game.scenes) == 2
        assert game.current_scene is new_scene
        assert new_scene.is_active()
    
    def test_complete_scene(self):
        """Test completing a scene by ID."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the initial scene ID
        scene_id = game.current_scene.id
        
        # Complete the scene
        result = game.complete_scene(scene_id)
        
        # Verify the result
        assert result is True
        assert game.current_scene.is_completed()
        assert not game.current_scene.is_active()
    
    def test_complete_nonexistent_scene(self):
        """Test completing a scene that doesn't exist."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Try to complete a non-existent scene
        with pytest.raises(ValueError) as excinfo:
            game.complete_scene("nonexistent")
        
        assert "Scene nonexistent not found" in str(excinfo.value)
    
    def test_complete_current_scene(self):
        """Test completing the current scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the initial scene
        initial_scene = game.current_scene
        
        # Complete the current scene
        result = game.complete_current_scene()
        
        # Verify the result
        assert result is True
        assert initial_scene.is_completed()
        assert not initial_scene.is_active()
    
    def test_complete_current_scene_with_no_current(self):
        """Test completing the current scene when there is no current scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Clear the current scene
        game.current_scene = None
        
        # Try to complete the current scene
        with pytest.raises(ValueError) as excinfo:
            game.complete_current_scene()
        
        assert "No current scene to complete" in str(excinfo.value)
    
    def test_create_scene_with_no_active_scenes(self):
        """Test creating a scene when there are no active scenes."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Complete the initial scene
        game.complete_current_scene()
        
        # Create a new scene
        new_scene = game.create_scene(
            title="New Scene",
            description="This should work."
        )
        
        # Verify the new scene was created and set as current
        assert len(game.scenes) == 2
        assert game.current_scene is new_scene
        assert new_scene.is_active()
    
    def test_get_active_scenes(self):
        """Test getting all active scenes."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Initially there should be one active scene
        active_scenes = game.get_active_scenes()
        assert len(active_scenes) == 1
        assert active_scenes[0] is game.current_scene
        
        # Complete the current scene
        game.complete_current_scene()
        
        # Now there should be no active scenes
        active_scenes = game.get_active_scenes()
        assert len(active_scenes) == 0
        
        # Create a new scene
        new_scene = game.create_scene(
            title="New Scene",
            description="This should work."
        )
        
        # Now there should be one active scene again
        active_scenes = game.get_active_scenes()
        assert len(active_scenes) == 1
        assert active_scenes[0] is new_scene
    
    def test_create_scene(self):
        """Test creating a scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Clear the initial scene for testing
        initial_scene = game.scenes[0]
        game.scenes = []
        game.current_scene = None
        
        # Create a new scene
        scene = game.create_scene(
            title="Test Scene",
            description="This is a test scene."
        )
        
        # Check the scene
        assert scene.title == "Test Scene"
        assert scene.description == "This is a test scene."
        assert scene.game is game
        assert scene in game.scenes
    
    def test_create_scene_with_defaults(self):
        """Test creating a scene with default values."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Clear the initial scene for testing
        game.scenes = []
        game.current_scene = None
        
        # Create a new scene with defaults
        scene = game.create_scene()
        
        # Check the scene
        assert scene.title.startswith("Scene ")
        assert f"A new scene in {game.name}" in scene.description
        assert scene.game is game
        assert scene in game.scenes
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            setting_info="A test setting"
        )
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert result["setting_info"] == "A test setting"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["members"] == ["user1"]
        assert len(result["scene_ids"]) == 1  # Initial scene
        assert result["current_scene_id"] == game.current_scene.id
        assert result["type"] == "Game"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "setting_info": "A test setting",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
            "members": ["user1", "user2"],
            "scene_ids": [],
            "current_scene_id": None,
            "type": "Game",
            "settings": {
                "scene_default_status": "active",
                "poll_default_timeout": 120
            }
        }
        
        game = Game.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.setting_info == "A test setting"
        assert game.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert game.updated_at == datetime.fromisoformat("2023-01-01T12:30:00")
        assert game.members == {"user1", "user2"}
        assert game.settings.poll_default_timeout == 120
        
        # Check that an initial scene was created since none were provided
        assert len(game.scenes) == 1
    
    def test_add_member(self):
        """Test adding a member."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        game.add_member("user2")
        
        assert "user2" in game.members
        assert len(game.members) == 2
    
    def test_add_existing_member(self):
        """Test adding a member who is already in the game."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        with pytest.raises(ValueError):
            game.add_member("user1")  # Creator is already a member
    
    def test_remove_member(self):
        """Test removing a member."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        game.add_member("user2")
        result = game.remove_member("user2")
        
        assert result is True
        assert "user2" not in game.members
        assert len(game.members) == 1  # Only creator left
    
    def test_remove_nonexistent_member(self):
        """Test removing a member who is not in the game."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        result = game.remove_member("user2")
        
        assert result is False
        assert len(game.members) == 1  # Only creator
    
    def test_is_member(self):
        """Test checking if a user is a member."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        assert game.is_member("user1") is True  # Creator is a member
        assert game.is_member("user2") is False
        
        game.add_member("user2")
        assert game.is_member("user2") is True
    
    def test_get_scene(self):
        """Test getting a scene by ID."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the initial scene
        scene_id = game.scenes[0].id
        scene = game.get_scene(scene_id)
        
        assert scene is not None
        assert scene.id == scene_id
        
        # Try to get a non-existent scene
        nonexistent_scene = game.get_scene("nonexistent")
        assert nonexistent_scene is None
    
    def test_remove_scene(self):
        """Test removing a scene."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Get the initial scene
        scene_id = game.scenes[0].id
        
        # Remove the scene
        result = game.remove_scene(scene_id)
        
        assert result is True
        assert len(game.scenes) == 0
        assert game.current_scene is None
    
    def test_remove_nonexistent_scene(self):
        """Test removing a scene that doesn't exist."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        result = game.remove_scene("nonexistent")
        
        assert result is False
        assert len(game.scenes) == 1  # Initial scene still there
    
    def test_set_nonexistent_scene(self):
        """Test setting a non-existent scene as current."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        result = game.set_current_scene("nonexistent")
        
        assert result is False
        # Current scene should still be the initial scene
        assert game.current_scene is game.scenes[0] 