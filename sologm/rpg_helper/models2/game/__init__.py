"""
Game models package.
"""
# Import models for easier access
from .settings import GameSetting
from .errors import (
    GameError, ChannelGameExistsError,
    SceneError, SceneNotFoundError, InvalidSceneStatusError,
    PollError, PollNotFoundError, PollClosedError,
    SettingError, SettingNotFoundError
)
from .base import Game, GameType
from .mythic import MythicGame, MythicChaosFactor, ChaosBoundaryError

# Import methods to add them to the Game class
import sologm.rpg_helper.models2.game.methods

# Import Mythic GME features
import sologm.rpg_helper.models2.game.mythic_features

__all__ = [
    'GameSetting',
    'GameError',
    'ChannelGameExistsError',
    'SceneError',
    'SceneNotFoundError',
    'InvalidSceneStatusError',
    'PollError',
    'PollNotFoundError',
    'PollClosedError',
    'SettingError',
    'SettingNotFoundError',
    'Game',
    'GameType',
    'MythicGame',
    'MythicChaosFactor',
    'ChaosBoundaryError'
] 