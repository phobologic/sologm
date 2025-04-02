"""Logging utilities for Solo RPG Helper."""

import logging
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
    # Use debug parameter if provided, otherwise use config
    if debug is None:
        debug = config.get("debug", False)

    logger = logging.getLogger("sologm")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if debug:
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        console_handler.setLevel(logging.ERROR)  # Only show errors in normal mode
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
