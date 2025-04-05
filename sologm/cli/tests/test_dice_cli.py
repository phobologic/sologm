"""Integration tests for dice CLI commands."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sologm.cli.dice import dice_app
from sologm.models.dice import DiceRoll


def test_roll_dice_command(cli_runner, mock_dice_manager):
    """Test the roll dice command."""
    result = cli_runner.invoke(dice_app, ["roll", "2d6+3", "--reason", "Test roll"])

    # Verify the command ran successfully
    assert result.exit_code == 0

    # Verify the dice manager was called correctly
    mock_instance = mock_dice_manager.return_value
    mock_instance.roll.assert_called_once_with("2d6+3", "Test roll", None)

    # Verify the output contains the expected information
    assert "2d6+3" in result.stdout
    assert "Test roll" in result.stdout


def test_dice_history_command(cli_runner, mock_dice_manager, sample_dice_rolls):
    """Test the dice history command."""
    # Configure the mock to return a list of dice rolls
    mock_instance = mock_dice_manager.return_value
    mock_instance.get_recent_rolls.return_value = sample_dice_rolls

    result = cli_runner.invoke(dice_app, ["history", "--limit", "2"])

    # Verify the command ran successfully
    assert result.exit_code == 0

    # Verify the dice manager was called correctly
    mock_instance.get_recent_rolls.assert_called_once_with(scene_id=None, limit=2)

    # Verify the output contains information about both dice rolls
    assert "1d20" in result.stdout
    assert "Attack roll" in result.stdout
    assert "2d6+3" in result.stdout
    assert "Damage roll" in result.stdout


@pytest.mark.parametrize(
    "args,expected_output,expected_notation,expected_reason",
    [
        (["roll", "1d20"], "1d20", "1d20", None),
        (["roll", "2d6+3", "--reason", "Test"], "Test", "2d6+3", "Test"),
        (["roll", "3d8-1", "--reason", "Skill check"], "Skill check", "3d8-1", "Skill check"),
    ],
)
def test_dice_roll_variations(
    cli_runner, mock_dice_manager, args, expected_output, expected_notation, expected_reason
):
    """Test various dice roll command variations."""
    result = cli_runner.invoke(dice_app, args)
    
    assert result.exit_code == 0
    assert expected_output in result.stdout
    
    mock_instance = mock_dice_manager.return_value
    mock_instance.roll.assert_called_once_with(expected_notation, expected_reason, None)
