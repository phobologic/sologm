"""
Tests for the MythicGMEGame class.
"""
import pytest
from datetime import datetime

from sologm.rpg_helper.models.game.mythic import MythicGMEGame
from sologm.rpg_helper.models.scene import Scene, SceneStatus

class TestMythicGMEGameClass:
    """Tests for the MythicGMEGame class."""
    
    def test_init(self):
        """Test MythicGMEGame initialization."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1",
            chaos_factor=6
        )
        
        # Check basic attributes
        assert game.id == "game1"
        assert game.name == "Test Mythic Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        
        # Check Mythic-specific attributes
        assert game.chaos_factor == 6
        
        # Check that an initial scene was created
        assert len(game.scenes) == 1
        assert game.current_scene is not None
        assert game.current_scene.is_active()
    
    def test_init_with_default_chaos(self):
        """Test MythicGMEGame initialization with default chaos factor."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Check that the default chaos factor was used
        assert game.chaos_factor == 5
    
    def test_init_with_existing_scenes(self):
        """Test MythicGMEGame initialization with existing scenes."""
        # Create a scene first
        game1 = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Create a second game with the scene from the first game
        existing_scene = game1.current_scene
        
        game2 = MythicGMEGame(
            id="game2",
            name="Test Mythic Game 2",
            creator_id="user2",
            channel_id="channel2",
            scenes=[existing_scene],
            current_scene=existing_scene
        )
        
        # Check that no new scene was created
        assert len(game2.scenes) == 1
        assert game2.scenes[0] is existing_scene
        assert game2.current_scene is existing_scene
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1",
            chaos_factor=7
        )
        
        result = game.to_dict()
        
        # Check basic fields
        assert result["id"] == "game1"
        assert result["name"] == "Test Mythic Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["members"] == ["user1"]
        assert len(result["scene_ids"]) == 1  # Initial scene
        assert result["current_scene_id"] == game.current_scene.id
        assert result["type"] == "MythicGMEGame"
        
        # Check Mythic-specific fields
        assert result["chaos_factor"] == 7
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "game1",
            "name": "Test Mythic Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
            "members": ["user1", "user2"],
            "scene_ids": [],
            "current_scene_id": None,
            "chaos_factor": 7
        }
        
        game = MythicGMEGame.from_dict(data)
        
        # Check basic fields
        assert game.id == "game1"
        assert game.name == "Test Mythic Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.created_at == datetime.fromisoformat("2023-01-01T12:00:00")
        assert game.updated_at == datetime.fromisoformat("2023-01-01T12:30:00")
        assert game.members == {"user1", "user2"}
        
        # Check Mythic-specific fields
        assert game.chaos_factor == 7
        
        # Check that an initial scene was created since none were provided
        assert len(game.scenes) == 1
        assert game.current_scene is not None
    
    def test_from_dict_default_chaos(self):
        """Test creation from dictionary without chaos factor."""
        data = {
            "id": "game1",
            "name": "Test Mythic Game",
            "creator_id": "user1",
            "channel_id": "channel1",
        }
        
        game = MythicGMEGame.from_dict(data)
        
        assert game.chaos_factor == 5  # Default value
    
    def test_create_scene_with_active_scene_fails(self):
        """Test that creating a scene fails when there's already an active scene."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
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
        
        assert "Cannot create new scene while current scene is active" in str(excinfo.value)
        assert len(game.scenes) == 1  # Still only the initial scene
    
    def test_create_scene_after_completing_current(self):
        """Test creating a scene after completing the current scene."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
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
    
    def test_increase_chaos(self):
        """Test increasing the chaos factor."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1",
            chaos_factor=5
        )
        
        # Test normal increase
        result = game.increase_chaos()
        assert result == 6
        assert game.chaos_factor == 6
        
        # Test upper limit
        game.chaos_factor = 9
        with pytest.raises(ValueError) as excinfo:
            game.increase_chaos()
        assert "Chaos factor cannot be greater than 9" in str(excinfo.value)
        assert game.chaos_factor == 9  # Should not change
    
    def test_decrease_chaos(self):
        """Test decreasing the chaos factor."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1",
            chaos_factor=5
        )
        
        # Test normal decrease
        result = game.decrease_chaos()
        assert result == 4
        assert game.chaos_factor == 4
        
        # Test lower limit
        game.chaos_factor = 1
        with pytest.raises(ValueError) as excinfo:
            game.decrease_chaos()
        assert "Chaos factor cannot be less than 1" in str(excinfo.value)
        assert game.chaos_factor == 1  # Should not change
    
    def test_set_chaos(self):
        """Test setting the chaos factor."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Test valid values
        result = game.set_chaos(8)
        assert result == 8
        assert game.chaos_factor == 8
        
        # Test lower limit
        with pytest.raises(ValueError) as excinfo:
            game.set_chaos(0)
        assert "Chaos factor cannot be less than or equal to 0" in str(excinfo.value)
        assert game.chaos_factor == 8  # Should not change
        
        # Test upper limit
        with pytest.raises(ValueError) as excinfo:
            game.set_chaos(10)
        assert "Chaos factor cannot be greater than 9" in str(excinfo.value)
        assert game.chaos_factor == 8  # Should not change