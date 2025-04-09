"""Add EventSource reference table

Revision ID: a1b2c3d4e5f6
Revises: 5d69d6f23e19
Create Date: 2023-11-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5d69d6f23e19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create event_sources table
    op.create_table(
        "event_sources",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )

    # Insert default event sources
    op.execute(
        """
        INSERT INTO event_sources (id, name) VALUES
        ('manual', 'Manual Entry'),
        ('oracle', 'Oracle Interpretation'),
        ('dice', 'Dice Roll')
        """
    )

    # For SQLite, we need to recreate the events table with the new foreign key
    # Create a temporary table with the new schema
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
