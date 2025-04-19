"""Tests for the RichRenderer class."""

# Add necessary imports
import pytest
from unittest.mock import MagicMock
from rich.console import Console
from rich.panel import Panel # Import Panel for assertion

from sologm.cli.rendering.rich_renderer import RichRenderer
from sologm.models.dice import DiceRoll # Assuming you have a fixture for test_dice_roll

# Add mock_console fixture if not already present globally
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width for consistent testing if needed
    console.width = 100
    return console

# --- Adapted Test (Red Phase - Expecting Failure) ---
def test_display_dice_roll(mock_console: MagicMock, test_dice_roll: DiceRoll):
    """Test displaying a dice roll using RichRenderer."""
    renderer = RichRenderer(mock_console)
    # This call will raise NotImplementedError initially, causing the test to fail.
    renderer.display_dice_roll(test_dice_roll)

    # This assertion will only be reached once the implementation is added (Green Phase).
    mock_console.print.assert_called()
    # Verify that a Panel object was printed
    args, kwargs = mock_console.print.call_args
    assert len(args) == 1
    assert isinstance(args[0], Panel)


# --- Add other tests below ---
