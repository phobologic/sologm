"""
Game-related exceptions.
"""
from typing import TYPE_CHECKING, Optional

from sologm.rpg_helper.models2.base import ModelError

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

class InvalidSceneStatusError(SceneError):
    """Exception raised when attempting to perform an operation on a scene with an invalid status."""
    def __init__(self, scene_id: str, current_status: str, required_status: str):
        self.scene_id = scene_id
        self.current_status = current_status
        self.required_status = required_status
        super().__init__(
            f"Scene {scene_id} has status {current_status}, but {required_status} is required"
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