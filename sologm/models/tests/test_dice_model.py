"""
DiceRoll Model Test Coverage Audit Results:

AUDIT FINDINGS (Phase 1.2, Sub-step 1.2.3):
- DiceRoll model has 1 hybrid property: has_reason
- No existing tests found for DiceRoll model hybrid properties
- Current tests are only in sologm/core/tests/test_dice.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTY:
1. has_reason - Field-based existence check (reason field not null/empty)

COVERAGE GAPS IDENTIFIED:
- No Python context testing for hybrid property
- No SQL context testing for hybrid property
- No edge case testing (None, empty, whitespace scenarios)
- No positive/negative case testing
- Field-based existence properties need comprehensive string validation testing

SPECIAL CONSIDERATIONS FOR DICEROLL:
- Field-based existence check rather than relationship check
- Need to test None, empty string, whitespace-only, and valid reason scenarios
- Simpler than relationship properties but still requires comprehensive testing
- Tests string field validation patterns
- No foreign key relationships involved, but may have optional scene association

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

import pytest

from sologm.database.session import SessionContext
from sologm.models.dice import DiceRoll

if TYPE_CHECKING:
    pass


class TestDiceRollHybridProperties:
    """Test DiceRoll model hybrid properties in both Python and SQL contexts."""

    def test_has_reason_python_context_none_reason(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason property in Python context with None reason."""
        with session_context as session:
            # Create dice roll with no reason (None)
            dice_roll = DiceRoll.create(
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason=None,
            )
            session.add(dice_roll)
            session.flush()

            # Test has_reason returns False for None reason
            assert not dice_roll.has_reason, (
                "DiceRoll with None reason should return False"
            )

    def test_has_reason_python_context_empty_reason(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason property in Python context with empty string reason."""
        with session_context as session:
            # Create dice roll with empty string reason
            dice_roll = DiceRoll.create(
                notation="1d20",
                individual_results=[12],
                modifier=0,
                total=12,
                reason="",
            )
            session.add(dice_roll)
            session.flush()

            # Test has_reason returns False for empty string reason
            assert not dice_roll.has_reason, (
                "DiceRoll with empty string reason should return False"
            )

    def test_has_reason_python_context_whitespace_reason(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason property in Python context with whitespace-only reason."""
        with session_context as session:
            # Create dice roll with whitespace-only reason
            dice_roll = DiceRoll.create(
                notation="1d20",
                individual_results=[8],
                modifier=0,
                total=8,
                reason="   \t\n  ",
            )
            session.add(dice_roll)
            session.flush()

            # Test has_reason returns False for whitespace-only reason
            assert not dice_roll.has_reason, (
                "DiceRoll with whitespace-only reason should return False"
            )

    def test_has_reason_python_context_valid_reason(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason property in Python context with valid reason."""
        with session_context as session:
            # Create dice roll with valid reason
            dice_roll = DiceRoll.create(
                notation="1d20",
                individual_results=[18],
                modifier=0,
                total=18,
                reason="Attack roll",
            )
            session.add(dice_roll)
            session.flush()

            # Test has_reason returns True for valid reason
            assert dice_roll.has_reason, "DiceRoll with valid reason should return True"

    def test_has_reason_sql_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason property in SQL context (query filtering)."""
        with session_context as session:
            # Create dice rolls with different reason states
            dice_roll_none = DiceRoll.create(
                notation="1d6",
                individual_results=[3],
                modifier=0,
                total=3,
                reason=None,
            )
            dice_roll_empty = DiceRoll.create(
                notation="1d6",
                individual_results=[4],
                modifier=0,
                total=4,
                reason="",
            )
            dice_roll_whitespace = DiceRoll.create(
                notation="1d6",
                individual_results=[2],
                modifier=0,
                total=2,
                reason="  \t  ",
            )
            dice_roll_valid = DiceRoll.create(
                notation="1d6",
                individual_results=[6],
                modifier=0,
                total=6,
                reason="Initiative roll",
            )

            session.add_all(
                [
                    dice_roll_none,
                    dice_roll_empty,
                    dice_roll_whitespace,
                    dice_roll_valid,
                ]
            )
            session.flush()

            # Test SQL filtering - dice rolls with reasons
            rolls_with_reason = (
                session.query(DiceRoll).filter(DiceRoll.has_reason).all()
            )
            roll_ids_with_reason = [r.id for r in rolls_with_reason]

            assert dice_roll_valid.id in roll_ids_with_reason
            assert dice_roll_none.id not in roll_ids_with_reason
            assert dice_roll_empty.id not in roll_ids_with_reason
            assert dice_roll_whitespace.id not in roll_ids_with_reason

            # Test SQL filtering - dice rolls without reasons
            rolls_without_reason = (
                session.query(DiceRoll).filter(~DiceRoll.has_reason).all()
            )
            roll_ids_without_reason = [r.id for r in rolls_without_reason]

            assert dice_roll_valid.id not in roll_ids_without_reason
            assert dice_roll_none.id in roll_ids_without_reason
            assert dice_roll_empty.id in roll_ids_without_reason
            assert dice_roll_whitespace.id in roll_ids_without_reason

    def test_has_reason_dynamic_changes(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason behavior when reason changes dynamically."""
        with session_context as session:
            # Create dice roll with no reason initially
            dice_roll = DiceRoll.create(
                notation="1d20",
                individual_results=[10],
                modifier=0,
                total=10,
                reason=None,
            )
            session.add(dice_roll)
            session.flush()

            # Test initially no reason
            assert not dice_roll.has_reason, "DiceRoll should not have reason initially"

            # Add a valid reason
            dice_roll.reason = "Skill check"
            session.add(dice_roll)
            session.flush()

            # Test after adding reason
            assert dice_roll.has_reason, (
                "DiceRoll should have reason after setting valid reason"
            )

            # Change to empty string
            dice_roll.reason = ""
            session.add(dice_roll)
            session.flush()

            # Test after clearing reason
            assert not dice_roll.has_reason, (
                "DiceRoll should not have reason after setting empty string"
            )

            # Change to whitespace-only
            dice_roll.reason = "   "
            session.add(dice_roll)
            session.flush()

            # Test with whitespace
            assert not dice_roll.has_reason, (
                "DiceRoll should not have reason with whitespace-only string"
            )

    def test_has_reason_with_scene_association(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_reason property works with scene associations."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create dice rolls with and without reasons, associated with scene
            dice_roll_with_reason = DiceRoll.create(
                notation="1d20",
                individual_results=[16],
                modifier=2,
                total=18,
                reason="Combat attack",
                scene_id=scene.id,
            )
            dice_roll_without_reason = DiceRoll.create(
                notation="1d20",
                individual_results=[11],
                modifier=0,
                total=11,
                reason=None,
                scene_id=scene.id,
            )

            session.add_all([dice_roll_with_reason, dice_roll_without_reason])
            session.flush()

            # Test Python context - should work regardless of scene association
            assert dice_roll_with_reason.has_reason, (
                "DiceRoll with reason should return True even with scene association"
            )
            assert not dice_roll_without_reason.has_reason, (
                "DiceRoll without reason should return False even with scene "
                + "association"
            )

            # Test SQL context - should work with scene filtering
            scene_rolls_with_reason = (
                session.query(DiceRoll)
                .filter(DiceRoll.scene_id == scene.id)
                .filter(DiceRoll.has_reason)
                .all()
            )
            scene_rolls_without_reason = (
                session.query(DiceRoll)
                .filter(DiceRoll.scene_id == scene.id)
                .filter(~DiceRoll.has_reason)
                .all()
            )

            assert len(scene_rolls_with_reason) == 1
            assert scene_rolls_with_reason[0].id == dice_roll_with_reason.id

            assert len(scene_rolls_without_reason) == 1
            assert scene_rolls_without_reason[0].id == dice_roll_without_reason.id

    def test_has_reason_edge_cases(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_reason with various string edge cases."""
        with session_context as session:
            # Test various edge case strings
            edge_cases = [
                ("Single space", " ", False),
                ("Tab only", "\t", False),
                ("Newline only", "\n", False),
                ("Mixed whitespace", " \t\n\r ", False),
                ("Valid with spaces", "  valid reason  ", True),
                ("Single character", "a", True),
                ("Number as string", "123", True),
                ("Special characters", "!@#$%", True),
                ("Unicode characters", "攻撃ロール", True),
            ]

            dice_rolls = []
            for description, reason_value, expected_has_reason in edge_cases:
                dice_roll = DiceRoll.create(
                    notation="1d6",
                    individual_results=[1],
                    modifier=0,
                    total=1,
                    reason=reason_value,
                )
                dice_rolls.append((dice_roll, description, expected_has_reason))
                session.add(dice_roll)

            session.flush()

            # Test Python context for all edge cases
            for dice_roll, description, expected in dice_rolls:
                actual = dice_roll.has_reason
                assert actual == expected, (
                    f"Edge case '{description}' with reason '{dice_roll.reason}' "
                    + f"expected {expected}, got {actual}"
                )

            # Test SQL context filtering
            rolls_with_reason = (
                session.query(DiceRoll).filter(DiceRoll.has_reason).all()
            )
            rolls_without_reason = (
                session.query(DiceRoll).filter(~DiceRoll.has_reason).all()
            )

            expected_with_reason = [dr for dr, _, expected in dice_rolls if expected]
            expected_without_reason = [
                dr for dr, _, expected in dice_rolls if not expected
            ]

            assert len(rolls_with_reason) == len(expected_with_reason)
            assert len(rolls_without_reason) == len(expected_without_reason)

            with_reason_ids = {r.id for r in rolls_with_reason}
            expected_with_ids = {dr.id for dr in expected_with_reason}
            assert with_reason_ids == expected_with_ids

    def test_has_reason_complex_sql_filtering(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test complex SQL queries combining has_reason with other conditions."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            scene2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")

            # Create dice rolls with different combinations
            d20_with_reason = DiceRoll.create(
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="d20 attack",
                scene_id=scene1.id,
            )
            d20_without_reason = DiceRoll.create(
                notation="1d20",
                individual_results=[12],
                modifier=0,
                total=12,
                reason=None,
                scene_id=scene1.id,
            )
            d6_with_reason = DiceRoll.create(
                notation="1d6",
                individual_results=[4],
                modifier=0,
                total=4,
                reason="d6 damage",
                scene_id=scene2.id,
            )
            d6_without_reason = DiceRoll.create(
                notation="1d6",
                individual_results=[2],
                modifier=0,
                total=2,
                reason="",
                scene_id=scene2.id,
            )

            session.add_all(
                [
                    d20_with_reason,
                    d20_without_reason,
                    d6_with_reason,
                    d6_without_reason,
                ]
            )
            session.flush()

            # Test complex queries
            d20_rolls_with_reason = (
                session.query(DiceRoll)
                .filter(DiceRoll.notation.like("%d20%"))
                .filter(DiceRoll.has_reason)
                .all()
            )

            scene1_rolls_with_reason = (
                session.query(DiceRoll)
                .filter(DiceRoll.scene_id == scene1.id)
                .filter(DiceRoll.has_reason)
                .all()
            )

            all_rolls_with_reason_high_total = (
                session.query(DiceRoll)
                .filter(DiceRoll.has_reason)
                .filter(DiceRoll.total >= 10)
                .all()
            )

            # Verify results
            assert len(d20_rolls_with_reason) == 1
            assert d20_rolls_with_reason[0].id == d20_with_reason.id

            assert len(scene1_rolls_with_reason) == 1
            assert scene1_rolls_with_reason[0].id == d20_with_reason.id

            assert len(all_rolls_with_reason_high_total) == 1
            assert all_rolls_with_reason_high_total[0].id == d20_with_reason.id

    @pytest.mark.parametrize(
        "reason_value,expected_has_reason",
        [
            (None, False),
            ("", False),
            ("   ", False),
            ("\t", False),
            ("\n", False),
            (" \t\n ", False),
            ("valid", True),
            ("attack roll", True),
            ("123", True),
            ("!", True),
        ],
    )
    def test_has_reason_parametrized(
        self,
        reason_value: str,
        expected_has_reason: bool,
        session_context: SessionContext,
    ) -> None:
        """Parametrized test for has_reason property with various reason values."""
        with session_context as session:
            # Create dice roll with the test reason value
            dice_roll = DiceRoll.create(
                notation="1d6",
                individual_results=[3],
                modifier=0,
                total=3,
                reason=reason_value,
            )
            session.add(dice_roll)
            session.flush()

            # Test Python context
            assert dice_roll.has_reason == expected_has_reason, (
                f"DiceRoll with reason '{reason_value}' should return "
                + f"{expected_has_reason}"
            )

            # Test SQL context
            rolls_with_reason = (
                session.query(DiceRoll).filter(DiceRoll.has_reason).all()
            )
            roll_found_in_query = dice_roll.id in [r.id for r in rolls_with_reason]

            assert roll_found_in_query == expected_has_reason, (
                f"DiceRoll with reason '{reason_value}' should be "
                + f"{'found' if expected_has_reason else 'not found'} in SQL query"
            )
