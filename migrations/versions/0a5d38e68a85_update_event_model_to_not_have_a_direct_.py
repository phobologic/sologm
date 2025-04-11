"""Update Event model to not have a direct relationship to the Game model.

Revision ID: 0a5d38e68a85
Revises: 059617f91179
Create Date: 2025-04-11 15:40:52.153242

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "0a5d38e68a85"
down_revision: Union[str, None] = "059617f91179"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get the connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Get foreign key constraints for the events table
    fks = inspector.get_foreign_keys("events")

    # Find the constraint that references game_id
    fk_name = None
    for fk in fks:
        if "game_id" in fk["constrained_columns"]:
            fk_name = fk["name"]
            break

    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("events") as batch_op:
        if fk_name:
            batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.drop_column("game_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(
            sa.Column("game_id", sa.VARCHAR(length=255), nullable=False)
        )
        batch_op.create_foreign_key("fk_events_game_id", "games", ["game_id"], ["id"])
