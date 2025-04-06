"""Main Typer app for Solo RPG Helper."""

import typer
from rich.console import Console

# Create Typer app
app = typer.Typer(
    name="sologm",
    help="Solo RPG Helper command-line application",
    add_completion=True,
    no_args_is_help=True,
)

# Create console for rich output
console = Console()
