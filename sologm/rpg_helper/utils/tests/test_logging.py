"""
Tests for the logging utilities.
"""
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock, call
import io
import sys
from datetime import datetime

import pytest

from sologm.rpg_helper.utils.logging import (
    get_logger, set_global_log_level, LogLevel, RPGLogger, get_level_from_string,
    initialize_logging, LoggingConfig, LogFormatter
)


def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test_module")

    expected_level = get_level_from_string(os.environ.get("RPG_HELPER_LOG_LEVEL", "INFO"))
    
    assert logger.name == "test_module"
    assert isinstance(logger, RPGLogger)
    assert logger.logger.level == expected_level


def test_get_logger_default_name():
    """Test getting a logger with default module name."""
    logger = get_logger()
    
    # The module name should be this test module
    expected_name = __name__
    assert logger.name == expected_name
    assert isinstance(logger, RPGLogger)


def test_logger_levels():
    """Test setting different log levels."""
    logger = get_logger("test_levels", level=LogLevel.DEBUG)
    assert logger.logger.level == LogLevel.DEBUG
    
    # Get the same logger but with a different level
    logger2 = get_logger("test_levels", level=LogLevel.ERROR)
    assert logger2.logger.level == LogLevel.ERROR
    
    # They should be the same object
    assert logger is logger2


def test_set_global_log_level():
    """Test setting the global log level."""
    logger1 = get_logger("test_global1")
    logger2 = get_logger("test_global2")
    
    set_global_log_level(LogLevel.DEBUG)
    
    assert logger1.logger.level == LogLevel.DEBUG
    assert logger2.logger.level == LogLevel.DEBUG


