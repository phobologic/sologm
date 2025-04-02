"""Dice rolling commands for Solo RPG Helper."""
import logging
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional

from sologm.core.dice import roll_dice
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
        logger.debug(f"Rolling dice with notation: {notation}, reason: "
                     f"{reason}")
        result = roll_dice(notation, reason)

        logger.debug(f"Creating formatted output for roll result: {result}")
        # Create formatted output
        title = Text()
        if reason:
            title.append(f"{reason}: ", style="bold blue")
        title.append(result.notation, style="bold")

        details = Text()
        if len(result.individual_results) > 1:
            details.append("Rolls: ", style="dim")
            details.append(str(result.individual_results), style="cyan")
            details.append("\n")

        if result.modifier != 0:
            details.append("Modifier: ", style="dim")
            details.append(f"{result.modifier:+d}", style="yellow")
            details.append("\n")

        details.append("Result: ", style="dim")
        details.append(str(result.total), style="bold green")

        # Display in a panel
        panel = Panel(
            details,
            title=title,
            border_style="bright_black",
            expand=False
        )
        console.print(panel)

    except DiceError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1)
