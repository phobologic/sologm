"""Error classes for Solo RPG Helper."""


class SoloGMError(Exception):
    """Base exception for all Solo GM errors."""

    pass


class ConfigError(SoloGMError):
    """Errors related to configuration."""

    pass


class GameError(SoloGMError):
    """Errors related to game management."""

    pass


class ActError(SoloGMError):
    """Errors related to act management."""

    pass


class SceneError(SoloGMError):
    """Errors related to scene management."""

    pass


class EventError(SoloGMError):
    """Errors related to event tracking."""

    pass


class OracleError(SoloGMError):
    """Errors related to oracle interpretation."""

    pass


class DiceError(SoloGMError):
    """Errors related to dice rolling."""

    pass


class StorageError(SoloGMError):
    """Errors related to data storage."""

    pass


class APIError(SoloGMError):
    """Errors related to external API calls."""

    pass