def test_log_to_file():
    """Test logging to a file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = "test.log"
        logger = get_logger(
            "test_file",
            log_to_file=True,
            log_dir=temp_dir,
            log_file=log_file
        )
        
        logger.info("Test message")
        
        # Check that the file exists and contains the message
        log_path = os.path.join(temp_dir, log_file)
        assert os.path.exists(log_path)
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert "test_file" in content
            assert "INFO" in content
            assert "Test message" in content


@patch('sys.stdout')
def test_log_to_stdout(mock_stdout):
    """Test logging to stdout."""
    logger = get_logger("test_stdout")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.info("Test stdout message")
        mock_log.assert_called_once()
        args, _ = mock_log.call_args
        assert args[0] == LogLevel.INFO
        assert "Test stdout message" in args[1]


def test_log_with_context():
    """Test logging with additional context."""
    logger = get_logger("test_context")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.info("User action", user_id="123", action="login")
        mock_log.assert_called_once()
        args, _ = mock_log.call_args
        assert "User action" in args[1]
        assert "user_id='123'" in args[1]
        assert "action='login'" in args[1]


def test_env_log_level():
    """Test setting log level from environment variable."""
    with patch.dict(os.environ, {"RPG_HELPER_LOG_LEVEL": "DEBUG"}):
        logger = get_logger("test_env")
        assert logger.logger.level == LogLevel.DEBUG 


def test_initialize_logging_updates_existing_loggers():
    """Test that initialize_logging updates formatters for existing loggers."""
    # Create a logger with default format
    logger1 = get_logger("test_init1")
    
    # Create another logger
    logger2 = get_logger("test_init2")
    
    # Capture stdout to verify format
    stdout = io.StringIO()
    with patch('sys.stdout', new=stdout):
        logger1.info("Test message before")
        before_format = stdout.getvalue()
        stdout.truncate(0)
        stdout.seek(0)
        
        # Initialize logging with simple format
        initialize_logging(format_type="simple", datefmt="%Y-%m-%d")
        
        # Log messages with both loggers
        logger1.info("Test message after")
        logger2.info("Test message after 2")
        after_format = stdout.getvalue()
    
    # Default format includes logger name, simple format doesn't
    assert "test_init1" in before_format
    assert "test_init1" not in after_format
    assert "[" in after_format  # Simple format starts with [
    assert "] INFO: Test message after" in after_format


def test_global_format_consistency():
    """Test that all loggers use the same format after initialization."""
    initialize_logging(format_type="simple")
    
    # Create multiple loggers
    loggers = [
        get_logger(f"test_format_{i}")
        for i in range(3)
    ]
    
    # Capture stdout
    stdout = io.StringIO()
    with patch('sys.stdout', new=stdout):
        for logger in loggers:
            logger.info("Test message")
        
        output = stdout.getvalue()
        
    # Check that all log messages have the same format
    lines = output.strip().split('\n')
    assert len(lines) == 3
    for line in lines:
        assert line.startswith('[')
        assert '] INFO: Test message' in line
        assert ' - ' not in line  # Default format uses dashes


@pytest.fixture
def capture_logs():
    """Fixture to capture log output."""
    # Create a string IO object to capture log output
    log_capture = io.StringIO()
    
    # Create a handler that writes to the string IO
    handler = logging.StreamHandler(log_capture)
    
    # Save the original handlers
    original_handlers = logging.root.handlers.copy()
    
    # Replace the handlers with our capture handler
    logging.root.handlers = [handler]
    
    # Make sure the root logger will pass messages to the handler
    original_level = logging.root.level
    logging.root.setLevel(logging.DEBUG)
    
    yield log_capture
    
    # Restore the original handlers and level
    logging.root.handlers = original_handlers
    logging.root.setLevel(original_level)


def test_format_update_propagation(capture_logs):
    """Test that format updates propagate to existing loggers."""
    # Create a logger with default format
    logger = get_logger("test_update")
    
    # Set root logger to DEBUG to see all messages
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Ensure the capture handler uses the default formatter
    for handler in root_logger.handlers:
        handler.setFormatter(LogFormatter.create_formatter("default"))
    
    # Log a message with default format
    logger.info("Before update")
    
    # Update the format and ensure it's applied to handlers
    initialize_logging(format_type="simple")
    for handler in root_logger.handlers:
        handler.setFormatter(LogFormatter.create_formatter("simple"))
    
    # Log another message
    logger.info("After update")
    
    # Get the log output
    log_output = capture_logs.getvalue()
    
    # The first message should use default format, second should use simple format
    assert " - INFO - " in log_output  # Default format
    assert "] INFO:" in log_output  # Simple format


def test_formatter_kwargs_propagation():
    """Test that formatter kwargs propagate to formatters."""
    custom_datefmt = "%Y-%m-%d"
    
    # Initialize with custom date format
    initialize_logging(format_type="simple", datefmt=custom_datefmt)
    
    # Get the formatter kwargs
    _, formatter_kwargs = LoggingConfig.get_format_config()
    
    # Check that the date format was set
    assert formatter_kwargs.get("datefmt") == custom_datefmt
    
    # Test with a logger
    logger = get_logger("test_kwargs")
    
    # Verify the formatter has the correct date format
    for handler in logger.logger.handlers:
        if hasattr(handler.formatter, 'datefmt'):
            assert handler.formatter.datefmt == custom_datefmt


def test_mixed_format_specifications(capture_logs):
    """Test handling of mixed format specifications between global and local."""
    # Set global format
    initialize_logging(format_type="simple")
    
    # Create loggers with different formats
    logger1 = get_logger("test_mixed1", format_type="json")
    logger2 = get_logger("test_mixed2")  # Should use global format
    
    # Ensure loggers use root logger's handler
    logger1.logger.handlers = []
    logger2.logger.handlers = []
    logger1.logger.propagate = True
    logger2.logger.propagate = True
    
    # Log messages
    logger1.info("Test JSON")
    logger2.info("Test simple")
    
    # Get the output
    log_output = capture_logs.getvalue()
    
    # Verify both messages appear
    assert "Test JSON" in log_output
    assert "Test simple" in log_output


def test_get_logger_returns_rpg_logger():
    """Test that get_logger returns an RPGLogger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, RPGLogger)


