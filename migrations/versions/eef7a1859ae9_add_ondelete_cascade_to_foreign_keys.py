"""Add ondelete=CASCADE to foreign keys using batch operations for SQLite compatibility

Revision ID: eef7a1859ae9
Revises: 0001
Create Date: 2025-05-02 06:54:55.169808

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eef7a1859ae9"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema using batch operations."""
    print("Applying upgrade eef7a1859ae9: Add ondelete=CASCADE using batch operations")

    # Remove potential leftover table from previous attempts (if exists)
    # This might error if the table doesn't exist, consider checking first or ignoring error
    try:
        op.drop_table("events_new")
        print("Dropped potentially leftover 'events_new' table.")
    except Exception:
        print("'events_new' table not found, skipping drop.")
        pass  # Ignore if table doesn't exist

    # --- Acts Table ---
    print("Modifying 'acts' table...")
    with op.batch_alter_table("acts", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        # No need to explicitly drop the old one within the batch context for SQLite.
        batch_op.create_foreign_key(
            "fk_acts_game_id_games",  # Explicit constraint name
            "games",
            ["game_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_acts_game_id_games' on 'acts' with CASCADE."
        )

    # --- Dice Rolls Table ---
    print("Modifying 'dice_rolls' table...")
    with op.batch_alter_table("dice_rolls", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            "fk_dice_rolls_scene_id_scenes",  # Explicit constraint name
            "scenes",
            ["scene_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_dice_rolls_scene_id_scenes' on 'dice_rolls' with CASCADE."
        )

    # --- Events Table ---
    print("Modifying 'events' table...")
    with op.batch_alter_table("events", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            "fk_events_scene_id_scenes",  # Explicit constraint name
            "scenes",
            ["scene_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_events_scene_id_scenes' on 'events' with CASCADE."
        )
        # Note: We are NOT modifying the FK to event_sources or interpretations here.

    # --- Interpretation Sets Table ---
    print("Modifying 'interpretation_sets' table...")
    with op.batch_alter_table("interpretation_sets", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            "fk_interpretation_sets_scene_id_scenes",  # Explicit constraint name
            "scenes",
            ["scene_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_interpretation_sets_scene_id_scenes' on 'interpretation_sets' with CASCADE."
        )

    # --- Interpretations Table ---
    print("Modifying 'interpretations' table...")
    with op.batch_alter_table("interpretations", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            "fk_interpretations_set_id_interpretation_sets",  # Explicit constraint name
            "interpretation_sets",
            ["set_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_interpretations_set_id_interpretation_sets' on 'interpretations' with CASCADE."
        )

    # --- Scenes Table ---
    print("Modifying 'scenes' table...")
    with op.batch_alter_table("scenes", schema=None) as batch_op:
        # Define the target state: Create the FK constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            "fk_scenes_act_id_acts",  # Explicit constraint name
            "acts",
            ["act_id"],
            ["id"],
            ondelete="CASCADE",
        )
        print(
            "Created new FK constraint 'fk_scenes_act_id_acts' on 'scenes' with CASCADE."
        )

        # Drop the status column within the same batch operation
        batch_op.drop_column("status")
        print("Dropped column 'status' from 'scenes'.")

    # Create index outside the batch operation (Alembic handles this correctly for SQLite)
    op.create_index(op.f("ix_scenes_is_active"), "scenes", ["is_active"], unique=False)
    print("Created index 'ix_scenes_is_active' on 'scenes'.")

    print("Finished upgrade eef7a1859ae9.")


def downgrade() -> None:
    """Downgrade schema using batch operations."""
    print(
        "Applying downgrade eef7a1859ae9: Remove ondelete=CASCADE using batch operations"
    )

    # Drop index outside the batch operation
    op.drop_index(op.f("ix_scenes_is_active"), table_name="scenes")
    print("Dropped index 'ix_scenes_is_active' from 'scenes'.")

    # --- Scenes Table ---
    print("Reverting 'scenes' table...")
    with op.batch_alter_table("scenes", schema=None) as batch_op:
        # Add the status column back
        # Need to determine the original type and nullability. Assuming VARCHAR(9) NOT NULL based on original downgrade.
        batch_op.add_column(
            sa.Column(
                "status", sa.VARCHAR(length=9), nullable=False, server_default="active"
            )
        )  # Added server_default for non-null column
        print("Added column 'status' back to 'scenes'.")

        # Define the target state: Recreate the original constraint without CASCADE
        # No need to explicitly drop the CASCADE one first within the batch context.
        batch_op.create_foreign_key(
            "fk_scenes_act_id_acts",  # Use the same name for consistency
            "acts",
            ["act_id"],
            ["id"],
            # No ondelete specified
        )
        print(
            "Recreated original FK constraint 'fk_scenes_act_id_acts' on 'scenes' without CASCADE."
        )

    # --- Interpretations Table ---
    print("Reverting 'interpretations' table...")
    with op.batch_alter_table("interpretations", schema=None) as batch_op:
        # Define the target state: Recreate the original constraint without CASCADE
        batch_op.create_foreign_key(
            "fk_interpretations_set_id_interpretation_sets",
            "interpretation_sets",
            ["set_id"],
            ["id"],
        )
        print(
            "Recreated original FK constraint 'fk_interpretations_set_id_interpretation_sets' on 'interpretations' without CASCADE."
        )

    # --- Interpretation Sets Table ---
    print("Reverting 'interpretation_sets' table...")
    with op.batch_alter_table("interpretation_sets", schema=None) as batch_op:
        # Define the target state: Recreate the original constraint without CASCADE
        batch_op.create_foreign_key(
            "fk_interpretation_sets_scene_id_scenes", "scenes", ["scene_id"], ["id"]
        )
        print(
            "Recreated original FK constraint 'fk_interpretation_sets_scene_id_scenes' on 'interpretation_sets' without CASCADE."
        )

    # --- Events Table ---
    print("Reverting 'events' table...")
    with op.batch_alter_table("events", schema=None) as batch_op:
        # Define the target state: Recreate the original constraint without CASCADE
        batch_op.create_foreign_key(
            "fk_events_scene_id_scenes", "scenes", ["scene_id"], ["id"]
        )
        print(
            "Recreated original FK constraint 'fk_events_scene_id_scenes' on 'events' without CASCADE."
        )

    # --- Dice Rolls Table ---
    print("Reverting 'dice_rolls' table...")
    with op.batch_alter_table("dice_rolls", schema=None) as batch_op:
        # Define the target state: Recreate the original constraint without CASCADE
        batch_op.create_foreign_key(
            "fk_dice_rolls_scene_id_scenes", "scenes", ["scene_id"], ["id"]
        )
        print(
            "Recreated original FK constraint 'fk_dice_rolls_scene_id_scenes' on 'dice_rolls' without CASCADE."
        )

    # --- Acts Table ---
    print("Reverting 'acts' table...")
    with op.batch_alter_table("acts", schema=None) as batch_op:
        # Define the target state: Recreate the original constraint without CASCADE
        batch_op.create_foreign_key(
            "fk_acts_game_id_games", "games", ["game_id"], ["id"]
        )
        print(
            "Recreated original FK constraint 'fk_acts_game_id_games' on 'acts' without CASCADE."
        )

    # Remove the create_table('events_new', ...) from the original downgrade as it seemed unrelated/cruft.
    print("Finished downgrade eef7a1859ae9.")
