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
        assert result["scene_allow_multiple_active"] is False
        assert result["poll_default_timeout"] == 120
        assert result["poll_default_option_count"] == 5
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "scene_default_status": "inactive",
            "poll_default_timeout": 120,
            "unknown_field": "value"  # Should be ignored
        }
        
        settings = GameSettings.from_dict(data)
        
        assert settings.scene_default_status == "inactive"
        assert settings.scene_allow_multiple_active is False
        assert settings.poll_default_timeout == 120
        assert settings.poll_default_option_count == 5
        assert not hasattr(settings, "unknown_field")


class TestGameClass:
    """Tests for the Game class."""
    
    def test_init(self):
        """Test Game initialization."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert isinstance(game.created_at, datetime)
        assert isinstance(game.updated_at, datetime)
        # Creator is now automatically added as a member
        assert game.members == {"user1"}
        assert game.scenes == []
        assert game.current_scene is None
    
    def test_add_member(self):
        """Test adding a member to a game."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Creator is already a member, so add a different user
        game.add_member("user2")
        assert "user2" in game.members
        assert len(game.members) == 2  # Creator + new member
    
    def test_add_member_already_exists(self):
        """Test adding a member that already exists."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Try to add the creator again (who is already a member)
        with pytest.raises(ValueError) as excinfo:
            game.add_member("user1")
        
        assert "is already a member" in str(excinfo.value)
    
    def test_remove_member(self):
        """Test removing a member from a game."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Add a member first
        game.add_member("user2")
        assert "user2" in game.members
        
        # Now remove them
        result = game.remove_member("user2")
        assert result is True
        assert "user2" not in game.members
    
    def test_remove_member_not_found(self):
        """Test removing a member that doesn't exist."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Try to remove a non-existent member
        result = game.remove_member("user3")
        assert result is False
    
    def test_remove_creator(self):
        """Test that removing the creator raises an error."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Try to remove the creator
        with pytest.raises(ValueError) as excinfo:
            game.remove_member("user1")
        
        assert "Cannot remove the game creator" in str(excinfo.value)
    
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
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1",
            setting_info="Fantasy world"
        )
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert result["setting_info"] == "Fantasy world"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["members"] == ["user1"]  # Creator is a member
        assert result["scene_ids"] == []
        assert result["current_scene_id"] is None
        assert result["type"] == "Game"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "game1",
            "name": "Test Game",
            "creator_id": "user1",
            "channel_id": "channel1",
            "setting_info": "Fantasy world",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
            "members": ["user1", "user2"],
            "scene_ids": [],
            "current_scene_id": None,
            "type": "Game",
            "settings": {
                "poll_default_timeout": 120
            }
        }
        
        game = Game.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.setting_info == "Fantasy world"
        assert game.created_at.isoformat() == "2023-01-01T12:00:00"
        assert game.updated_at.isoformat() == "2023-01-01T12:30:00"
        assert game.members == {"user1", "user2"}
        assert game.scenes == []
        assert game.current_scene is None
        assert game.settings.poll_default_timeout == 120 