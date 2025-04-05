"""Test fixtures for CLI tests."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from sologm.models.dice import DiceRoll


@pytest.fixture
def cli_runner():
    """Create a CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_db_session_decorator():
    """Mock the with_db_session decorator to bypass database access.

    This is applied automatically to all tests in this directory.
    """
    with patch("sologm.cli.db_helpers.with_db_session", lambda f: f):
        yield


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_dice_manager():
    """Mock the DiceManager for testing."""
    with patch("sologm.cli.dice.DiceManager") as mock:
        # Configure the mock to return a predictable dice roll
        mock_instance = mock.return_value

        # Create a mock DiceRoll model
        mock_roll = DiceRoll(
            id="test-id",
            notation="2d6+3",
            individual_results=[4, 5],
            modifier=3,
            total=12,
            reason="Test roll",
        )
        # Add created_at attribute
        mock_roll.created_at = datetime.fromisoformat("2023-01-01T12:00:00")
        mock_instance.roll.return_value = mock_roll

        yield mock


@pytest.fixture
def mock_game_manager():
    """Mock the GameManager for testing."""
    with patch("sologm.cli.game.GameManager") as mock:
        yield mock


@pytest.fixture
def mock_scene_manager():
    """Mock the SceneManager for testing."""
    with patch("sologm.cli.scene.SceneManager") as mock:
        yield mock


@pytest.fixture
def mock_event_manager():
    """Mock the EventManager for testing."""
    with patch("sologm.cli.event.EventManager") as mock:
        yield mock


@pytest.fixture
def mock_oracle_manager():
    """Mock the OracleManager for testing."""
    with patch("sologm.cli.oracle.OracleManager") as mock:
        yield mock


@pytest.fixture
def sample_dice_roll():
    """Create a sample dice roll for testing."""
    roll = DiceRoll(
        id="test-id",
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
        total=12,
        reason="Test roll",
    )
    roll.created_at = datetime.fromisoformat("2023-01-01T12:00:00")
    return roll


@pytest.fixture
def sample_dice_rolls():
    """Create a list of sample dice rolls for testing."""
    mock_roll1 = DiceRoll(
        id="test-id-1",
        notation="1d20",
        individual_results=[15],
        modifier=0,
        total=15,
        reason="Attack roll",
    )
    mock_roll1.created_at = datetime.fromisoformat("2023-01-01T12:00:00")

    mock_roll2 = DiceRoll(
        id="test-id-2",
        notation="2d6+3",
        individual_results=[4, 5],
        modifier=3,
        total=12,
        reason="Damage roll",
    )
    mock_roll2.created_at = datetime.fromisoformat("2023-01-01T12:01:00")

    return [mock_roll1, mock_roll2]


@pytest.fixture
def mock_db_session():
    """Mock the database session for testing."""
    with patch("sologm.cli.db_helpers.get_db_context") as mock:
        mock_context = MagicMock()
        mock_session = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock.return_value = mock_context
        yield mock_session


@pytest.fixture
def cli_test_base():
    """Base fixture for CLI tests that provides common mocks and utilities."""

    class CLITestBase:
        @staticmethod
        def assert_success(result):
            """Assert that a CLI command executed successfully."""
            assert result.exit_code == 0

        @staticmethod
        def assert_error(result, expected_message=None):
            """Assert that a CLI command failed with an expected error message."""
            assert result.exit_code != 0
            if expected_message:
                assert expected_message in result.stdout

        @staticmethod
        def assert_output_contains(result, *expected_strings):
            """Assert that the command output contains all expected strings."""
            for expected in expected_strings:
                assert expected in result.stdout

    return CLITestBase()
