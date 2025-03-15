"""
Story-focused logging extension for the RPG Helper application.
"""
import logging
import inspect
from typing import Dict, Optional, Any

from .logging import RPGLogger, LogFormatter, get_logger, initialize_logging, _loggers

# Define the STORY log level
STORY_LEVEL_ID = 25
logging.addLevelName(STORY_LEVEL_ID, 'STORY')


class StoryFormatter(logging.Formatter):
    """Formatter for story mode logging."""
    
    def format(self, record):
        # Extract prefix from record if available
        prefix = getattr(record, 'prefix', 'System')
        # Use System emoji for unknown prefixes
        prefix_str = StoryLogger.PREFIXES.get(prefix, f"🔧 {prefix}")
        
        # Format the message with prefix
        record.message = record.getMessage()
        message = record.message
        
        # Add exception info if available
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            if record.exc_text:
                message = f"{message}\n{record.exc_text}"
        
        return f"{prefix_str} {message}"


class DebugFormatter(logging.Formatter):
    """Technical formatter for debug mode logging."""
    
    def __init__(self, **kwargs):
        """Initialize with standard debug format."""
        super().__init__(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(pathname)s:%(lineno)d - %(message)s',
            **kwargs
        )
    
    def format(self, record):
        # First apply the standard formatting
        formatted = super().format(record)
        
        # Add prefix if available (for story messages in debug mode)
        if hasattr(record, 'prefix'):
            prefix = record.prefix
            prefix_str = StoryLogger.PREFIXES.get(prefix, StoryLogger.PREFIXES['System'])
            return f"{formatted} (prefix: {prefix_str})"
        
        return formatted


class StoryLogFormatter(LogFormatter):
    """Story-aware formatter factory that extends the base LogFormatter."""
    
    @classmethod
    def create_formatter(cls, format_type: str = "default", **kwargs) -> logging.Formatter:
        """Create a story-aware formatter.
        
        Args:
            format_type: Type of formatter to create ("story", "debug", or base types)
            **kwargs: Additional arguments to pass to the Formatter constructor
        
        Returns:
            logging.Formatter instance configured for story or debug mode
        """
        # Remove is_debug from kwargs if present
        is_debug = kwargs.pop('is_debug', False)
        
        if is_debug or format_type == "debug":
            return DebugFormatter(**kwargs)
        elif format_type == "story" or format_type == "default":
            return StoryFormatter()
        else:
            # For other format types, use the parent class implementation
            return super().create_formatter(format_type, **kwargs)


class StoryLogger(RPGLogger):
    """Extended logger with story-specific functionality."""
    
    # Define prefixes for different model types
    PREFIXES = {
        'Game': '🎲 Game',
        'Scene': '🎬 Scene',
        'SceneEvent': '🎭 Event',
        'Poll': '📊 Poll',
        'User': '👤 User',
        'System': '🔧 System',
    }
    
    def __init__(self, 
                name: str, 
                level: int = logging.INFO,
                log_to_stdout: bool = True,
                log_to_file: bool = False,
                log_dir: str = "logs",
                log_file: Optional[str] = None,
                format_type: str = "default",
                formatter_kwargs: Optional[Dict[str, Any]] = None):
        """Initialize story logger with story-specific configuration."""
        # Initialize with parent class but override formatter creation
        super().__init__(
            name=name,
            level=level,
            log_to_stdout=False,  # Don't add handlers at logger level
            log_to_file=log_file is not None,  # Only add file handler if explicitly requested
            log_dir=log_dir,
            log_file=log_file,
            format_type=format_type,
            formatter_kwargs=formatter_kwargs
        )
        
        # Ensure propagation is enabled
        self.logger.propagate = True
        
        # Set debug level if in debug mode
        if format_type == "debug":
            self.logger.setLevel(logging.DEBUG)
        
        # Apply story formatter to any remaining handlers (file handlers)
        formatter = StoryLogFormatter.create_formatter(format_type, **(formatter_kwargs or {}))
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def story(self, message: str, prefix: str = 'System', **kwargs):
        """
        Log a story message with optional prefix.
        
        Args:
            message: The story message to log
            prefix: Category prefix for the message (e.g., 'Game', 'Scene')
            **kwargs: Additional context to include in the log
        """
        if not self.logger.isEnabledFor(STORY_LEVEL_ID):
            return
            
        extra = kwargs.pop('extra', {}).copy() if 'extra' in kwargs else {}
        extra['prefix'] = prefix
        
        # Handle exc_info if provided
        exc_info = kwargs.pop('exc_info', None)
        if exc_info:
            extra['exc_info'] = exc_info
        
        self._log(STORY_LEVEL_ID, message, extra=extra, **kwargs)


# Global story logger registry
_story_loggers: Dict[str, StoryLogger] = {}


def get_story_logger(name: Optional[str] = None, 
                    level: Optional[int] = None,
                    log_to_stdout: bool = True,
                    log_to_file: bool = False,
                    log_dir: str = "logs",
                    log_file: Optional[str] = None,
                    format_type: Optional[str] = None,
                    formatter_kwargs: Optional[Dict[str, Any]] = None) -> StoryLogger:
    """
    Get or create a story-enabled logger.
    
    Args:
        name: Logger name (defaults to calling module name)
        level: Minimum log level to record (defaults to INFO)
        log_to_stdout: Whether to log to stdout
        log_to_file: Whether to log to a file
        log_dir: Directory for log files
        log_file: Specific log file name (defaults to name-YYYY-MM-DD.log)
        format_type: Type of log format to use (defaults to global config)
        formatter_kwargs: Additional arguments for the formatter
        
    Returns:
        StoryLogger instance
    """
    # If no name provided, get the calling module's name
    if name is None:
        # Get the frame of the caller
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        name = module.__name__ if module else "unknown"
    
    # Return existing logger if it exists
    if name in _story_loggers:
        logger = _story_loggers[name]
        # Update level if specified
        if level is not None:
            logger.logger.setLevel(level)
        return logger

    # Create a new logger
    logger = StoryLogger(
        name=name,
        level=level if level is not None else STORY_LEVEL_ID,
        log_to_stdout=log_to_stdout,
        log_to_file=log_to_file,
        log_dir=log_dir,
        log_file=log_file,
        format_type=format_type or "story",
        formatter_kwargs=formatter_kwargs
    )
    
    _story_loggers[name] = logger
    return logger


def setup_story_logging(debug_mode: bool = False):
    """
    Set up logging for story mode or debug mode.
    
    Args:
        debug_mode: If True, set up logging for debug mode. Otherwise, set up for story mode.
    """
    format_type = "debug" if debug_mode else "story"
    level = logging.DEBUG if debug_mode else STORY_LEVEL_ID
    
    # Initialize logging with appropriate settings
    initialize_logging(format_type=format_type, level=level)
    
    # Create story formatter
    formatter = StoryLogFormatter.create_formatter(format_type)
    
    # Update root logger and its handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)
        handler.setFormatter(formatter)
    
    # Update all existing loggers - remove their handlers and ensure propagation
    for logger in _story_loggers.values():
        logger.logger.handlers.clear()  # Remove handlers from individual loggers
        logger.logger.setLevel(level)
        logger.logger.propagate = True  # Ensure propagation to root logger 