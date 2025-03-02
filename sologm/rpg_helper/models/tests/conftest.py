"""
Configuration for pytest.
"""
import pytest
from unittest.mock import patch, MagicMock


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
    config.addinivalue_line(
        "markers",
        "scene: mark test as a scene-related test"
    )


# Mock Timer globally for all tests to prevent hanging
@pytest.fixture(autouse=True, scope="session")
def mock_timer_globally():
    """
    Mock the Timer class globally for all tests to prevent hanging.
    """
    # First, patch the direct import in poll.py
    with patch('sologm.rpg_helper.models.poll.Timer') as mock_timer:
        # Create a mock timer instance that does nothing when started
        timer_instance = MagicMock()
        mock_timer.return_value = timer_instance
        
        # Make sure the timer doesn't actually run
        timer_instance.start = MagicMock()
        timer_instance.cancel = MagicMock()
        
        yield mock_timer


# Add a fixture to clean up any real timers that might have been created
@pytest.fixture(autouse=True, scope="function")
def cleanup_timers():
    """Clean up any timers that might have been created during tests."""
    yield
    
    # After each test, try to clean up any timers
    # This is a safety measure in case our mocking didn't catch everything
    import threading
    for thread in threading.enumerate():
        if isinstance(thread, threading.Timer):
            thread.cancel()