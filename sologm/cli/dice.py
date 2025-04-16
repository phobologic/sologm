"""Dice rolling commands for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console
from sqlalchemy.orm import Session

from sologm.cli.utils import display
from sologm.core.dice import DiceManager
from sologm.database.session import get_db_context
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError, SceneError

logger = logging.getLogger(__name__)
dice_app = typer.Typer(help="Dice rolling commands")
console = Console()


def resolve_scene_id(session: Session, scene_id: Optional[str]) -> Optional[Scene]:
    """Resolve scene ID from active context if not provided.

    Args:
        session: Database session
        scene_id: Optional scene ID provided by user

    Returns:
        Resolved Scene or None if not resolvable. Default to using the current
        scene if no scene_id is passed in.
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
    notation: str = typer.Argument(..., help="Dice notation (e.g., 2d6+3)"),
    reason: Optional[str] = typer.Option(
        None, "--reason", "-r", help="Reason for the roll"
    ),
    scene_id: Optional[str] = typer.Option(
        None, "--scene-id", "-s", help="ID of the scene for this roll"
    ),
) -> None:
    """Roll dice using standard notation (XdY+Z).

    Examples:
        1d20    Roll a single 20-sided die
        2d6+3   Roll two 6-sided dice and add 3
        3d8-1   Roll three 8-sided dice and subtract 1
    """
    try:
        # Use a single session for the entire command
        with get_db_context() as session:
            # Initialize manager with the session
            dice_manager = DiceManager(session=session)

            # If no scene_id is provided, try to get the current scene
            scene = resolve_scene_id(session, scene_id)
        if scene is None:
            if scene_id:
                console.print(f"Scene {scene_id} not found.", style="yellow")
            else:
                console.print("No current active scene found.", style="yellow")
            console.print(
                "Dice roll will not be associated with any scene.", style="yellow"
            )

        logger.debug(
            f'Rolling dice with notation: {notation}, reason: '
            f'{reason}, scene_id: {scene.id if scene else "NA"}'
        )

        result = dice_manager.roll(notation, reason, scene)
        display.display_dice_roll(console, result)

    except DiceError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1) from e


@dice_app.command("history")
def dice_history_command(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of rolls to show"),
    scene_id: Optional[str] = typer.Option(
        None, "--scene-id", "-s", help="Filter by scene ID"
    ),
) -> None:
    """Show recent dice roll history."""
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
            console.print("No dice rolls found.", style="yellow")
            return

        console.print("Recent dice rolls:", style="bold")
        for roll in rolls:
            display.display_dice_roll(console, roll)

    except DiceError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1) from e
