"""Tests for dice rolling functionality."""

import logging
from typing import Callable

import pytest
from sqlalchemy.orm import Session

# Import factory and models needed for test setup
from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext
from sologm.models.act import Act
from sologm.models.dice import DiceRoll as DiceRollModel
from sologm.models.game import Game
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError

logger = logging.getLogger(__name__)


# Helper function to create base test data within a session context
# Adapted from test_event.py
def create_base_test_data(
    session: Session,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    create_test_scene: Callable[..., Scene],
    game_active: bool = True,
    act_active: bool = True,
    scene_active: bool = True,
) -> tuple[Game, Act, Scene]:
    """Creates a standard game, act, and scene for testing."""
    game = create_test_game(session, is_active=game_active)
    act = create_test_act(session, game_id=game.id, is_active=act_active)
    scene = create_test_scene(session, act_id=act.id, is_active=scene_active)
    return game, act, scene


class TestDiceManager:
    """Tests for the DiceManager class."""

    def test_parse_basic_notation(self, session_context: SessionContext) -> None:
        """Test parsing basic XdY notation."""
        with session_context as session:
            managers = create_all_managers(session)
            count, sides, modifier = managers.dice._parse_notation("2d6")
            assert count == 2
            assert sides == 6
        assert modifier == 0

    def test_parse_notation_with_positive_modifier(
        self, session_context: SessionContext
    ) -> None:
        """Test parsing notation with positive modifier."""
        with session_context as session:
            managers = create_all_managers(session)
            count, sides, modifier = managers.dice._parse_notation("3d8+2")
            assert count == 3
            assert sides == 8
            assert modifier == 2

    def test_parse_notation_with_negative_modifier(
        self, session_context: SessionContext
    ) -> None:
        """Test parsing notation with negative modifier."""
        with session_context as session:
            managers = create_all_managers(session)
            count, sides, modifier = managers.dice._parse_notation("4d10-3")
            assert count == 4
            assert sides == 10
            assert modifier == -3

    def test_parse_invalid_notation(self, session_context: SessionContext) -> None:
        """Test parsing invalid notation formats."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(DiceError):
                managers.dice._parse_notation("invalid")

            with pytest.raises(DiceError):
                managers.dice._parse_notation("d20")

            with pytest.raises(DiceError):
                managers.dice._parse_notation("20")

    def test_parse_invalid_dice_count(self, session_context: SessionContext) -> None:
        """Test parsing notation with invalid dice count."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(DiceError):
                managers.dice._parse_notation("0d6")

    def test_parse_invalid_sides(self, session_context: SessionContext) -> None:
        """Test parsing notation with invalid sides."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(DiceError):
                managers.dice._parse_notation("1d1")

            with pytest.raises(DiceError):
                managers.dice._parse_notation("1d0")

    def test_roll_basic(self, session_context: SessionContext) -> None:
        """Test basic dice roll."""
        with session_context as session:
            managers = create_all_managers(session)
            roll = managers.dice.roll("1d6")

            assert roll.notation == "1d6"
            assert len(roll.individual_results) == 1
            assert 1 <= roll.individual_results[0] <= 6
            assert roll.modifier == 0
            assert roll.total == roll.individual_results[0]
            assert roll.reason is None

            # Verify it's in the database using session_context
            db_roll = (
                session.query(DiceRollModel).filter(DiceRollModel.id == roll.id).first()
            )
            assert db_roll is not None
            assert db_roll.notation == "1d6"
            assert len(db_roll.individual_results) == 1
            assert db_roll.total == roll.total

    def test_roll_multiple_dice(self, session_context: SessionContext) -> None:
        """Test rolling multiple dice."""
        with session_context as session:
            managers = create_all_managers(session)
            roll = managers.dice.roll("3d6")

            assert roll.notation == "3d6"
            assert len(roll.individual_results) == 3
        for result in roll.individual_results:
            assert 1 <= result <= 6
            assert roll.modifier == 0
            assert roll.total == sum(roll.individual_results)

    def test_roll_with_modifier(self, session_context: SessionContext) -> None:
        """Test rolling with modifier."""
        with session_context as session:
            managers = create_all_managers(session)
            roll = managers.dice.roll("2d4+3")

            assert roll.notation == "2d4+3"
            assert len(roll.individual_results) == 2
        for result in roll.individual_results:
            assert 1 <= result <= 4
            assert roll.modifier == 3
            assert roll.total == sum(roll.individual_results) + 3

    def test_roll_with_reason(self, session_context: SessionContext) -> None:
        """Test rolling with a reason."""
        with session_context as session:
            managers = create_all_managers(session)
            roll = managers.dice.roll("1d20", reason="Attack roll")

            assert roll.notation == "1d20"
            assert len(roll.individual_results) == 1
            assert 1 <= roll.individual_results[0] <= 20
            assert roll.reason == "Attack roll"

    def test_roll_with_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test rolling with a scene object."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create scene within the context
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            roll = managers.dice.roll("1d20", scene=scene)

            assert roll.scene_id == scene.id

            # Verify it's in the database with the scene ID
            db_roll = (
                session.query(DiceRollModel).filter(DiceRollModel.id == roll.id).first()
            )
            assert db_roll is not None
            assert db_roll.scene_id == scene.id

    def test_get_recent_rolls(self, session_context: SessionContext) -> None:
        """Test getting recent rolls."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create some rolls
            managers.dice.roll("1d20", reason="Roll 1")
            managers.dice.roll("2d6", reason="Roll 2")
            managers.dice.roll("3d8", reason="Roll 3")

            # Get recent rolls
            rolls = managers.dice.get_recent_rolls(limit=2)

            # Verify we got the most recent 2 rolls
            assert len(rolls) == 2
            assert rolls[0].reason == "Roll 3"  # Most recent first
            assert rolls[1].reason == "Roll 2"

    def test_get_recent_rolls_by_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting recent rolls filtered by scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create scenes within the context
            game, act, scene1 = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )
            # Create a second scene in the same act
            scene2 = create_test_scene(session, act_id=act.id, title="Other Scene")

            # Create some rolls with different scene objects
            managers.dice.roll("1d20", reason="Roll 1", scene=scene2)
            managers.dice.roll("2d6", reason="Roll 2", scene=scene1)
            managers.dice.roll("3d8", reason="Roll 3", scene=scene1)

            # Get recent rolls for the specific scene
            rolls = managers.dice.get_recent_rolls(scene=scene1)

            # Verify we got only rolls for the specified scene
            assert len(rolls) == 2
            assert all(roll.scene_id == scene1.id for roll in rolls)
            assert rolls[0].reason == "Roll 3"  # Most recent first
            assert rolls[1].reason == "Roll 2"

    def test_dice_roll_randomness(self, session_context: SessionContext):
        """Test that dice rolls produce random results within expected range."""
        with session_context as session:
            managers = create_all_managers(session)
            # Roll a large number of d6
            results = []
            for _ in range(100):
                roll = managers.dice.roll("1d6")
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
    def test_parse_notation_parametrized(
        self, session_context: SessionContext, notation, expected
    ):
        """Test parsing various dice notations."""
        with session_context as session:
            managers = create_all_managers(session)
            count, sides, modifier = managers.dice._parse_notation(notation)
            assert (count, sides, modifier) == expected

    def test_execute_db_operation(self, session_context: SessionContext):
        """Test the _execute_db_operation method."""
        with session_context as session:
            managers = create_all_managers(session)

            def _test_operation(inner_session):
                assert inner_session is session  # Ensure correct session is passed
                return "success"

            result = managers.dice._execute_db_operation(
                "test operation", _test_operation
            )
            assert result == "success"

    def test_execute_db_operation_error(self, session_context: SessionContext):
        """Test error handling in _execute_db_operation."""
        with session_context as session:
            managers = create_all_managers(session)

            def _test_operation(inner_session):
                assert inner_session is session  # Ensure correct session is passed
                raise ValueError("Test error")

            with pytest.raises(ValueError) as exc:
                managers.dice._execute_db_operation("test operation", _test_operation)
            assert "Test error" in str(exc.value)

    def test_logging_functionality(self, session_context: SessionContext, caplog):
        """Test that enhanced logging is working properly."""
        caplog.set_level(logging.DEBUG)

        with session_context as session:
            managers = create_all_managers(session)
            # Test logging in roll method
            roll = managers.dice.roll("2d6+3")

            # Check for expected log messages
            assert "Rolling dice with notation: 2d6+3" in caplog.text
            assert "Parsed notation: 2d6+3" in caplog.text
            assert "Individual dice results:" in caplog.text
            assert "Final result:" in caplog.text
            assert "Created dice roll with ID:" in caplog.text

    def test_roll_for_active_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test rolling dice for the active scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create active scene within the context
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Roll dice for active scene
            roll = managers.dice.roll_for_active_scene("1d20", "Test roll")

            assert roll.notation == "1d20"
            assert roll.scene_id == scene.id
            assert roll.reason == "Test roll"

    def test_get_rolls_for_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test getting rolls for a specific scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create scenes within the context
            game, act, scene1 = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )
            scene2 = create_test_scene(session, act_id=act.id, title="Different Scene")

            # Create some rolls for the test scene
            managers.dice.roll("1d6", "Roll 1", scene1)
            managers.dice.roll("2d8", "Roll 2", scene1)

            # Create a roll for a different scene
            managers.dice.roll("3d10", "Roll 3", scene2)

            # Get rolls for the test scene
            rolls = managers.dice.get_rolls_for_scene(scene1)

            assert len(rolls) == 2
            assert all(roll.scene_id == scene1.id for roll in rolls)
            assert rolls[0].reason == "Roll 2"  # Most recent first
            assert rolls[1].reason == "Roll 1"

    def test_get_rolls_for_active_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test getting rolls for the active scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create active scene within the context
            _, _, scene = create_base_test_data(
                session, create_test_game, create_test_act, create_test_scene
            )

            # Create some rolls for the test scene
            managers.dice.roll("1d6", "Roll 1", scene)
            managers.dice.roll("2d8", "Roll 2", scene)

            # Get rolls for active scene
            rolls = managers.dice.get_rolls_for_active_scene()

            assert len(rolls) == 2
            assert all(roll.scene_id == scene.id for roll in rolls)
            assert rolls[0].reason == "Roll 2"  # Most recent first
            assert rolls[1].reason == "Roll 1"
