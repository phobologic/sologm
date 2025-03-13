"""
Tests for game error classes.
"""
import pytest
from unittest.mock import MagicMock

from sologm.rpg_helper.models.game.errors import (
    GameError, ChannelGameExistsError, SceneNotFoundError,
    PollNotFoundError, PollClosedError, SceneError,
    InvalidSceneStateError, SceneStateTransitionError
)


class TestGameError:
    """Tests for the base GameError class."""
    
    def test_inheritance(self):
        """Test that GameError inherits from Exception."""
        assert issubclass(GameError, Exception)
    
    def test_init(self):
        """Test initialization with a message."""
        message = "Test error message"
        error = GameError(message)
        
        assert str(error) == message


class TestSceneError:
    """Tests for the base SceneError class."""
    
    def test_inheritance(self):
        """Test that SceneError inherits from GameError."""
        assert issubclass(SceneError, GameError)
    
    def test_init(self):
        """Test initialization with a message."""
        message = "Test scene error message"
        error = SceneError(message)
        
        assert str(error) == message


class TestChannelGameExistsError:
    """Tests for the ChannelGameExistsError class."""
    
    def test_inheritance(self):
        """Test that ChannelGameExistsError inherits from GameError."""
        assert issubclass(ChannelGameExistsError, GameError)
    
    def test_init(self):
        """Test initialization with channel ID and existing game."""
        channel_id = "test-channel-id"
        existing_game = MagicMock()
        existing_game.id = "test-game-id"
        
        error = ChannelGameExistsError(channel_id, existing_game)
        
        assert error.channel_id == channel_id
        assert error.existing_game == existing_game
        assert channel_id in str(error)
        assert "already exists in channel" in str(error)


class TestSceneNotFoundError:
    """Tests for the SceneNotFoundError class."""
    
    def test_inheritance(self):
        """Test that SceneNotFoundError inherits from GameError."""
        assert issubclass(SceneNotFoundError, GameError)
    
    def test_init_with_scene_id(self):
        """Test initialization with scene ID."""
        scene_id = "test-scene-id"
        game_id = "test-game-id"
        
        error = SceneNotFoundError(scene_id=scene_id, game_id=game_id)
        
        assert error.scene_id == scene_id
        assert error.game_id == game_id
        assert scene_id in str(error)
        assert game_id in str(error)
    

class TestInvalidSceneStateError:
    """Tests for the InvalidSceneStateError class."""
    
    def test_inheritance(self):
        """Test that InvalidSceneStateError inherits from SceneError."""
        assert issubclass(InvalidSceneStateError, SceneError)
    
    def test_init(self):
        """Test initialization with scene ID, current state, and required state."""
        scene_id = "test-scene-id"
        current_state = "COMPLETED"
        required_state = "ACTIVE"
        
        error = InvalidSceneStateError(
            scene_id=scene_id,
            current_state=current_state,
            required_state=required_state
        )
        
        assert error.scene_id == scene_id
        assert error.current_state == current_state
        assert error.required_state == required_state
        assert scene_id in str(error)
        assert current_state in str(error)
        assert required_state in str(error)
        assert "must be in state" in str(error)


class TestSceneStateTransitionError:
    """Tests for the SceneStateTransitionError class."""
    
    def test_inheritance(self):
        """Test that SceneStateTransitionError inherits from SceneError."""
        assert issubclass(SceneStateTransitionError, SceneError)
    
    def test_init(self):
        """Test initialization with scene ID, current state, and requested state."""
        scene_id = "test-scene-id"
        current_state = "COMPLETED"
        requested_state = "ACTIVE"
        
        error = SceneStateTransitionError(
            scene_id=scene_id,
            current_state=current_state,
            requested_state=requested_state
        )
        
        assert error.scene_id == scene_id
        assert error.current_state == current_state
        assert error.requested_state == requested_state
        assert scene_id in str(error)
        assert current_state in str(error)
        assert requested_state in str(error)
        assert "cannot transition from" in str(error)