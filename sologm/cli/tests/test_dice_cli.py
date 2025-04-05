"""Tests for the dice CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from datetime import datetime

from sologm.cli.dice import dice_app
from sologm.models.dice import DiceRoll
from sologm.utils.errors import DiceError


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    # Setting mix_stderr=True can help with file closure issues
    return CliRunner(mix_stderr=True)


@pytest.fixture
def mock_dice_manager():
    """Create a mock DiceManager for testing."""
    with patch("sologm.cli.dice.DiceManager") as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def sample_dice_roll():
    """Create a sample dice roll for testing."""
    # Create a mock DiceRoll instead of trying to instantiate the actual model
    mock_roll = MagicMock(spec=DiceRoll)
    mock_roll.id = "dice_123"
    mock_roll.notation = "2d6+3"
    mock_roll.individual_results = [4, 5]
    mock_roll.modifier = 3
    mock_roll.total = 12
    mock_roll.reason = "Test roll"
    mock_roll.scene_id = "scene_123"
    mock_roll.created_at = datetime.fromisoformat("2023-01-01T12:00:00")

    return mock_roll


class TestRollDiceCommand:
    """Tests for the roll dice command."""

    def test_roll_dice_success(self, runner, mock_dice_manager, sample_dice_roll):
        """Test successful dice roll."""
        # Setup the mock to return our sample dice roll
        mock_dice_manager.roll.return_value = sample_dice_roll

        # Create a fresh runner for each test to avoid file closure issues
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command with isolated_filesystem to avoid file closure issues
        with fresh_runner.isolated_filesystem():
            result = fresh_runner.invoke(
                dice_app,
                ["roll", "2d6+3", "--reason", "Test roll", "--scene-id", "scene_123"],
            )

            # Verify the command executed successfully
            assert result.exit_code == 0
            
            # Verify the manager was called with correct parameters
            mock_dice_manager.roll.assert_called_once_with(
                "2d6+3", "Test roll", "scene_123"
            )
            
            # Verify output contains expected information
            assert "2d6+3" in result.stdout
            assert "Total: 12" in result.stdout

    def test_roll_dice_minimal_args(self, runner, mock_dice_manager, sample_dice_roll):
        """Test dice roll with only required arguments."""
        # Setup the mock
        mock_dice_manager.roll.return_value = sample_dice_roll

        # Create a fresh runner for each test
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command with only the notation
        with fresh_runner.isolated_filesystem():
            result = fresh_runner.invoke(dice_app, ["roll", "2d6+3"])

            # Verify success
            assert result.exit_code == 0
            
            # Verify the manager was called with correct parameters
            mock_dice_manager.roll.assert_called_once_with("2d6+3", None, None)

    def test_roll_dice_error(self, runner, mock_dice_manager):
        """Test handling of errors during dice roll."""
        # Setup the mock to raise an error
        mock_dice_manager.roll.side_effect = DiceError("Invalid dice notation")

        # Create a fresh runner
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command with isolated_filesystem
        with fresh_runner.isolated_filesystem():
            # We'll keep catch_exceptions=True to properly capture the output
            result = fresh_runner.invoke(dice_app, ["roll", "invalid"])

            # Verify the command failed with the expected error
            assert result.exit_code == 1
            assert "Error: Invalid dice notation" in result.stdout


class TestDiceHistoryCommand:
    """Tests for the dice history command."""

    def test_history_with_results(self, runner, mock_dice_manager, sample_dice_roll):
        """Test dice history command when there are results."""
        # Setup the mock to return a list of dice rolls
        mock_dice_manager.get_recent_rolls.return_value = [sample_dice_roll]

        # Create a fresh runner
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command
        with fresh_runner.isolated_filesystem():
            result = fresh_runner.invoke(
                dice_app, ["history", "--limit", "5", "--scene-id", "scene_123"]
            )

            # Verify success
            assert result.exit_code == 0
            
            # Verify the manager was called with correct parameters
            mock_dice_manager.get_recent_rolls.assert_called_once_with(
                scene_id="scene_123", limit=5
            )
            
            # Verify output contains expected information
            assert "Recent dice rolls:" in result.stdout
            assert "2d6+3" in result.stdout
            assert "Total: 12" in result.stdout

    def test_history_no_results(self, runner, mock_dice_manager):
        """Test dice history command when there are no results."""
        # Setup the mock to return an empty list
        mock_dice_manager.get_recent_rolls.return_value = []

        # Create a fresh runner
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command
        with fresh_runner.isolated_filesystem():
            result = fresh_runner.invoke(dice_app, ["history"])

            # Verify success
            assert result.exit_code == 0
            
            # Verify the manager was called with default parameters
            mock_dice_manager.get_recent_rolls.assert_called_once_with(
                scene_id=None, limit=5
            )
            
            # Verify output contains expected message
            assert "No dice rolls found." in result.stdout

    def test_history_error(self, runner, mock_dice_manager):
        """Test handling of errors during history retrieval."""
        # Setup the mock to raise an error
        mock_dice_manager.get_recent_rolls.side_effect = DiceError("Database error")

        # Create a fresh runner
        fresh_runner = CliRunner(mix_stderr=True)
        
        # Run the command
        with fresh_runner.isolated_filesystem():
            result = fresh_runner.invoke(dice_app, ["history"])

            # Verify the command failed with the expected error
            assert result.exit_code == 1
            assert "Error: Database error" in result.stdout
