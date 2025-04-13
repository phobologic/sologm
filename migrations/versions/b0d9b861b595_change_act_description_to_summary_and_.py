"""change act description to summary and remove status

Revision ID: b0d9b861b595
Revises: 0a5d38e68a85
Create Date: 2025-04-13 14:11:56.601206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0d9b861b595'
down_revision: Union[str, None] = '0a5d38e68a85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('acts', sa.Column('summary', sa.Text(), nullable=True))
    op.drop_column('acts', 'status')
    op.drop_column('acts', 'description')
    op.alter_column('games', 'description',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('scenes', 'description',
               existing_type=sa.TEXT(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('scenes', 'description',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('games', 'description',
               existing_type=sa.TEXT(),
               nullable=False)
    op.add_column('acts', sa.Column('description', sa.TEXT(), nullable=True))
    op.add_column('acts', sa.Column('status', sa.VARCHAR(length=9), nullable=False))
    op.drop_column('acts', 'summary')
    # ### end Alembic commands ###
