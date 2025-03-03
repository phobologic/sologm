"""
Logging utilities for the RPG Helper application.
"""
import logging
import os
import sys
import inspect
from datetime import datetime
from typing import Optional, Union, Dict, Any


# Define log levels
class LogLevel:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

def get_level_from_string(level_str: str) -> LogLevel:
    """
    Get a log level from a string.
    """
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL
    }

    return level_map.get(level_str.upper(), LogLevel.INFO)


class RPGLogger:
    """
    Logger for the RPG Helper application.
    
    Provides structured logging with different log levels and output options.
    """
    
    def __init__(self, 
                name: str, 
                level: int = LogLevel.INFO,
                log_to_stdout: bool = True,
                log_to_file: bool = False,
                log_dir: str = "logs",
                log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name (usually module name)
            level: Minimum log level to record
            log_to_stdout: Whether to log to stdout
            log_to_file: Whether to log to a file
            log_dir: Directory for log files
            log_file: Specific log file name (defaults to name-YYYY-MM-DD.log)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Don't propagate to parent loggers
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Add stdout handler if requested
        if log_to_stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if requested
        if log_to_file:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            if log_file is None:
                today = datetime.now().strftime("%Y-%m-%d")
                log_file = f"{name}-{today}.log"
            
            file_path = os.path.join(log_dir, log_file)
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Internal method to log a message with additional context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context to include in the log
        """
        if kwargs:
            # Format additional context as JSON-like string
            context_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
            full_message = f"{message} - {{{context_str}}}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)


# Global logger registry to avoid creating duplicate loggers
_loggers: Dict[str, RPGLogger] = {}


def get_logger(name: Optional[str] = None, 
              level: Optional[int] = None,
              log_to_stdout: bool = True,
              log_to_file: bool = False,
              log_dir: str = "logs",
              log_file: Optional[str] = None) -> RPGLogger:
    """
    Get or create a logger with the given name.
    
    If no name is provided, automatically uses the calling module's name.
    
    Args:
        name: Logger name (defaults to calling module name)
        level: Minimum log level to record (defaults to INFO)
        log_to_stdout: Whether to log to stdout
        log_to_file: Whether to log to a file
        log_dir: Directory for log files
        log_file: Specific log file name (defaults to name-YYYY-MM-DD.log)
        
    Returns:
        RPGLogger instance
    """
    # If no name provided, get the calling module's name
    if name is None:
        # Get the frame of the caller
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        name = module.__name__ if module else "unknown"
    
    if name in _loggers:
        logger = _loggers[name]
        # Update level if specified
        if level is not None:
            logger.logger.setLevel(level)
        return logger
    
    if level is None:
        # Default to INFO, but check environment variable
        env_level = os.environ.get("RPG_HELPER_LOG_LEVEL", "INFO")
        level = get_level_from_string(env_level)
    
    logger = RPGLogger(
        name=name,
        level=level,
        log_to_stdout=log_to_stdout,
        log_to_file=log_to_file,
        log_dir=log_dir,
        log_file=log_file
    )
    
    _loggers[name] = logger
    return logger


def set_global_log_level(level: int):
    """
    Set the log level for all existing loggers.
    
    Args:
        level: New log level
    """
    for logger in _loggers.values():
        logger.logger.setLevel(level) 