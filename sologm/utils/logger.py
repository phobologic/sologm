"""Logging utilities for Solo RPG Helper."""

import logging
import os
import sys
from typing import Optional

from sologm.utils.config import config


def setup_root_logger(debug: Optional[bool] = None) -> None:
    """Configure the root logger for the application.

    When debug mode is enabled, logs will be sent to stdout with debug level.
    Otherwise, only error logs will be displayed.

    Args:
        debug: Override debug setting from config. If None, will check
            environment variable SOLOGM_DEBUG and then config file.
    """
    # Check environment variable first, then parameter, then config
    debug_env = os.environ.get("SOLOGM_DEBUG")
    if debug_env is not None:
        debug = debug_env.lower() in ("1", "true", "yes")
    elif debug is None:
        debug = config.get("debug", False)

    # Configure the root logger for the sologm package
    logger = logging.getLogger("sologm")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove any existing handlers
    logger.handlers = []

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.ERROR)

    # Use detailed format in debug mode, simple format otherwise
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ) if debug else logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
