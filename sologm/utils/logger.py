"""Logging utilities for Solo RPG Helper."""

import logging
import os
import sys
from typing import Optional

from sologm.utils.config import config


def setup_logger(debug: Optional[bool] = None) -> logging.Logger:
    """Set up the logger for the application.

    When debug mode is enabled, logs will be sent to stdout.
    Otherwise, only error logs will be displayed.

    Args:
        debug: Override debug setting from config.

    Returns:
        Configured logger.
    """
    # Check environment variable first, then parameter, then config
    debug_env = os.environ.get("SOLOGM_DEBUG")
    if debug_env is not None:
        debug = debug_env.lower() in ("1", "true", "yes")
    elif debug is None:
        debug = config.get("debug", False)

    logger = logging.getLogger("sologm")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.ERROR)
    
    # Always use debug format when debug is enabled
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ) if debug else logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
