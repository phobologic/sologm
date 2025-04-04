"""Utility functions for SQLAlchemy models."""

import uuid
from typing import Optional


def generate_unique_id(prefix: Optional[str] = None) -> str:
    """Generate a unique ID with an optional prefix.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        A unique ID string.
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: The text to convert.

    Returns:
        A URL-friendly version of the text.
    """
    return "-".join(text.lower().split())
