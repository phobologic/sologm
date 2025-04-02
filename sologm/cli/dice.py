"""Dice rolling commands for Solo RPG Helper."""

from typing import Optional

import typer
from rich.console import Console

from sologm.cli.main import app, handle_errors

# Create dice subcommand
dice_app = typer.Typer(help="Dice rolling commands")
app.add_typer(dice_app, name="dice")

# Create console for rich output
console = Console()


@dice_app.command("roll")
@handle_errors
def roll_dice(
    notation: str = typer.Argument(..., help="Dice notation (e.g., 2d6+3)"),
    reason: Optional[str] = typer.Option(
        None, "--reason", "-r", help="Reason for the roll"
    ),
) -> None:
    """Roll dice using standard notation."""
    console.print("[bold]Dice Roll:[/]")
    if reason:
        console.print(f"Reason: {reason}")
    console.print(f"Notation: {notation}")
    console.print(
        "[yellow]This is a placeholder. Dice rolling will be implemented later.[/]"
    )
