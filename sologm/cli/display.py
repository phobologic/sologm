"""Display helpers for CLI output."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from sologm.core.dice import DiceRoll
from sologm.core.oracle import Interpretation, InterpretationSet


def display_dice_roll(console: Console, roll: DiceRoll) -> None:
    """Display a dice roll result.

    Args:
        console: Rich console instance
        roll: DiceRoll to display
    """
    title = Text()
    if roll.reason:
        title.append(f"{roll.reason}: ", style="bold blue")
    title.append(roll.notation, style="bold")

    details = Text()
    if len(roll.individual_results) > 1:
        details.append("Rolls: ", style="dim")
        details.append(str(roll.individual_results), style="cyan")
        details.append("\n")

    if roll.modifier != 0:
        details.append("Modifier: ", style="dim")
        details.append(f"{roll.modifier:+d}", style="yellow")
        details.append("\n")

    details.append("Result: ", style="dim")
    details.append(str(roll.total), style="bold green")

    panel = Panel(details, title=title, border_style="bright_black", expand=False)
    console.print(panel)


def display_interpretation(
    console: Console, interp: Interpretation, selected: bool = False
) -> None:
    """Display a single interpretation.

    Args:
        console: Rich console instance
        interp: Interpretation to display
        selected: Whether this interpretation is selected
    """
    selected_text = "[green](Selected)[/green] " if selected else ""
    panel = Panel(
        Text.from_markup(f"[bold]{interp.title}[/bold]\n\n{interp.description}"),
        title=f"Interpretation [dim][{interp.id}][/dim] {selected_text}",
        border_style="blue",
    )
    console.print(panel)
    console.print()


def display_interpretation_set(
    console: Console,
    interp_set: InterpretationSet,
    show_context: bool = True,
) -> None:
    """Display a full interpretation set.

    Args:
        console: Rich console instance
        interp_set: InterpretationSet to display
        show_context: Whether to show context information
    """
    if show_context:
        console.print("\n[bold]Oracle Interpretations[/bold]")
        console.print(f"Context: {interp_set.context}")
        console.print(f"Results: {interp_set.oracle_results}\n")

    for i, interp in enumerate(interp_set.interpretations, 1):
        selected = interp_set.selected_interpretation == i - 1
        display_interpretation(console, interp, selected)

    console.print(
        f"\nInterpretation set ID: [bold]{interp_set.id}[/bold] "
        "(use this ID to select an interpretation)"
    )
