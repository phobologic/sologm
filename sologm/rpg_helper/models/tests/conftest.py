"""
Configuration for pytest.
"""
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "game: tests for the Game class"
    )
    config.addinivalue_line(
        "markers", "mythic: tests for the MythicGMEGame class"
    )
    config.addinivalue_line(
        "markers", "functions: tests for game-related functions"
    )
    config.addinivalue_line(
        "markers",
        "poll: mark test as a poll-related test"
    )