"""
Game-related exceptions.
"""
from typing import TYPE_CHECKING, Optional

from sologm.rpg_helper.models.base import ModelError

if TYPE_CHECKING:
    from .base import Game

class GameError(ModelError):
    """Base exception for game-related errors."""
    pass

class ChannelGameExistsError(GameError):
    """Exception raised when attempting to create a game in a channel that already has one."""
    def __init__(self, channel_id: str, existing_game: 'Game'):
        self.channel_id = channel_id
        self.existing_game = existing_game
        super().__init__(f"A game already exists in channel {channel_id}")

class SceneError(GameError):
    """Base exception for scene-related errors."""
    pass

class SceneNotFoundError(SceneError):
    """Exception raised when a scene cannot be found."""
    def __init__(self, scene_id: str, game_id: Optional[str] = None):
        self.scene_id = scene_id
        self.game_id = game_id
        message = f"Scene with ID {scene_id} not found"
        if game_id:
            message += f" in game {game_id}"
        super().__init__(message)

class InvalidSceneStateError(SceneError):
    """Exception raised when a scene is in an invalid state for an operation."""
    def __init__(self, scene_id: str, current_state: str, required_state: str):
        self.scene_id = scene_id
        self.current_state = current_state
        self.required_state = required_state
        super().__init__(
            f"Scene {scene_id} is in state {current_state}, but must be in state {required_state}"
        )

class SceneStateTransitionError(SceneError):
    """Exception raised when a scene state transition is invalid."""
    def __init__(self, scene_id: str, current_state: str, requested_state: str):
        self.scene_id = scene_id
        self.current_state = current_state
        self.requested_state = requested_state
        super().__init__(
            f"Scene {scene_id} cannot transition from {current_state} to {requested_state}"
        )

class PollError(GameError):
    """Base exception for poll-related errors."""
    pass

class PollNotFoundError(PollError):
    """Exception raised when a poll cannot be found."""
    def __init__(self, poll_id: str, game_id: Optional[str] = None):
        self.poll_id = poll_id
        self.game_id = game_id
        message = f"Poll with ID {poll_id} not found"
        if game_id:
            message += f" in game {game_id}"
        super().__init__(message)

class PollClosedError(PollError):
    """Exception raised when attempting to modify a closed poll."""
    def __init__(self, poll_id: str):
        self.poll_id = poll_id
        super().__init__(f"Poll {poll_id} is closed and cannot be modified")

class SettingError(GameError):
    """Base exception for setting-related errors."""
    pass

class SettingNotFoundError(SettingError):
    """Exception raised when a setting cannot be found."""
    def __init__(self, setting_name: str, game_id: str):
        self.setting_name = setting_name
        self.game_id = game_id
        super().__init__(f"Setting {setting_name} not found for game {game_id}") 