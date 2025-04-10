"""Add Act model and update relationships

Revision ID: 059617f91179
Revises: b2d3e4f5g6h7
Create Date: 2025-04-10 07:39:39.096059

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "059617f91179"
down_revision: Union[str, None] = "b2d3e4f5g6h7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the acts table
    op.create_table(
        "acts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("game_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.Enum("ACTIVE", "COMPLETED", name="actstatus"), nullable=False
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "slug", name="uix_game_act_slug"),
    )
    op.create_index(op.f("ix_acts_slug"), "acts", ["slug"], unique=False)

    # Use batch mode for event_sources table to add unique constraint
    with op.batch_alter_table("event_sources") as batch_op:
        batch_op.create_unique_constraint("uq_event_sources_name", ["name"])

    # First, add the act_id column to scenes (initially nullable)
    op.add_column("scenes", sa.Column("act_id", sa.String(), nullable=True))

    # Create a default act for each existing game
    # Get all existing games
    connection = op.get_bind()
    games = connection.execute(sa.text("SELECT id, name FROM games")).fetchall()

    # For each game, create a default "Act 1"
    import uuid
    from datetime import datetime

    now = datetime.utcnow()

    for game_id, game_name in games:
        # Create a default act for this game
        act_id = str(uuid.uuid4())
        act_slug = "act-1-untitled"

        # Insert the act
        connection.execute(
            sa.text(
                """
                INSERT INTO acts (id, slug, game_id, title, description, status, 
                                 sequence, is_active, created_at, modified_at)
                VALUES (:id, :slug, :game_id, :title, :description, :status, 
                       :sequence, :is_active, :created_at, :modified_at)
                """
            ),
            {
                "id": act_id,
                "slug": act_slug,
                "game_id": game_id,
                "title": None,  # Untitled act
                "description": None,
                "status": "ACTIVE",
                "sequence": 1,
                "is_active": True,  # Set as active
                "created_at": now,
                "modified_at": now,
            },
        )

        # Update all scenes for this game to reference the new act
        connection.execute(
            sa.text(
                """
                UPDATE scenes
                SET act_id = :act_id
                WHERE game_id = :game_id
                """
            ),
            {"act_id": act_id, "game_id": game_id},
        )

    # Use a single batch operation with recreate="always" to handle all changes
    with op.batch_alter_table("scenes", recreate="always") as batch_op:
        # Create a foreign key from scenes.act_id to acts.id
        batch_op.create_foreign_key("fk_scenes_act_id_acts", "acts", ["act_id"], ["id"])
        
        # Update the unique constraint
        batch_op.create_unique_constraint("uix_act_scene_slug", ["act_id", "slug"])
        
        # Make act_id not nullable
        batch_op.alter_column("act_id", nullable=False)
        
        # Drop the game_id column (this will automatically drop any foreign keys)
        batch_op.drop_column("game_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the game_id column to scenes
    with op.batch_alter_table("scenes", recreate="always") as batch_op:
        # Add the game_id column
        batch_op.add_column(sa.Column("game_id", sa.String(), nullable=True))

    # Get all scenes and their associated acts to restore the game_id
    connection = op.get_bind()
    scenes_acts = connection.execute(
        sa.text("SELECT s.id, a.game_id FROM scenes s JOIN acts a ON s.act_id = a.id")
    ).fetchall()

    # Update each scene with its original game_id
    for scene_id, game_id in scenes_acts:
        connection.execute(
            sa.text("UPDATE scenes SET game_id = :game_id WHERE id = :scene_id"),
            {"game_id": game_id, "scene_id": scene_id},
        )

    # Complete the table modifications in a single batch operation
    with op.batch_alter_table("scenes", recreate="always") as batch_op:
        # Make game_id not nullable
        batch_op.alter_column("game_id", nullable=False)
        
        # Recreate the foreign key from scenes to games
        batch_op.create_foreign_key("fk_scenes_game_id_games", "games", ["game_id"], ["id"])
        
        # Update the unique constraint
        batch_op.create_unique_constraint("uix_game_scene_slug", ["game_id", "slug"])
        
        # Drop the act_id column
        batch_op.drop_column("act_id")

    # Use batch mode for event_sources table
    with op.batch_alter_table("event_sources") as batch_op:
        batch_op.drop_constraint("uq_event_sources_name", type_="unique")

    # Drop the acts table
    op.drop_index(op.f("ix_acts_slug"), table_name="acts")
    op.drop_table("acts")
