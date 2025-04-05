"""Integration tests for dice CLI commands."""

import pytest
from sologm.cli.dice import dice_app
from sologm.models.dice import DiceRoll


def test_roll_dice_command(cli_runner, mock_dice_manager, mock_session, cli_test_base):
    """Test the roll dice command."""
    # Run the command
    result = cli_runner.invoke(dice_app, ["roll", "2d6+3", "--reason", "Test roll"])

    # Verify results
    cli_test_base.assert_success(result)

    # Verify the dice manager was called correctly
    mock_instance = mock_dice_manager.return_value
    mock_instance.roll.assert_called_once_with("2d6+3", "Test roll", None)

    # Verify the output contains the expected information
    cli_test_base.assert_output_contains(result, "2d6+3", "Test roll")


def test_dice_history_command(
    cli_runner, mock_dice_manager, sample_dice_rolls, mock_session, cli_test_base
):
    """Test the dice history command."""
    # Configure the mock to return a list of dice rolls
    mock_instance = mock_dice_manager.return_value
    mock_instance.get_recent_rolls.return_value = sample_dice_rolls

    # Run the command
    result = cli_runner.invoke(dice_app, ["history", "--limit", "2"])

    # Verify results
    cli_test_base.assert_success(result)

    # Verify the dice manager was called correctly
    mock_instance.get_recent_rolls.assert_called_once_with(scene_id=None, limit=2)

    # Verify the output contains information about both dice rolls
    cli_test_base.assert_output_contains(
        result, "1d20", "Attack roll", "2d6+3", "Damage roll"
    )


@pytest.mark.parametrize(
    "args,expected_output,expected_notation,expected_reason",
    [
        (["roll", "1d20"], "1d20", "1d20", None),
        (["roll", "2d6+3", "--reason", "Test"], "Test", "2d6+3", "Test"),
        (
            ["roll", "3d8-1", "--reason", "Skill check"],
            "Skill check",
            "3d8-1",
            "Skill check",
        ),
    ],
)
def test_dice_roll_variations(
    cli_runner,
    mock_dice_manager,
    mock_session,
    cli_test_base,
    args,
    expected_output,
    expected_notation,
    expected_reason,
):
    """Test various dice roll command variations."""
    # Run the command
    result = cli_runner.invoke(dice_app, args)

    # Verify results
    cli_test_base.assert_success(result)
    cli_test_base.assert_output_contains(result, expected_output)

    # Verify the dice manager was called correctly
    mock_instance = mock_dice_manager.return_value
    mock_instance.roll.assert_called_once_with(expected_notation, expected_reason, None)


def test_dice_roll_error_handling(
    cli_runner, mock_dice_manager, mock_session, cli_test_base
):
    """Test error handling in the dice roll command."""
    # Configure the mock to raise an error
    mock_instance = mock_dice_manager.return_value
    from sologm.utils.errors import DiceError

    mock_instance.roll.side_effect = DiceError("Invalid dice notation")

    # Run the command
    result = cli_runner.invoke(dice_app, ["roll", "invalid"])

    # Verify the error is handled properly
    cli_test_base.assert_error(result, "Invalid dice notation")
