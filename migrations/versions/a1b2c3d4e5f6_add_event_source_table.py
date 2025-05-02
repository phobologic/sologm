"""Add EventSource reference table

Revision ID: a1b2c3d4e5f6
Revises: 5d69d6f23e19
Create Date: 2025-04-08 20:18:37.910271

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5d69d6f23e19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if the event_sources table already exists
    if not inspector.has_table("event_sources"):
        # Create event_sources table only if it doesn't exist
        op.create_table(
            "event_sources",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
        )

        # Insert default event sources only if the table was just created
        op.execute(
            """
            INSERT INTO event_sources (id, name) VALUES
            ('manual', 'Manual Entry'),
            ('oracle', 'Oracle Interpretation'),
            ('dice', 'Dice Roll')
            """
        )
    else:
        print("Table 'event_sources' already exists, skipping creation and data insertion.")


    # --- SQLite Specific Logic for 'events' table modification ---
    # This part assumes the 'event_sources' table exists (either pre-existing or just created)
    # and modifies the 'events' table. This logic remains unchanged as per the request.

    # Create a temporary table with the new schema for 'events'
    op.execute(
        """
        CREATE TABLE events_new (
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
            FOREIGN KEY(source_id) REFERENCES event_sources (id)
        )
        """
    )

    # Copy data from the old table to the new one, mapping source to source_id
    op.execute(
        """
        INSERT INTO events_new 
        SELECT id, scene_id, game_id, description, source, interpretation_id, created_at, modified_at
        FROM events
        """
    )

    # Drop the old table
    op.drop_table("events")

    # Rename the new table to the original name
    op.rename_table("events_new", "events")


def downgrade() -> None:
    """Downgrade schema."""
    # For SQLite, we need to recreate the events table without the foreign key
    # Create a temporary table with the old schema
    op.execute(
        """
        CREATE TABLE events_old (
            id VARCHAR(255) NOT NULL, 
            scene_id VARCHAR(255) NOT NULL, 
            game_id VARCHAR(255) NOT NULL, 
            description TEXT NOT NULL, 
            source VARCHAR(255) NOT NULL, 
            interpretation_id VARCHAR(255), 
            created_at DATETIME NOT NULL, 
            modified_at DATETIME NOT NULL, 
            PRIMARY KEY (id), 
            FOREIGN KEY(scene_id) REFERENCES scenes (id), 
            FOREIGN KEY(game_id) REFERENCES games (id), 
            FOREIGN KEY(interpretation_id) REFERENCES interpretations (id)
        )
        """
    )

    # Copy data from the new table to the old one, mapping source_id to source
    op.execute(
        """
        INSERT INTO events_old 
        SELECT id, scene_id, game_id, description, source_id, interpretation_id, created_at, modified_at
        FROM events
        """
    )

    # Drop the new table
    op.drop_table("events")

    # Rename the old table to the original name
    op.rename_table("events_old", "events")

    # Drop the event_sources table
    op.drop_table("event_sources")
