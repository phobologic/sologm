"""
Tests for the story logging functionality.
"""
import logging
import io
from unittest.mock import patch, MagicMock
from typing import Generator

import pytest

from sologm.rpg_helper.utils.logging import (
    get_logger, LogLevel, RPGLogger, LogFormatter,
    initialize_logging, set_global_log_level
)
from sologm.rpg_helper.utils.story_logging import (
    get_story_logger, setup_story_logging, StoryFormatter, DebugFormatter,
    StoryLogFormatter, STORY_LEVEL_ID
)

@pytest.fixture
def reset_logging() -> Generator[None, None, None]:
    """Reset logging configuration before each test."""
    # Store original handlers and level
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    original_level = root_logger.level
    
    # Clear all handlers from all loggers
    for logger in [logging.getLogger(name) for name in logging.root.manager.loggerDict]:
        logger.handlers.clear()
    root_logger.handlers.clear()
    
    yield
    
    # Restore original state
    root_logger.handlers = original_handlers
    root_logger.setLevel(original_level)

@pytest.fixture
def capture_logs(reset_logging) -> Generator[io.StringIO, None, None]:
    """Fixture to capture log output."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    
    # Create a formatter that will handle both story and debug messages
    class TestFormatter(logging.Formatter):
        def format(self, record):
            # Extract prefix from record if available
            if hasattr(record, 'prefix'):
                prefix = record.prefix
                prefix_str = StoryLogger.PREFIXES.get(prefix, StoryLogger.PREFIXES['System'])
                return f"{prefix_str} {record.getMessage()}"
            return record.getMessage()
    
    handler.setFormatter(TestFormatter())
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    
    def mock_init(self, name, **kwargs):
        """Mock initialization that properly sets up the logger."""
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(kwargs.get('level', logging.DEBUG))  # Default to DEBUG
        self.logger.propagate = True
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Add our capture handler
        self.logger.addHandler(handler)
    
    # Patch stdout and RPGLogger.__init__
    with patch('sys.stdout', new=io.StringIO()):
        with patch('sologm.rpg_helper.utils.logging.RPGLogger.__init__', mock_init):
            yield log_stream
    
    log_stream.close()

def test_story_level_registration(reset_logging):
    """Test that the STORY log level is properly registered."""
    # Register the story level
    setup_story_logging(debug_mode=False)
    
    assert STORY_LEVEL_ID == 25
    assert logging.getLevelName(STORY_LEVEL_ID) == 'STORY'
    # Note: logging.STORY is added dynamically, so we check the level name instead
    assert logging.getLevelName('STORY') == STORY_LEVEL_ID

def test_story_logger_methods(reset_logging, capture_logs):
    """Test StoryLogger logging methods."""
    # Initialize logging first
    setup_story_logging(debug_mode=True)  # Use debug mode to see all messages
    logger = get_story_logger("test_methods")
    
    # Ensure debug level is set
    logger.logger.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Test standard logging methods
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    logger.story("Story message", prefix="Game")
    
    log_output = capture_logs.getvalue()
    
    # Add debug info to error message
    debug_info = (f"\nLogger levels:"
                 f"\nRoot logger: {root_logger.level}"
                 f"\nLogger: {logger.logger.level}")
    
    for msg in ["Debug message", "Info message", "Warning message", 
                "Error message", "Critical message", "Story message"]:
        assert msg in log_output, f"Missing message: {msg}\nLog output was: {log_output}{debug_info}"
    assert "🎲 Game" in log_output, f"Missing prefix\nLog output was: {log_output}"

def test_story_formatter():
    """Test StoryFormatter functionality."""
    formatter = StoryFormatter()
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Story message",
        args=(),
        exc_info=None
    )
    setattr(record, 'prefix', "Scene")
    
    formatted = formatter.format(record)
    assert "Scene" in formatted
    assert "Story message" in formatted

def test_debug_formatter():
    """Test DebugFormatter functionality."""
    formatter = DebugFormatter()
    
    record = logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname="test_file.py",
        lineno=42,
        msg="Debug message",
        args=(),
        exc_info=None
    )
    setattr(record, 'prefix', "Scene")
    
    formatted = formatter.format(record)
    assert "Debug message" in formatted
    assert "Scene" in formatted
    assert "test_file.py:42" in formatted  # Check file and line number format

def test_story_log_formatter():
    """Test StoryLogFormatter factory class."""
    # Create formatters with format string
    story_fmt = StoryLogFormatter()
    
    # Test story mode formatter
    formatter = story_fmt.create_formatter(format_type="story")
    assert isinstance(formatter, StoryFormatter)
    
    # Test debug mode formatter
    formatter = story_fmt.create_formatter(format_type="debug")
    assert isinstance(formatter, DebugFormatter)
    
    # Test with is_debug parameter
    formatter = story_fmt.create_formatter(is_debug=True)
    assert isinstance(formatter, DebugFormatter)
    
    # Test default formatter - should fall back to story mode
    formatter = story_fmt.create_formatter()
    assert isinstance(formatter, StoryFormatter)

def test_setup_story_logging(reset_logging, capture_logs):
    """Test story logging setup in different modes."""
    # Test story mode
    setup_story_logging(debug_mode=False)
    logger = get_story_logger("test_setup")
    logger.logger.propagate = True  # Ensure propagation
    logger.story("Story message", prefix="Test")
    
    log_output = capture_logs.getvalue()
    assert "Story message" in log_output
    assert "🔧 Test" in log_output, f"Missing prefix. Log output was: {log_output}"  # Test uses System emoji

def test_story_mode_debug_filtering(reset_logging, capture_logs):
    """Test that debug messages are filtered in story mode."""
    setup_story_logging(debug_mode=False)
    logger = get_story_logger("test_filtering")
    logger.logger.propagate = True  # Ensure propagation
    
    logger.debug("Debug message")
    logger.story("Story message", prefix="Test")
    
    log_output = capture_logs.getvalue()
    assert "Story message" in log_output
    # In story mode, debug messages should be filtered
    assert "Debug message" not in log_output

def test_debug_mode_all_messages(reset_logging, capture_logs):
    """Test that all messages are shown in debug mode."""
    # Initialize core logging first
    initialize_logging(format_type="simple")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Set up story logging in debug mode
    setup_story_logging(debug_mode=True)
    logger = get_story_logger("test_debug_mode")
    logger.logger.propagate = True  # Ensure propagation
    logger.logger.setLevel(logging.DEBUG)  # Explicitly set debug level
    
    # Test messages
    logger.debug("Debug message")
    logger.story("Story message", prefix="Test")
    
    log_output = capture_logs.getvalue()
    debug_info = (f"\nLogger levels:"
                 f"\nRoot logger: {root_logger.level}"
                 f"\nLogger: {logger.logger.level}")
    
    assert "Debug message" in log_output, f"Log output was: {log_output}{debug_info}"
    assert "Story message" in log_output, f"Log output was: {log_output}{debug_info}"

def test_integration_with_core_logging(reset_logging, capture_logs):
    """Test integration between core and story logging."""
    # Initialize both logging systems
    initialize_logging(format_type="simple")
    setup_story_logging(debug_mode=True)  # Use debug mode to see all messages
    
    # Ensure root logger has our capture handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    core_logger = get_logger("test_core")
    story_logger = get_story_logger("test_story")
    
    # Ensure loggers use the root logger's handlers
    core_logger.logger.handlers = []
    story_logger.logger.handlers = []
    core_logger.logger.propagate = True
    story_logger.logger.propagate = True
    
    core_logger.info("Core info message")
    story_logger.story("Story message", prefix="Test")
    
    log_output = capture_logs.getvalue()
    assert "Core info message" in log_output, f"Log output was: {log_output}"
    assert "Story message" in log_output, f"Log output was: {log_output}"

def test_global_level_propagation(reset_logging):
    """Test that global log level changes affect both logging systems."""
    # Initialize both logging systems
    initialize_logging(format_type="simple")
    setup_story_logging(debug_mode=True)
    
    core_logger = get_logger("test_level_core")
    story_logger = get_story_logger("test_level_story")
    
    # Set global level to WARNING
    set_global_log_level(LogLevel.WARNING)
    
    # Compare against the integer value directly
    assert core_logger.logger.level == logging.WARNING
    # Story logger should maintain its STORY level
    assert story_logger.logger.level == STORY_LEVEL_ID

def test_formatter_inheritance():
    """Test that story formatters properly extend core formatters."""
    # Test inheritance
    assert issubclass(StoryFormatter, logging.Formatter)
    assert issubclass(DebugFormatter, logging.Formatter)
    
    # Test creation without passing debug_mode to base formatter
    story_fmt = StoryLogFormatter()
    
    # Create formatters directly
    story_formatter = StoryFormatter()
    debug_formatter = DebugFormatter()
    
    assert isinstance(story_formatter, logging.Formatter)
    assert isinstance(debug_formatter, logging.Formatter)

def test_mixed_logging_modes(reset_logging, capture_logs):
    """Test using different logging modes with both systems."""
    # Initialize core logging first with DEBUG level
    initialize_logging(format_type="simple")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create and test core logger
    core_logger = get_logger("test_mixed_core")
    core_logger.logger.handlers = []
    core_logger.logger.propagate = True
    core_logger.logger.setLevel(logging.DEBUG)
    
    # Now set up story logging
    setup_story_logging(debug_mode=True)
    story_logger = get_story_logger("test_mixed_story")
    story_logger.logger.handlers = []
    story_logger.logger.propagate = True
    story_logger.logger.setLevel(logging.DEBUG)
    
    # Test both loggers
    core_logger.debug("Core debug")
    story_logger.debug("Story debug")
    story_logger.story("Story message", prefix="Test")
    
    # Get and check log output
    log_output = capture_logs.getvalue()
    
    # Add debug output to error message
    debug_info = (f"\nLogger levels:"
                 f"\nRoot logger: {root_logger.level}"
                 f"\nCore logger: {core_logger.logger.level}"
                 f"\nStory logger: {story_logger.logger.level}")
    
    # Verify all messages appear
    assert "Core debug" in log_output, f"Log output was: {log_output}{debug_info}"
    assert "Story debug" in log_output, f"Log output was: {log_output}{debug_info}"
    assert "Story message" in log_output, f"Log output was: {log_output}{debug_info}"

def test_error_handling_integration(reset_logging, capture_logs):
    """Test error handling across both logging systems."""
    # Initialize core logging first
    initialize_logging(format_type="simple")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all messages
    
    # Create loggers
    core_logger = get_logger("test_error_core")
    core_logger.logger.propagate = True  # Ensure propagation
    core_logger.logger.setLevel(logging.ERROR)
    
    # Set up story logging
    setup_story_logging(debug_mode=True)
    story_logger = get_story_logger("test_error_story")
    story_logger.logger.propagate = True  # Ensure propagation
    story_logger.logger.setLevel(logging.ERROR)
    
    # Test error logging
    core_logger.error("Core error")
    story_logger.error("Story error")
    
    # Get and check log output
    log_output = capture_logs.getvalue()
    
    # Add debug output to error message
    debug_info = (f"\nLogger levels:"
                 f"\nRoot logger: {root_logger.level}"
                 f"\nCore logger: {core_logger.logger.level}"
                 f"\nStory logger: {story_logger.logger.level}")
    
    # Verify error messages appear
    assert "Core error" in log_output, f"Log output was: {log_output}{debug_info}"
    assert "Story error" in log_output, f"Log output was: {log_output}{debug_info}"
    
    # Test error logging with exception info
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        # Use error() with exc_info=True and include the exception
        core_logger.error("Core error with exception", exc_info=True)
        story_logger.error("Story error with exception", exc_info=True)
        
        # Get updated log output and verify exception details
        log_output = capture_logs.getvalue()
        assert "Core error with exception" in log_output
        assert "Story error with exception" in log_output
        assert str(e) in log_output  # Check for exception message
        assert "Traceback" in log_output  # Check for traceback 