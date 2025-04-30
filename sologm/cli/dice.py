"""Dice rolling commands for Solo RPG Helper."""

import logging
from typing import TYPE_CHECKING, Optional

import typer

# Console import removed
from sqlalchemy.orm import Session

# display import removed
from sologm.core.dice import DiceManager
from sologm.database.session import get_db_context
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError, SceneError

if TYPE_CHECKING:
    from sologm.cli.rendering.base import Renderer


logger = logging.getLogger(__name__)
dice_app = typer.Typer(help="Dice rolling commands")
# console instance removed


def resolve_scene_id(session: Session, scene_id: Optional[str]) -> Optional[Scene]:
    """Resolve scene ID from active context if not provided.

    Args:
        session: Database session
        scene_id: Optional scene ID provided by user.

    Returns:
        Resolved Scene or None if not resolvable. Defaults to the current scene
        if no scene_id is passed in.
    """
    scene = None
    # Create a new DiceManager instance with the session
    dice_manager = DiceManager(session=session)
    # Access scene manager through dice manager
    scene_manager = dice_manager.scene_manager

    if scene_id is None:
        try:
            logger.debug("Attempting to resolve current scene.")
            context = scene_manager.get_active_context()
            scene = context["scene"]
            logger.debug(f"Using current scene: {scene.id}")
        except SceneError as e:
            logger.debug(f"Could not determine current scene: {str(e)}")
    else:
        scene = scene_manager.get_scene(scene_id)

    return scene


@dice_app.command("roll")
def roll_dice_command(
    ctx: typer.Context,
    notation: str = typer.Argument(..., help="Dice notation (e.g., 2d6+3)"),
    reason: Optional[str] = typer.Option(
        None, "--reason", "-r", help="Reason for the roll"
    ),
    scene_id: Optional[str] = typer.Option(
        None, "--scene-id", "-s", help="ID of the scene for this roll"
    ),
) -> None:
    """Roll dice using standard notation (XdY+Z).

    Args:
        ctx: Typer context.
        notation: Dice notation string (e.g., "2d6+3").
        reason: Optional reason for the roll.
        scene_id: Optional ID of the scene to associate the roll with.

    Examples:
        1d20    Roll a single 20-sided die
        2d6+3   Roll two 6-sided dice and add 3
        3d8-1   Roll three 8-sided dice and subtract 1
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            # Initialize manager with the session
            dice_manager = DiceManager(session=session)

            # If no scene_id is provided, try to get the current scene
            scene = resolve_scene_id(session, scene_id)
            if scene is None:
                if scene_id:
                    renderer.display_warning(f"Scene {scene_id} not found.")
                else:
                    renderer.display_warning("No current active scene found.")
                renderer.display_warning(
                    "Dice roll will not be associated with any scene."
                )

            scene_display_id = scene.id if scene else "N/A"
            logger.debug(
                f"Rolling dice: notation={notation}, reason={reason}, "
                f"scene_id={scene_display_id}"
            )

            result = dice_manager.roll(notation, reason, scene)
            renderer.display_dice_roll(result)

    except DiceError as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e


@dice_app.command("history")
def dice_history_command(
    ctx: typer.Context,
    limit: int = typer.Option(5, "--limit", "-l", help="Number of rolls to show"),
    scene_id: Optional[str] = typer.Option(
        None, "--scene-id", "-s", help="Filter by scene ID"
    ),
) -> None:
    """Show recent dice roll history.

    Args:
        ctx: Typer context.
        limit: Maximum number of rolls to display.
        scene_id: Optional ID of the scene to filter rolls by.
    """
    renderer: "Renderer" = ctx.obj["renderer"]
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            # Initialize manager with the session
            dice_manager = DiceManager(session=session)

            # If scene_id is not provided, try to get the active scene
            scene = resolve_scene_id(session, scene_id)

            # Call get_recent_rolls with the scene object (or None)
            rolls = dice_manager.get_recent_rolls(scene=scene, limit=limit)

            if not rolls:
                renderer.display_warning("No dice rolls found.")
                return

            renderer.display_message("Recent dice rolls:", style="bold")
            for roll in rolls:
                renderer.display_dice_roll(roll)
    except DiceError as e:
        renderer.display_error(f"Error: {str(e)}")
        raise typer.Exit(1) from e
