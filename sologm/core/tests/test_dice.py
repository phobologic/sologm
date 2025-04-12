"""Tests for dice rolling functionality."""

import logging

import pytest

from sologm.models.dice import DiceRoll as DiceRollModel
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError


class TestDiceManager:
    """Tests for the DiceManager class."""

    def test_parse_basic_notation(self, dice_manager) -> None:
        """Test parsing basic XdY notation."""
        count, sides, modifier = dice_manager._parse_notation("2d6")
        assert count == 2
        assert sides == 6
        assert modifier == 0

    def test_parse_notation_with_positive_modifier(self, dice_manager) -> None:
        """Test parsing notation with positive modifier."""
        count, sides, modifier = dice_manager._parse_notation("3d8+2")
        assert count == 3
        assert sides == 8
        assert modifier == 2

    def test_parse_notation_with_negative_modifier(self, dice_manager) -> None:
        """Test parsing notation with negative modifier."""
        count, sides, modifier = dice_manager._parse_notation("4d10-3")
        assert count == 4
        assert sides == 10
        assert modifier == -3

    def test_parse_invalid_notation(self, dice_manager) -> None:
        """Test parsing invalid notation formats."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("invalid")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("d20")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("20")

    def test_parse_invalid_dice_count(self, dice_manager) -> None:
        """Test parsing notation with invalid dice count."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("0d6")

    def test_parse_invalid_sides(self, dice_manager) -> None:
        """Test parsing notation with invalid sides."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("1d1")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("1d0")

    def test_roll_basic(self, dice_manager, db_session) -> None:
        """Test basic dice roll."""
        roll = dice_manager.roll("1d6")

        assert roll.notation == "1d6"
        assert len(roll.individual_results) == 1
        assert 1 <= roll.individual_results[0] <= 6
        assert roll.modifier == 0
        assert roll.total == roll.individual_results[0]
        assert roll.reason is None

        # Verify it's in the database
        db_roll = (
            db_session.query(DiceRollModel).filter(DiceRollModel.id == roll.id).first()
        )
        assert db_roll is not None
        assert db_roll.notation == "1d6"
        assert len(db_roll.individual_results) == 1
        assert db_roll.total == roll.total

    def test_roll_multiple_dice(self, dice_manager) -> None:
        """Test rolling multiple dice."""
        roll = dice_manager.roll("3d6")

        assert roll.notation == "3d6"
        assert len(roll.individual_results) == 3
        for result in roll.individual_results:
            assert 1 <= result <= 6
        assert roll.modifier == 0
        assert roll.total == sum(roll.individual_results)

    def test_roll_with_modifier(self, dice_manager) -> None:
        """Test rolling with modifier."""
        roll = dice_manager.roll("2d4+3")

        assert roll.notation == "2d4+3"
        assert len(roll.individual_results) == 2
        for result in roll.individual_results:
            assert 1 <= result <= 4
        assert roll.modifier == 3
        assert roll.total == sum(roll.individual_results) + 3

    def test_roll_with_reason(self, dice_manager) -> None:
        """Test rolling with a reason."""
        roll = dice_manager.roll("1d20", reason="Attack roll")

        assert roll.notation == "1d20"
        assert len(roll.individual_results) == 1
        assert 1 <= roll.individual_results[0] <= 20
        assert roll.reason == "Attack roll"

    def test_roll_with_scene(self, dice_manager, db_session, test_scene) -> None:
        """Test rolling with a scene object."""
        roll = dice_manager.roll("1d20", scene=test_scene)

        assert roll.scene_id == test_scene.id

        # Verify it's in the database with the scene ID
        db_roll = (
            db_session.query(DiceRollModel).filter(DiceRollModel.id == roll.id).first()
        )
        assert db_roll is not None
        assert db_roll.scene_id == test_scene.id

    def test_get_recent_rolls(self, dice_manager) -> None:
        """Test getting recent rolls."""
        # Create some rolls
        dice_manager.roll("1d20", reason="Roll 1")
        dice_manager.roll("2d6", reason="Roll 2")
        dice_manager.roll("3d8", reason="Roll 3")

        # Get recent rolls
        rolls = dice_manager.get_recent_rolls(limit=2)

        # Verify we got the most recent 2 rolls
        assert len(rolls) == 2
        assert rolls[0].reason == "Roll 3"  # Most recent first
        assert rolls[1].reason == "Roll 2"

    def test_get_recent_rolls_by_scene(self, dice_manager, test_scene) -> None:
        """Test getting recent rolls filtered by scene."""
        # Create a mock scene for "other-scene"
        other_scene = Scene(id="other-scene", title="Other Scene")

        # Create some rolls with different scene objects
        dice_manager.roll("1d20", reason="Roll 1", scene=other_scene)
        dice_manager.roll("2d6", reason="Roll 2", scene=test_scene)
        dice_manager.roll("3d8", reason="Roll 3", scene=test_scene)

        # Get recent rolls for the specific scene
        rolls = dice_manager.get_recent_rolls(scene=test_scene)

        # Verify we got only rolls for the specified scene
        assert len(rolls) == 2
        assert all(roll.scene_id == test_scene.id for roll in rolls)
        assert rolls[0].reason == "Roll 3"  # Most recent first
        assert rolls[1].reason == "Roll 2"

    def test_dice_roll_randomness(self, dice_manager):
        """Test that dice rolls produce random results within expected range."""
        # Roll a large number of d6
        results = []
        for _ in range(100):
            roll = dice_manager.roll("1d6")
            results.append(roll.individual_results[0])

        # Check we get a good distribution
        assert min(results) == 1
        assert max(results) == 6
        # Check we get at least one of each number (very unlikely to fail)
        assert set(range(1, 7)).issubset(set(results))

    @pytest.mark.parametrize(
        "notation,expected",
        [
            ("2d6", (2, 6, 0)),
            ("3d8+2", (3, 8, 2)),
            ("4d10-3", (4, 10, -3)),
        ],
    )
    def test_parse_notation_parametrized(self, dice_manager, notation, expected):
        """Test parsing various dice notations."""
        count, sides, modifier = dice_manager._parse_notation(notation)
        assert (count, sides, modifier) == expected

    def test_execute_db_operation(self, dice_manager):
        """Test the _execute_db_operation method."""

        def _test_operation(session):
            return "success"

        result = dice_manager._execute_db_operation("test operation", _test_operation)
        assert result == "success"

    def test_execute_db_operation_error(self, dice_manager):
        """Test error handling in _execute_db_operation."""

        def _test_operation(session):
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc:
            dice_manager._execute_db_operation("test operation", _test_operation)
        assert "Test error" in str(exc.value)

    def test_logging_functionality(self, dice_manager, caplog):
        """Test that enhanced logging is working properly."""
        caplog.set_level(logging.DEBUG)

        # Test logging in roll method
        roll = dice_manager.roll("2d6+3")

        # Check for expected log messages
        assert "Rolling dice with notation: 2d6+3" in caplog.text
        assert "Parsed notation: 2d6+3" in caplog.text
        assert "Individual dice results:" in caplog.text
        assert "Final result:" in caplog.text
        assert "Created dice roll with ID:" in caplog.text

    def test_roll_for_active_scene(
        self, dice_manager, scene_manager, test_scene, monkeypatch
    ):
        """Test rolling dice for the active scene."""

        # Mock validate_active_context to return our test scene
        def mock_validate_active_context():
            return "test_act_id", test_scene

        monkeypatch.setattr(
            scene_manager, "validate_active_context", mock_validate_active_context
        )
        monkeypatch.setattr(dice_manager, "scene_manager", scene_manager)

        # Roll dice for active scene
        roll = dice_manager.roll_for_active_scene("1d20", "Test roll")

        assert roll.notation == "1d20"
        assert roll.scene_id == test_scene.id
        assert roll.reason == "Test roll"

    def test_get_rolls_for_scene(self, dice_manager, test_scene):
        """Test getting rolls for a specific scene."""
        # Create a different scene
        different_scene = Scene(id="different-scene-id", title="Different Scene")

        # Create some rolls for the test scene
        dice_manager.roll("1d6", "Roll 1", test_scene)
        dice_manager.roll("2d8", "Roll 2", test_scene)

        # Create a roll for a different scene
        dice_manager.roll("3d10", "Roll 3", different_scene)

        # Get rolls for the test scene
        rolls = dice_manager.get_rolls_for_scene(test_scene)

        assert len(rolls) == 2
        assert all(roll.scene_id == test_scene.id for roll in rolls)
        assert rolls[0].reason == "Roll 2"  # Most recent first
        assert rolls[1].reason == "Roll 1"

    def test_get_rolls_for_active_scene(
        self, dice_manager, scene_manager, test_scene, monkeypatch
    ):
        """Test getting rolls for the active scene."""

        # Mock validate_active_context to return our test scene
        def mock_validate_active_context():
            return "test_act_id", test_scene

        monkeypatch.setattr(
            scene_manager, "validate_active_context", mock_validate_active_context
        )
        monkeypatch.setattr(dice_manager, "scene_manager", scene_manager)

        # Create some rolls for the test scene
        dice_manager.roll("1d6", "Roll 1", test_scene)
        dice_manager.roll("2d8", "Roll 2", test_scene)

        # Get rolls for active scene
        rolls = dice_manager.get_rolls_for_active_scene()

        assert len(rolls) == 2
        assert all(roll.scene_id == test_scene.id for roll in rolls)
        assert rolls[0].reason == "Roll 2"  # Most recent first
        assert rolls[1].reason == "Roll 1"
