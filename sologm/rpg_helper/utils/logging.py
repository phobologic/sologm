"""
Core logging utilities for the RPG Helper application.
"""
import logging
import os
import sys
import inspect
from datetime import datetime
from typing import Optional, Union, Dict, Any, Tuple


class LogLevel:
    """Log levels."""
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


class LoggingConfig:
    """Global configuration for logging formats."""
    
    _format_type: str = "default"
    _formatter_kwargs: Dict[str, Any] = {}
    
    @classmethod
    def set_global_format(cls, format_type: str, **kwargs):
        """
        Set the global logging format configuration.
        
        Args:
            format_type: The type of format to use ("default", "simple", "json")
            **kwargs: Additional formatter configuration
        """
        cls._format_type = format_type
        cls._formatter_kwargs = kwargs
        cls.update_existing_loggers()
    
    @classmethod
    def get_format_config(cls) -> Tuple[str, Dict[str, Any]]:
        """Get the current format configuration."""
        return cls._format_type, cls._formatter_kwargs.copy()
    
    @classmethod
    def update_existing_loggers(cls):
        """Update all existing loggers with current format configuration."""
        format_type, formatter_kwargs = cls.get_format_config()
        formatter = LogFormatter.create_formatter(format_type, **formatter_kwargs)
        
        for logger in _loggers.values():
            for handler in logger.logger.handlers:
                handler.setFormatter(formatter)


class LogFormatter:
    """Factory class for creating log formatters."""
    
    @staticmethod
    def create_formatter(format_type: str = "default", **kwargs) -> logging.Formatter:
        """
        Create a formatter based on the specified type.
        
        Args:
            format_type: Type of formatter to create ("default", "simple", "json")
            **kwargs: Additional arguments to pass to the Formatter constructor
        
        Returns:
            logging.Formatter instance
        """
        if format_type == "simple":
            return logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                **kwargs
            )
        elif format_type == "json":
            return logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
                **kwargs
            )
        # default
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            **kwargs
        )


class RPGLogger:
    """Base logger for the RPG Helper application."""
    
    def __init__(self, 
                name: str, 
                level: int = LogLevel.INFO,
                log_to_stdout: bool = True,
                log_to_file: bool = False,
                log_dir: str = "logs",
                log_file: Optional[str] = None,
                format_type: str = "default",
                formatter_kwargs: Optional[Dict[str, Any]] = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name (usually module name)
            level: Minimum log level to record
            log_to_stdout: Whether to log to stdout
            log_to_file: Whether to log to a file
            log_dir: Directory for log files
            log_file: Specific log file name (defaults to name-YYYY-MM-DD.log)
            format_type: Type of log format to use
            formatter_kwargs: Additional arguments for the formatter
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent propagation to root logger to avoid duplicate messages
        self.logger.propagate = False
        
        formatter = LogFormatter.create_formatter(
            format_type,
            **(formatter_kwargs or {})
        )
        
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        if log_to_stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        if log_to_file:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            if log_file is None:
                today = datetime.now().strftime("%Y-%m-%d")
                log_file = f"{name}-{today}.log"
            
            file_path = os.path.join(log_dir, log_file)
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, **kwargs):
        """Log a debug message."""
        self.logger.debug(msg, extra={"data": kwargs})
    
    def info(self, msg: str, **kwargs):
        """Log an info message."""
        self.logger.info(msg, extra={"data": kwargs})
    
    def warning(self, msg: str, **kwargs):
        """Log a warning message."""
        self.logger.warning(msg, extra={"data": kwargs})
    
    def error(self, msg: str, **kwargs):
        """Log an error message."""
        self.logger.error(msg, extra={"data": kwargs})
    
    def critical(self, msg: str, **kwargs):
        """Log a critical message."""
        self.logger.critical(msg, extra={"data": kwargs})


# Global logger registry
_loggers: Dict[str, RPGLogger] = {}


def get_logger(
    name: Optional[str] = None,
    level: Optional[int] = None,
    format_type: Optional[str] = None,
    formatter_kwargs: Optional[Dict[str, Any]] = None,
    log_to_stdout: bool = True,
    log_to_file: bool = False,
    log_dir: str = "logs",
    log_file: Optional[str] = None
) -> RPGLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (defaults to module name)
        level: Optional log level override
        format_type: Optional format type override
        formatter_kwargs: Optional formatter arguments override
        log_to_stdout: Whether to log to stdout
        log_to_file: Whether to log to a file
        log_dir: Directory for log files
        log_file: Specific log file name
    
    Returns:
        RPGLogger instance
    """
    if name is None:
        # Get the module name of the caller
        frame = inspect.currentframe()
        if frame is None:
            name = "__main__"
        else:
            try:
                frame = frame.f_back
                if frame is not None:
                    name = frame.f_globals["__name__"]
                else:
                    name = "__main__"
            finally:
                del frame
    
    if name in _loggers:
        logger = _loggers[name]
        if level is not None:
            logger.logger.setLevel(level)
        if format_type is not None or formatter_kwargs is not None:
            global_format, global_kwargs = LoggingConfig.get_format_config()
            final_format_type = format_type or global_format
            final_formatter_kwargs = formatter_kwargs or global_kwargs
            formatter = LogFormatter.create_formatter(final_format_type, **final_formatter_kwargs)
            for handler in logger.logger.handlers:
                handler.setFormatter(formatter)
        return logger

    if level is None:
        env_level = os.environ.get("RPG_HELPER_LOG_LEVEL", "INFO")
        level = get_level_from_string(env_level)
    
    global_format, global_kwargs = LoggingConfig.get_format_config()
    final_format_type = format_type or global_format
    final_formatter_kwargs = formatter_kwargs or global_kwargs
    
    logger = RPGLogger(
        name=name,
        level=level,
        log_to_stdout=log_to_stdout,
        log_to_file=log_to_file,
        log_dir=log_dir,
        log_file=log_file,
        format_type=final_format_type,
        formatter_kwargs=final_formatter_kwargs
    )
    
    _loggers[name] = logger
    return logger


def set_global_log_level(level: int):
    """Set the log level for all existing loggers."""
    for logger in _loggers.values():
        logger.logger.setLevel(level)


def initialize_logging(
    format_type: str = "default",
    level: Optional[int] = None,
    **formatter_kwargs
) -> None:
    """
    Initialize global logging configuration.
    
    Args:
        format_type: The type of format to use ("default", "simple", "json")
        level: Optional global log level
        **formatter_kwargs: Additional formatter configuration
    """
    LoggingConfig.set_global_format(format_type, **formatter_kwargs)
    
    if level is not None:
        # Clear any existing root handlers to avoid duplicates
        logging.root.handlers.clear()
        
        # Set root logger level
        logging.root.setLevel(level)
        
        # Update all existing loggers
        set_global_log_level(level) 