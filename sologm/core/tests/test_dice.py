"""Tests for dice rolling functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sologm.core.dice import DiceManager
from sologm.models.base import Base
from sologm.models.dice import DiceRoll as DiceRollModel
from sologm.utils.errors import DiceError


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def dice_manager(db_session):
    """Create a DiceManager with a test session."""
    return DiceManager(session=db_session)


class TestDiceManager:
    """Tests for the DiceManager class."""

    def test_parse_basic_notation(self, dice_manager: DiceManager) -> None:
        """Test parsing basic XdY notation."""
        count, sides, modifier = dice_manager._parse_notation("2d6")
        assert count == 2
        assert sides == 6
        assert modifier == 0

    def test_parse_notation_with_positive_modifier(
        self, dice_manager: DiceManager
    ) -> None:
        """Test parsing notation with positive modifier."""
        count, sides, modifier = dice_manager._parse_notation("3d8+2")
        assert count == 3
        assert sides == 8
        assert modifier == 2

    def test_parse_notation_with_negative_modifier(
        self, dice_manager: DiceManager
    ) -> None:
        """Test parsing notation with negative modifier."""
        count, sides, modifier = dice_manager._parse_notation("4d10-3")
        assert count == 4
        assert sides == 10
        assert modifier == -3

    def test_parse_invalid_notation(self, dice_manager: DiceManager) -> None:
        """Test parsing invalid notation formats."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("invalid")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("d20")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("20")

    def test_parse_invalid_dice_count(self, dice_manager: DiceManager) -> None:
        """Test parsing notation with invalid dice count."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("0d6")

    def test_parse_invalid_sides(self, dice_manager: DiceManager) -> None:
        """Test parsing notation with invalid sides."""
        with pytest.raises(DiceError):
            dice_manager._parse_notation("1d1")

        with pytest.raises(DiceError):
            dice_manager._parse_notation("1d0")

    def test_roll_basic(self, dice_manager: DiceManager, db_session: Session) -> None:
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

    def test_roll_multiple_dice(self, dice_manager: DiceManager) -> None:
        """Test rolling multiple dice."""
        roll = dice_manager.roll("3d6")

        assert roll.notation == "3d6"
        assert len(roll.individual_results) == 3
        for result in roll.individual_results:
            assert 1 <= result <= 6
        assert roll.modifier == 0
        assert roll.total == sum(roll.individual_results)

    def test_roll_with_modifier(self, dice_manager: DiceManager) -> None:
        """Test rolling with modifier."""
        roll = dice_manager.roll("2d4+3")

        assert roll.notation == "2d4+3"
        assert len(roll.individual_results) == 2
        for result in roll.individual_results:
            assert 1 <= result <= 4
        assert roll.modifier == 3
        assert roll.total == sum(roll.individual_results) + 3

    def test_roll_with_reason(self, dice_manager: DiceManager) -> None:
        """Test rolling with a reason."""
        roll = dice_manager.roll("1d20", reason="Attack roll")

        assert roll.notation == "1d20"
        assert len(roll.individual_results) == 1
        assert 1 <= roll.individual_results[0] <= 20
        assert roll.reason == "Attack roll"

    def test_roll_with_scene_id(
        self, dice_manager: DiceManager, db_session: Session
    ) -> None:
        """Test rolling with a scene ID."""
        scene_id = "test-scene-123"
        roll = dice_manager.roll("1d20", scene_id=scene_id)

        assert roll.scene_id == scene_id

        # Verify it's in the database with the scene ID
        db_roll = (
            db_session.query(DiceRollModel).filter(DiceRollModel.id == roll.id).first()
        )
        assert db_roll is not None
        assert db_roll.scene_id == scene_id

    def test_get_recent_rolls(self, dice_manager: DiceManager) -> None:
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

    def test_get_recent_rolls_by_scene(self, dice_manager: DiceManager) -> None:
        """Test getting recent rolls filtered by scene."""
        scene_id = "test-scene-456"

        # Create some rolls with different scene IDs
        dice_manager.roll("1d20", reason="Roll 1", scene_id="other-scene")
        dice_manager.roll("2d6", reason="Roll 2", scene_id=scene_id)
        dice_manager.roll("3d8", reason="Roll 3", scene_id=scene_id)

        # Get recent rolls for the specific scene
        rolls = dice_manager.get_recent_rolls(scene_id=scene_id)

        # Verify we got only rolls for the specified scene
        assert len(rolls) == 2
        assert all(roll.scene_id == scene_id for roll in rolls)
        assert rolls[0].reason == "Roll 3"  # Most recent first
        assert rolls[1].reason == "Roll 2"
