"""Integration tests for dice CLI commands."""

import pytest
from unittest.mock import patch
from sologm.cli.dice import dice_app
from sologm.models.dice import DiceRoll


def test_roll_dice_command(cli_runner, mock_dice_manager, mock_session, cli_test_base):
    """Test the roll dice command."""
    # Setup mock return value
    mock_instance = mock_dice_manager.return_value
    mock_roll = DiceRoll.create(
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
        total=12,
        reason="Test roll",
    )
    mock_instance.roll.return_value = mock_roll

    # Run the command
    result = cli_runner.invoke(dice_app, ["roll", "2d6+3", "--reason", "Test roll"])

    # Verify results
    cli_test_base.assert_success(result)

    # Verify the dice manager was called correctly
    mock_instance.roll.assert_called_once_with("2d6+3", "Test roll", None)


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
    "args,expected_notation,expected_reason,expected_scene_id",
    [
        (["roll", "1d20"], "1d20", None, None),
        (["roll", "2d6+3", "--reason", "Test"], "2d6+3", "Test", None),
        (["roll", "3d8-1", "--reason", "Skill check"], "3d8-1", "Skill check", None),
        (["roll", "1d6", "--scene-id", "scene123"], "1d6", None, "scene123"),
        (
            ["roll", "1d6", "--reason", "Test", "--scene-id", "scene123"],
            "1d6",
            "Test",
            "scene123",
        ),
    ],
)
def test_dice_roll_variations(
    cli_runner,
    mock_dice_manager,
    mock_session,
    cli_test_base,
    args,
    expected_notation,
    expected_reason,
    expected_scene_id,
):
    """Test various dice roll command variations."""
    # Setup mock
    mock_instance = mock_dice_manager.return_value
    mock_roll = DiceRoll.create(
        notation=expected_notation,
        individual_results=[4],
        modifier=0,
        total=4,
        reason=expected_reason,
        scene_id=expected_scene_id,
    )
    mock_instance.roll.return_value = mock_roll

    # Run the command
    result = cli_runner.invoke(dice_app, args)

    # Verify results
    cli_test_base.assert_success(result)

    # Verify the dice manager was called correctly
    mock_instance.roll.assert_called_once_with(
        expected_notation, expected_reason, expected_scene_id
    )


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
    assert "Error: Invalid dice notation" in result.stdout
    assert result.exit_code == 1


def test_dice_history_empty_results(
    cli_runner, mock_dice_manager, mock_session, cli_test_base
):
    """Test dice history command when no rolls are found."""
    # Configure the mock to return an empty list
    mock_instance = mock_dice_manager.return_value
    mock_instance.get_recent_rolls.return_value = []

    # Run the command
    result = cli_runner.invoke(dice_app, ["history"])

    # Verify results
    cli_test_base.assert_success(result)
    cli_test_base.assert_output_contains(result, "No dice rolls found.")
