"""
Tests for the logging utilities.
"""
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock

import pytest

from sologm.rpg_helper.utils.logging import (
    get_logger, set_global_log_level, LogLevel, RPGLogger
)


def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test_module")
    
    assert logger.name == "test_module"
    assert isinstance(logger, RPGLogger)
    assert logger.logger.level == LogLevel.INFO


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