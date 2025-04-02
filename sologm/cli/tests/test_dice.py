"""Tests for dice CLI commands."""

from typer.testing import CliRunner
from rich.console import Console

from sologm.cli.main import app

runner = CliRunner()
console = Console()

def test_roll_basic():
    """Test basic dice roll command."""
    result = runner.invoke(app, ["dice", "roll", "1d20"])
    assert result.exit_code == 0
    assert "1d20" in result.stdout
    assert "Result:" in result.stdout

def test_roll_with_reason():
    """Test dice roll with reason."""
    result = runner.invoke(app, ["dice", "roll", "2d6", "--reason", "Attack roll"])
    assert result.exit_code == 0
    assert "2d6" in result.stdout
    assert "Attack roll" in result.stdout

def test_roll_with_modifier():
    """Test dice roll with modifier."""
    result = runner.invoke(app, ["dice", "roll", "3d8+2"])
    assert result.exit_code == 0
    assert "3d8+2" in result.stdout
    assert "Modifier: +2" in result.stdout

def test_roll_invalid_notation():
    """Test dice roll with invalid notation."""
    result = runner.invoke(app, ["dice", "roll", "invalid"])
    assert result.exit_code == 1
    assert "Error" in result.stdout
