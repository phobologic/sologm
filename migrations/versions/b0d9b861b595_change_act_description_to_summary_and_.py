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
    # First, add the summary column to acts table
    with op.batch_alter_table("acts") as batch_op:
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))
    
    # Copy data from description to summary
    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE acts SET summary = description WHERE description IS NOT NULL"
    ))
    
    # Now use batch operations with recreate for the structural changes
    with op.batch_alter_table("acts", recreate="always") as batch_op:
        # Drop the status and description columns
        batch_op.drop_column('status')
        batch_op.drop_column('description')
    
    # Use batch operations for games table
    with op.batch_alter_table("games") as batch_op:
        batch_op.alter_column('description',
                   existing_type=sa.TEXT(),
                   nullable=True)
    
    # Use batch operations for scenes table
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.alter_column('description',
                   existing_type=sa.TEXT(),
                   nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch operations for scenes table
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.alter_column('description',
                   existing_type=sa.TEXT(),
                   nullable=False)
    
    # Use batch operations for games table
    with op.batch_alter_table("games") as batch_op:
        batch_op.alter_column('description',
                   existing_type=sa.TEXT(),
                   nullable=False)
    
    # First, add back the original columns
    with op.batch_alter_table("acts") as batch_op:
        batch_op.add_column(sa.Column('description', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.VARCHAR(length=9), nullable=False, server_default="ACTIVE"))
    
    # Copy data from summary back to description
    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE acts SET description = summary WHERE summary IS NOT NULL"
    ))
    
    # Set default status for all acts
    connection.execute(sa.text(
        "UPDATE acts SET status = 'ACTIVE'"
    ))
    
    # Now drop the summary column
    with op.batch_alter_table("acts", recreate="always") as batch_op:
        batch_op.drop_column('summary')
    
    # Remove the server_default from status
    with op.batch_alter_table("acts") as batch_op:
        batch_op.alter_column('status', server_default=None)
