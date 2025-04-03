"""Tests for dice rolling functionality."""

import pytest

from sologm.core.dice import DiceRoll, parse_dice_notation, roll_dice
from sologm.utils.errors import DiceError


class TestDiceRoll:
    """Tests for the DiceRoll class."""

    def test_dice_roll_creation(self) -> None:
        """Test creating a DiceRoll object."""
        roll = DiceRoll(
            notation="2d6+1",
            individual_results=[3, 4],
            modifier=1,
            total=8,
            reason="Test roll",
        )

        assert roll.notation == "2d6+1"
        assert roll.individual_results == [3, 4]
        assert roll.modifier == 1
        assert roll.total == 8
        assert roll.reason == "Test roll"


class TestDiceNotationParser:
    """Tests for dice notation parsing."""

    def test_parse_basic_notation(self) -> None:
        """Test parsing basic XdY notation."""
        count, sides, modifier = parse_dice_notation("2d6")
        assert count == 2
        assert sides == 6
        assert modifier == 0

    def test_parse_notation_with_positive_modifier(self) -> None:
        """Test parsing notation with positive modifier."""
        count, sides, modifier = parse_dice_notation("3d8+2")
        assert count == 3
        assert sides == 8
        assert modifier == 2

    def test_parse_notation_with_negative_modifier(self) -> None:
        """Test parsing notation with negative modifier."""
        count, sides, modifier = parse_dice_notation("4d10-3")
        assert count == 4
        assert sides == 10
        assert modifier == -3

    def test_parse_invalid_notation(self) -> None:
        """Test parsing invalid notation formats."""
        with pytest.raises(DiceError):
            parse_dice_notation("invalid")

        with pytest.raises(DiceError):
            parse_dice_notation("d20")

        with pytest.raises(DiceError):
            parse_dice_notation("20")

    def test_parse_invalid_dice_count(self) -> None:
        """Test parsing notation with invalid dice count."""
        with pytest.raises(DiceError):
            parse_dice_notation("0d6")

    def test_parse_invalid_sides(self) -> None:
        """Test parsing notation with invalid sides."""
        with pytest.raises(DiceError):
            parse_dice_notation("1d1")

        with pytest.raises(DiceError):
            parse_dice_notation("1d0")


class TestDiceRolling:
    """Tests for dice rolling functionality."""

    def test_roll_basic(self) -> None:
        """Test basic dice roll."""
        roll = roll_dice("1d6")

        assert roll.notation == "1d6"
        assert len(roll.individual_results) == 1
        assert 1 <= roll.individual_results[0] <= 6
        assert roll.modifier == 0
        assert roll.total == roll.individual_results[0]
        assert roll.reason is None

    def test_roll_multiple_dice(self) -> None:
        """Test rolling multiple dice."""
        roll = roll_dice("3d6")

        assert roll.notation == "3d6"
        assert len(roll.individual_results) == 3
        for result in roll.individual_results:
            assert 1 <= result <= 6
        assert roll.modifier == 0
        assert roll.total == sum(roll.individual_results)

    def test_roll_with_modifier(self) -> None:
        """Test rolling with modifier."""
        roll = roll_dice("2d4+3")

        assert roll.notation == "2d4+3"
        assert len(roll.individual_results) == 2
        for result in roll.individual_results:
            assert 1 <= result <= 4
        assert roll.modifier == 3
        assert roll.total == sum(roll.individual_results) + 3

    def test_roll_with_reason(self) -> None:
        """Test rolling with a reason."""
        roll = roll_dice("1d20", reason="Attack roll")

        assert roll.notation == "1d20"
        assert len(roll.individual_results) == 1
        assert 1 <= roll.individual_results[0] <= 20
        assert roll.reason == "Attack roll"

    def test_roll_invalid_notation(self) -> None:
        """Test rolling with invalid notation."""
        with pytest.raises(DiceError):
            roll_dice("invalid")
