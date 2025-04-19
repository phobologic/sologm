"""
Unit tests for the MarkdownRenderer class.
"""

from unittest.mock import MagicMock

import pytest
from rich.console import Console  # <-- Import Console

# Import the renderer and models needed for tests
# Import the renderer and models needed for tests
from sologm.cli.rendering.markdown_renderer import MarkdownRenderer
from sologm.models.dice import DiceRoll
from sologm.models.oracle import Interpretation  # <-- Added import


# Fixture for mock console (can be shared or defined here)
@pytest.fixture
def mock_console() -> MagicMock:
    """Fixture for a mocked Rich Console."""
    console = MagicMock(spec=Console)
    # Set a default width if needed for truncation tests later
    console.width = 100
    return console


# --- Test for display_dice_roll ---


def test_display_dice_roll_markdown(mock_console: MagicMock, test_dice_roll: DiceRoll):
    """Test displaying a dice roll as Markdown."""
    renderer = MarkdownRenderer(mock_console)

    # Modify the test dice roll for a more complete test case
    test_dice_roll.notation = "2d6+1"
    test_dice_roll.individual_results = [4, 3]
    test_dice_roll.modifier = 1
    test_dice_roll.total = 8
    test_dice_roll.reason = "Test Roll"

    renderer.display_dice_roll(test_dice_roll)

    # Define the expected Markdown output
    expected_output = (
        "### Dice Roll: 2d6+1 (Reason: Test Roll)\n\n"
        "*   **Result:** `8`\n"
        "*   Rolls: `[4, 3]`\n"
        "*   Modifier: `+1`"
    )

    # Assert that console.print was called with the expected string
    # Using assert_called_once_with checks for exact match including newlines
    mock_console.print.assert_called_once_with(expected_output)


# --- Test for display_interpretation ---


def test_display_interpretation_markdown(
    mock_console: MagicMock, test_interpretations: list[Interpretation]
):
    """Test displaying a single interpretation as Markdown."""
    renderer = MarkdownRenderer(mock_console)
    interp = test_interpretations[0]  # Assuming fixture provides at least one

    # Test case 1: Basic interpretation
    renderer.display_interpretation(interp)
    expected_output_basic = (
        f"#### {interp.title}\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_basic)
    mock_console.reset_mock()

    # Test case 2: Selected interpretation with sequence
    renderer.display_interpretation(interp, selected=True, sequence=1)
    expected_output_selected = (
        f"#### Interpretation #1: {interp.title} (**Selected**)\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_selected)
    mock_console.reset_mock()

    # Test case 3: Interpretation with sequence but not selected
    renderer.display_interpretation(interp, selected=False, sequence=2)
    expected_output_sequence = (
        f"#### Interpretation #2: {interp.title}\n\n"
        f"{interp.description}\n\n"
        f"*ID: {interp.id} / {interp.slug}*"
    )
    mock_console.print.assert_called_with(expected_output_sequence)


# --- Add other tests below ---
