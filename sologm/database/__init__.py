"""Database package for SoloGM."""

import logging
import os
from typing import Optional

from sqlalchemy.engine import Engine

from sologm.database.session import (
    DatabaseSession,
    get_db_context,
    get_session,
    initialize_database,
)
from sologm.utils.config import Config

logger = logging.getLogger(__name__)


def init_db(engine: Optional[Engine] = None) -> DatabaseSession:
    """Initialize the database and create tables if they don't exist.

    Args:
        engine: Pre-configured SQLAlchemy engine instance (optional)

    Returns:
        The DatabaseSession instance.

    Raises:
        ValueError: If database URL cannot be determined
    """
    logger.info("Initializing database")

    from sologm.utils.config import get_config

    # Get database URL from config if engine not provided
    if not engine:
        config = get_config()
        db_url = config.get("database_url")

        if not db_url:
            logger.error("No database URL configured")
            raise ValueError(
                "Database URL not configured. Set SOLOGM_DATABASE_URL environment "
                "variable or add 'database_url' to your config file."
            )

        # Get or create the singleton instance
        db_session = DatabaseSession.get_instance(db_url=db_url)
    else:
        # Use provided engine
        db_session = DatabaseSession.get_instance(engine=engine)

    # Create tables
    db_session.create_tables()

    logger.info("Database initialized successfully")
    return db_session


__all__ = [
    "DatabaseSession",
    "get_session",
    "initialize_database",
    "get_db_context",
    "init_db",
]
