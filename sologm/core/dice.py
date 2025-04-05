"""Dice rolling functionality."""

import random
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.dice import DiceRoll
from sologm.utils.errors import DiceError


class DiceManager(BaseManager[DiceRoll, DiceRoll]):
    """Manages dice rolling operations."""

    def roll(
        self,
        notation: str,
        reason: Optional[str] = None,
        scene_id: Optional[str] = None,
    ) -> DiceRoll:
        """Roll dice according to the specified notation and save to database.

        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll
            scene_id: Optional ID of the scene this roll belongs to

        Returns:
            DiceRoll model with results

        Raises:
            DiceError: If notation is invalid
        """
        try:
            # Parse notation and roll dice
            count, sides, modifier = self._parse_notation(notation)

            self.logger.debug(
                f"Rolling {count} dice with {sides} sides and modifier {modifier:+d}"
            )
            individual_results = [random.randint(1, sides) for _ in range(count)]
            self.logger.debug(f"Individual dice results: {individual_results}")

            total = sum(individual_results) + modifier
            self.logger.debug(
                f"Final result: {individual_results} + {modifier} = {total}"
            )

            # Define the database operation
            def create_roll_operation(session: Session) -> DiceRoll:
                # Create the model instance
                dice_roll_model = DiceRoll.create(
                    notation=notation,
                    individual_results=individual_results,
                    modifier=modifier,
                    total=total,
                    reason=reason,
                    scene_id=scene_id,
                )

                # Add to session and flush to get ID
                session.add(dice_roll_model)
                session.flush()

                return dice_roll_model

            # Execute the operation
            return self._execute_db_operation("roll dice", create_roll_operation)

        except DiceError:
            raise
        except Exception as e:
            raise DiceError(f"Unexpected error during dice roll: {str(e)}") from e

    def get_recent_rolls(
        self, scene_id: Optional[str] = None, limit: int = 5
    ) -> List[DiceRoll]:
        """Get recent dice rolls, optionally filtered by scene.

        Args:
            scene_id: Optional scene ID to filter by
            limit: Maximum number of rolls to return

        Returns:
            List of DiceRoll models
        """

        def get_rolls_operation(session: Session) -> List[DiceRoll]:
            # Build query
            query = session.query(DiceRoll)
            if scene_id:
                query = query.filter(DiceRoll.scene_id == scene_id)

            # Order by creation time and limit results
            return query.order_by(DiceRoll.created_at.desc()).limit(limit).all()

        try:
            return self._execute_db_operation(
                "get recent dice rolls", get_rolls_operation
            )
        except Exception as e:
            raise DiceError(f"Failed to get recent dice rolls: {str(e)}") from e

    def _parse_notation(self, notation: str) -> tuple[int, int, int]:
        """Parse XdY+Z notation into components.

        Args:
            notation: Dice notation string (e.g., "2d6+3")

        Returns:
            Tuple of (number of dice, sides per die, modifier)

        Raises:
            DiceError: If notation is invalid
        """
        pattern = r"^(\d+)d(\d+)([+-]\d+)?$"
        match = re.match(pattern, notation)

        if not match:
            self.logger.error(f"Invalid dice notation: {notation}")
            raise DiceError(f"Invalid dice notation: {notation}")

        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3) or 0)

        self.logger.debug(
            f"Parsing dice notation - count: {count}, "
            f"sides: {sides}, modifier: {modifier}"
        )

        if count < 1:
            self.logger.error(f"Invalid dice count: {count}")
            raise DiceError("Must roll at least 1 die")
        if sides < 2:
            self.logger.error(f"Invalid sides count: {sides}")
            raise DiceError("Die must have at least 2 sides")

        self.logger.debug(f"Parsed {notation} as {count}d{sides}{modifier:+d}")
        return count, sides, modifier
