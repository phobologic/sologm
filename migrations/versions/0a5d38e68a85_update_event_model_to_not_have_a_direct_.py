"""Update Event model to not have a direct relationship to the Game model.

Revision ID: 0a5d38e68a85
Revises: 059617f91179
Create Date: 2025-04-11 15:40:52.153242

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic.context import get_context


# revision identifiers, used by Alembic.
revision: str = "0a5d38e68a85"
down_revision: Union[str, None] = "059617f91179"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch operations for SQLite compatibility
    context = get_context()
    if context.get_impl().dialect.name == "sqlite":
        with op.batch_alter_table("events") as batch_op:
            batch_op.drop_constraint(None, type_="foreignkey")
            batch_op.drop_column("game_id")
    else:
        # For other databases that support direct column dropping
        op.drop_constraint(None, "events", type_="foreignkey")
        op.drop_column("events", "game_id")


def downgrade() -> None:
    """Downgrade schema."""
    context = get_context()
    if context.get_impl().dialect.name == "sqlite":
        with op.batch_alter_table("events") as batch_op:
            batch_op.add_column(
                sa.Column("game_id", sa.VARCHAR(length=255), nullable=False)
            )
            batch_op.create_foreign_key(None, "games", ["game_id"], ["id"])
    else:
        # For other databases
        op.add_column(
            "events", sa.Column("game_id", sa.VARCHAR(length=255), nullable=False)
        )
        op.create_foreign_key(None, "events", "games", ["game_id"], ["id"])
