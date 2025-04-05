"""Database package for SoloGM."""

import logging
import os
from typing import Optional

from sqlalchemy.engine import Engine

from sologm.database.session import (
    DatabaseSession,
    get_session,
    initialize_database,
    get_db_context,
)
from sologm.utils.config import Config

logger = logging.getLogger(__name__)

def init_db(engine: Optional[Engine] = None) -> DatabaseSession:
    """Initialize the database connection.
    
    Args:
        engine: Pre-configured SQLAlchemy engine
        
    Returns:
        Initialized DatabaseSession instance
    """
    if engine:
        logger.info("Initializing database with provided engine")
        return initialize_database(engine=engine)
    
    # Priority: 1. Environment variable, 2. Config file
    db_url = os.environ.get("SOLOGM_DATABASE_URL")
    
    if not db_url:
        config = Config.get_instance()
        db_url = config.get("database_url")
        
    if not db_url:
        logger.error("No database URL configured")
        raise ValueError(
            "No database URL configured. Please set the SOLOGM_DATABASE_URL "
            "environment variable or add 'database_url' to your config file."
        )
    
    logger.info(f"Initializing database with URL: {db_url}")
    return initialize_database(db_url=db_url)

__all__ = [
    "DatabaseSession",
    "get_session",
    "initialize_database",
    "get_db_context",
    "init_db",
]
