"""
Tests for the MythicGMEGame class.
"""
import pytest
from datetime import datetime

from sologm.rpg_helper.models.game.mythic import MythicGMEGame

class TestMythicGMEGameClass:
    """Tests for the MythicGMEGame class."""
    
    def test_init(self):
        """Test MythicGMEGame initialization."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        assert game.id == "game1"
        assert game.name == "Test Mythic Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert isinstance(game.created_at, datetime)
        assert isinstance(game.updated_at, datetime)
        assert game.members == {"user1"}  # Creator is a member
        assert game.scenes == []
        assert game.current_scene is None
        
        # Check Mythic-specific attributes
        assert game.chaos_factor == 5
        assert game.settings.mythic_chaos_factor == 5
    
    def test_to_dict(self):
        """Test conversion to dictionary for MythicGMEGame."""
        game = MythicGMEGame(
            id="game1",
            name="Test Mythic Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        result = game.to_dict()
        
        assert result["id"] == "game1"
        assert result["name"] == "Test Mythic Game"
        assert result["creator_id"] == "user1"
        assert result["channel_id"] == "channel1"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["members"] == ["user1"]  # Creator is a member
        assert result["scene_ids"] == []
        assert result["current_scene_id"] is None
        assert result["type"] == "MythicGMEGame"
        assert result["settings"]["mythic_chaos_factor"] == 5
    
    def test_from_dict(self):
        """Test creation from dictionary for MythicGMEGame."""
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
            "type": "MythicGMEGame",
            "settings": {
                "mythic_chaos_factor": 7
            }
        }
        
        game = MythicGMEGame.from_dict(data)
        
        assert game.id == "game1"
        assert game.name == "Test Mythic Game"
        assert game.creator_id == "user1"
        assert game.channel_id == "channel1"
        assert game.members == {"user1", "user2"}
        assert game.scenes == []
        assert game.current_scene is None
        assert game.chaos_factor == 7
        assert game.settings.mythic_chaos_factor == 7 