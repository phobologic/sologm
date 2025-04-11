"""Update Event model to not have a direct relationship to the Game model.

Revision ID: 0a5d38e68a85
Revises: 059617f91179
Create Date: 2025-04-11 15:40:52.153242

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a5d38e68a85"
down_revision: Union[str, None] = "059617f91179"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch operations for SQLite compatibility
    # SQLite doesn't support dropping columns directly, so we use batch operations
    with op.batch_alter_table("events") as batch_op:
        # Use None to let SQLAlchemy find the constraint by column
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("game_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(
            sa.Column("game_id", sa.VARCHAR(length=255), nullable=False)
        )
        # Use None for the constraint name in downgrade as well
        batch_op.create_foreign_key(None, "games", ["game_id"], ["id"])
