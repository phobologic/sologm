"""Logging utilities for Solo RPG Helper."""

import logging
import logging.handlers  # Import handlers
import os
import sys
from pathlib import Path  # Use pathlib for paths
from typing import Optional

# Import get_config here
from sologm.utils.config import ConfigError, get_config

# Define application name for potential use
APP_NAME = "sologm"


def setup_root_logger(debug: Optional[bool] = None) -> None:
    """Configure the root logger for the application.

    Reads logging settings (path, size, backups) from config.
    - In debug mode: Logs DEBUG and above to stdout.
    - In non-debug mode: Logs INFO and above to a configured rotating file.

    Args:
        debug: Override debug setting from config. If None, checks env var
               SOLOGM_DEBUG, then config file.
    """
    config = None
    try:
        config = get_config()
    except ConfigError as e:
        # Config failed to load, log critical error to stderr.
        sys.stderr.write(f"CRITICAL: Failed to load configuration for logging: {e}\n")
        # Setup minimal stderr logging for errors only
        logger = logging.getLogger("sologm")
        logger.setLevel(logging.ERROR)
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        # Avoid adding duplicate handlers if this somehow runs multiple times on failure
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            logger.addHandler(handler)
        return  # Stop further setup

    # Determine debug status (using config safely now)
    debug_env = os.environ.get("SOLOGM_DEBUG")
    if debug_env is not None:
        debug = debug_env.lower() in ("1", "true", "yes")
    elif debug is None:
        debug = config.get("debug", False)  # Default to False if key missing

    # Get the root logger for the application package
    logger = logging.getLogger("sologm")

    # Remove any existing handlers to prevent duplicates and ensure clean setup
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()  # Close handlers before removing

    if debug:
        # --- Debug Mode: Log DEBUG+ to stdout ---
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        # --- Non-Debug Mode: Log INFO+ to rotating file ---
        logger.setLevel(logging.INFO)  # Default file level

        # --- Get logging config with defaults ---
        # Use config.base_dir for the default path calculation
        default_log_path = config.base_dir / f"{APP_NAME}.log"  # Calculate default path
        log_file_path_str = config.get(
            "log_file_path", str(default_log_path)
        )  # Use flat key
        log_max_bytes = config.get("log_max_bytes", 5 * 1024 * 1024)  # Use flat key
        log_backup_count = config.get("log_backup_count", 1)  # Use flat key

        # --- Determine final log file path ---
        log_file_path = Path(log_file_path_str)
        # Check if the configured path is absolute. If not, make it relative to config.base_dir
        if not log_file_path.is_absolute():
            log_file_path = config.base_dir / log_file_path
            # Log this resolution only if logger is already partially configured or use print
            # print(f"DEBUG: Relative log path configured. Resolved to: {log_file_path}")

        # Ensure log directory exists
        try:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            sys.stderr.write(
                f"Warning: Could not create log directory {log_file_path.parent}. Logging to stderr instead. Error: {e}\n"
            )
            # Fallback to basic stderr logging for errors only
            logger.setLevel(logging.ERROR)
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.ERROR)
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return  # Exit setup early

        # Create the rotating file handler using configured values
        try:
            handler = logging.handlers.RotatingFileHandler(
                filename=log_file_path,
                maxBytes=int(log_max_bytes),  # Ensure integer
                backupCount=int(log_backup_count),  # Ensure integer
                encoding="utf-8",
            )
            handler.setLevel(logging.INFO)  # Use INFO level for file handler
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        except (
            ValueError,
            OSError,
        ) as e:  # Catch potential errors during handler creation/config parsing
            sys.stderr.write(
                f"Warning: Could not create log file handler for {log_file_path} (maxBytes={log_max_bytes}, backupCount={log_backup_count}). Logging to stderr instead. Error: {e}\n"
            )
            # Fallback to basic stderr logging for errors only
            logger.setLevel(logging.ERROR)
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.ERROR)
            formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Common steps: Set formatter and add handler
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Optional: Log the mode for clarity, especially in the log file
    if not debug:
        # Use the resolved log_file_path here
        logger.info(
            f"--- Starting sologm session (Log Level: INFO, File: {log_file_path}, MaxBytes: {log_max_bytes}, Backups: {log_backup_count}) ---"
        )
    # else: # Debug logging already goes to stdout
    #     logger.debug("--- Starting sologm session (Log Level: DEBUG, Output: stdout) ---")
