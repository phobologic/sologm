"""Dice rolling commands for Solo RPG Helper."""

import logging
from typing import Optional

import typer
from rich.console import Console

from sologm.cli import display
from sologm.core.dice import DiceManager
from sologm.utils.errors import DiceError

logger = logging.getLogger(__name__)
dice_app = typer.Typer(help="Dice rolling commands")
console = Console()


@dice_app.command("roll")
def roll_dice_command(
    notation: str = typer.Argument(..., help="Dice notation (e.g., 2d6+3)"),
    reason: Optional[str] = typer.Option(
        None, "--reason", "-r", help="Reason for the roll"
    ),
) -> None:
    """Roll dice using standard notation (XdY+Z).

    Examples:
        1d20    Roll a single 20-sided die
        2d6+3   Roll two 6-sided dice and add 3
        3d8-1   Roll three 8-sided dice and subtract 1
    """
    try:
        logger.debug(f"Rolling dice with notation: {notation}, reason: {reason}")
        manager = DiceManager()
        result = manager.roll(notation, reason)
        display.display_dice_roll(console, result)

    except DiceError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1) from e
