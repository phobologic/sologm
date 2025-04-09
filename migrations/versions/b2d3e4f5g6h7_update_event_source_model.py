"""Update EventSource model to use integer primary key

Revision ID: b2d3e4f5g6h7
Revises: a1b2c3d4e5f6
Create Date: 2025-04-10 15:30:42.123456

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d3e4f5g6h7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, we need to recreate the tables with the new schema

    # Create a temporary table with the new schema for event_sources
    op.execute(
        """
        CREATE TABLE event_sources_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(32) NOT NULL UNIQUE
        )
        """
    )

    # Copy data from the old table to the new one, mapping id to name
    op.execute(
        """
        INSERT INTO event_sources_new (name)
        SELECT id FROM event_sources
        """
    )

    # Create a temporary table for events with the new foreign key
    op.execute(
        """
        CREATE TABLE events_new (
            id VARCHAR(255) NOT NULL, 
            scene_id VARCHAR(255) NOT NULL, 
            game_id VARCHAR(255) NOT NULL, 
            description TEXT NOT NULL, 
            source_id INTEGER NOT NULL, 
            interpretation_id VARCHAR(255), 
            created_at DATETIME NOT NULL, 
            modified_at DATETIME NOT NULL, 
            PRIMARY KEY (id), 
            FOREIGN KEY(scene_id) REFERENCES scenes (id), 
            FOREIGN KEY(game_id) REFERENCES games (id), 
            FOREIGN KEY(interpretation_id) REFERENCES interpretations (id),
            FOREIGN KEY(source_id) REFERENCES event_sources_new (id)
        )
        """
    )

    # Copy data from the old events table to the new one, mapping source_id to the new ID
    op.execute(
        """
        INSERT INTO events_new (id, scene_id, game_id, description, source_id, interpretation_id, created_at, modified_at)
        SELECT e.id, e.scene_id, e.game_id, e.description, es.id, e.interpretation_id, e.created_at, e.modified_at
        FROM events e
        JOIN event_sources_new es ON e.source_id = es.name
        """
    )

    # Drop the old tables
    op.drop_table("events")
    op.drop_table("event_sources")

    # Rename the new tables to the original names
    op.rename_table("events_new", "events")
    op.rename_table("event_sources_new", "event_sources")


def downgrade() -> None:
    """Downgrade schema."""
    # For SQLite, we need to recreate the tables with the old schema

    # Create a temporary table with the old schema for event_sources
    op.execute(
        """
        CREATE TABLE event_sources_old (
            id VARCHAR(50) NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE
        )
        """
    )

    # Copy data from the new table to the old one, mapping name to id and name to name
    op.execute(
        """
        INSERT INTO event_sources_old (id, name)
        SELECT name, name FROM event_sources
        """
    )

    # Create a temporary table for events with the old foreign key
    op.execute(
        """
        CREATE TABLE events_old (
            id VARCHAR(255) NOT NULL, 
            scene_id VARCHAR(255) NOT NULL, 
            game_id VARCHAR(255) NOT NULL, 
            description TEXT NOT NULL, 
            source_id VARCHAR(50) NOT NULL, 
            interpretation_id VARCHAR(255), 
            created_at DATETIME NOT NULL, 
            modified_at DATETIME NOT NULL, 
            PRIMARY KEY (id), 
            FOREIGN KEY(scene_id) REFERENCES scenes (id), 
            FOREIGN KEY(game_id) REFERENCES games (id), 
            FOREIGN KEY(interpretation_id) REFERENCES interpretations (id),
            FOREIGN KEY(source_id) REFERENCES event_sources_old (id)
        )
        """
    )

    # Copy data from the new events table to the old one, mapping source_id to name
    op.execute(
        """
        INSERT INTO events_old (id, scene_id, game_id, description, source_id, interpretation_id, created_at, modified_at)
        SELECT e.id, e.scene_id, e.game_id, e.description, es.name, e.interpretation_id, e.created_at, e.modified_at
        FROM events e
        JOIN event_sources es ON e.source_id = es.id
        """
    )

    # Drop the new tables
    op.drop_table("events")
    op.drop_table("event_sources")

    # Rename the old tables to the original names
    op.rename_table("events_old", "events")
    op.rename_table("event_sources_old", "event_sources")