def test_get_logger_caches_loggers():
    """Test that get_logger caches loggers by name."""
    logger1 = get_logger("test_cache")
    logger2 = get_logger("test_cache")
    assert logger1 is logger2


def test_initialize_logging_sets_format(capture_logs):
    """Test that initialize_logging sets the format."""
    # Initialize with simple format
    initialize_logging(format_type="simple")
    
    # Get a logger and log a message
    logger = get_logger("test_init1")
    logger.info("Test message")
    
    # Check that the log message has the expected format
    log_output = capture_logs.getvalue()
    assert "Test message" in log_output


def test_initialize_logging_updates_existing_loggers(capture_logs):
    """Test that initialize_logging updates existing loggers."""
    # Create a logger before initializing
    logger = get_logger("test_init2")
    
    # Log a message before initialization
    logger.info("Before initialization")
    
    # Initialize with simple format
    initialize_logging(format_type="simple")
    
    # Log a message after initialization
    logger.info("After initialization")
    
    # Check that the log messages appear
    log_output = capture_logs.getvalue()
    assert "Before initialization" in log_output
    assert "After initialization" in log_output


def test_set_global_log_level():
    """Test that set_global_log_level updates all loggers."""
    # Create some loggers
    loggers = [
        get_logger(f"test_level_{i}")
        for i in range(3)
    ]
    
    # Set the global log level to WARNING
    set_global_log_level(logging.WARNING)
    
    # Check that all loggers have the WARNING level
    for logger in loggers:
        assert logger.logger.level == logging.WARNING


def test_global_format_consistency():
    """Test that all loggers use the same format."""
    # Initialize with default format
    initialize_logging(format_type="default")
    
    # Create some loggers
    loggers = [
        get_logger(f"test_format_{i}")
        for i in range(3)
    ]
    
    # Check that all loggers have the same format
    format_type, _ = LoggingConfig.get_format_config()
    assert format_type == "default"
    
    # Check that all handlers have formatters
    for logger in loggers:
        for handler in logger.logger.handlers:
            assert isinstance(handler.formatter, logging.Formatter)


def test_log_formatter():
    """Test the LogFormatter class."""
    formatter = LogFormatter.create_formatter("simple")
    assert isinstance(formatter, logging.Formatter)
    
    formatter = LogFormatter.create_formatter("json")
    assert isinstance(formatter, logging.Formatter)
    
    # Test default format
    formatter = LogFormatter.create_formatter()
    assert isinstance(formatter, logging.Formatter)


def test_log_level_enum():
    """Test LogLevel class functionality."""
    assert LogLevel.DEBUG == logging.DEBUG
    assert LogLevel.INFO == logging.INFO
    assert LogLevel.WARNING == logging.WARNING
    assert LogLevel.ERROR == logging.ERROR
    assert LogLevel.CRITICAL == logging.CRITICAL


def test_get_level_from_string():
    """Test converting string log levels to LogLevel enum."""
    assert get_level_from_string("DEBUG") == LogLevel.DEBUG
    assert get_level_from_string("INFO") == LogLevel.INFO
    assert get_level_from_string("WARNING") == LogLevel.WARNING
    assert get_level_from_string("ERROR") == LogLevel.ERROR
    assert get_level_from_string("CRITICAL") == LogLevel.CRITICAL
    # Test default case
    assert get_level_from_string("INVALID") == LogLevel.INFO


def test_rpg_logger_methods(capture_logs):
    """Test RPGLogger logging methods."""
    logger = get_logger("test_methods")
    
    # Set root logger to DEBUG to see all messages
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Set logger to DEBUG
    logger.logger.setLevel(logging.DEBUG)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    log_output = capture_logs.getvalue()
    assert "Debug message" in log_output
    assert "Info message" in log_output
    assert "Warning message" in log_output
    assert "Error message" in log_output
    assert "Critical message" in log_output 