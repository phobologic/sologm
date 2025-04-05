"""Integration tests for dice CLI commands."""

from typer.testing import CliRunner
import pytest
from unittest.mock import patch

from sologm.cli.app import app
from sologm.core.dice import DiceManager, DiceRoll

runner = CliRunner()

@pytest.fixture
def mock_dice_manager():
    """Mock the DiceManager for testing."""
    with patch('sologm.cli.dice.DiceManager') as mock:
        # Configure the mock to return a predictable dice roll
        mock_instance = mock.return_value
        mock_instance.roll.return_value = DiceRoll(
            id="test-id",
            notation="2d6+3",
            individual_results=[4, 5],
            modifier=3,
            total=12,
            reason="Test roll",
            created_at="2023-01-01T12:00:00"
        )
        yield mock

def test_roll_dice_command(mock_dice_manager):
    """Test the roll dice command."""
    result = runner.invoke(app, ["dice", "roll", "2d6+3", "--reason", "Test roll"])
    
    # Verify the command ran successfully
    assert result.exit_code == 0
    
    # Verify the dice manager was called correctly
    mock_instance = mock_dice_manager.return_value
    mock_instance.roll.assert_called_once_with("2d6+3", "Test roll", None)
    
    # Verify the output contains the expected information
    assert "2d6+3" in result.stdout
    assert "Test roll" in result.stdout

def test_dice_history_command(mock_dice_manager):
    """Test the dice history command."""
    # Configure the mock to return a list of dice rolls
    mock_instance = mock_dice_manager.return_value
    mock_instance.get_recent_rolls.return_value = [
        DiceRoll(
            id="test-id-1",
            notation="1d20",
            individual_results=[15],
            modifier=0,
            total=15,
            reason="Attack roll",
            created_at="2023-01-01T12:00:00"
        ),
        DiceRoll(
            id="test-id-2",
            notation="2d6+3",
            individual_results=[4, 5],
            modifier=3,
            total=12,
            reason="Damage roll",
            created_at="2023-01-01T12:01:00"
        )
    ]
    
    result = runner.invoke(app, ["dice", "history", "--limit", "2"])
    
    # Verify the command ran successfully
    assert result.exit_code == 0
    
    # Verify the dice manager was called correctly
    mock_instance.get_recent_rolls.assert_called_once_with(scene_id=None, limit=2)
    
    # Verify the output contains information about both dice rolls
    assert "1d20" in result.stdout
    assert "Attack roll" in result.stdout
    assert "2d6+3" in result.stdout
    assert "Damage roll" in result.stdout
